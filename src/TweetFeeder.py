import json
import argparse

from utils import es_connect, pg_connect
from tqdm import tqdm


def iterate(cursor, attributes, size=100):
    """
    An iterator that returns objects from a PostgreSQL database connection.
    The objects are turned into dictionaries of a certain shape defined by attributes. 
    """
    while True:
        results = cursor.fetchmany(size)
        if not results:
            break

        for result in results:
            obj = {}
            for i, attr in enumerate(attributes):
                obj[attr] = result[i]
            yield obj


# parse command line arguments
parser = argparse.ArgumentParser(description='Feed Postgres data into Elastic Search Index')
parser.add_argument('-i', '--index', required=True, help='Elastic Search index')
parser.add_argument('-t', '--table', required=True, help='Postgres table')
parser.add_argument('-wc', '--wordcount', required=False, default=25, help='Minimum number of words per Tweet')
parser.add_argument('-a', '--attributes', required=False, default=None, help='Comma-separated attributes of Postgres table to be included')
args = parser.parse_args()                    

# connect to postgres and elastic search
es_cred = json.load(open('../es-credentials.json'))
pg_cred = json.load(open('../pg-credentials.json'))

es_client = es_connect(credentials=es_cred)
pg_client = pg_connect(credentials=pg_cred)

pg_cursor = pg_client.cursor()

if args.attributes is None:
    # obtain all column names
    pg_cursor.execute(f"SELECT * FROM {args.table} LIMIT 0")
    args.attributes = [c[0] for c in pg_cursor.description]
else:
    args.attributes = args.attributes.split(",")

# create index if it not exists
if not es_client.indices.exists(index=args.index):
    es_client.indices.create(index=args.index)

# formulate query to add number of words within a tweet text
word_count_query = (
    f"SELECT {', '.join(args.attributes)}, array_length(string_to_array(regexp_replace(txt,  '[^\w\s]', '', 'g'), ' '), 1) AS word_count FROM {args.table})"
)

# compose final query
pg_query = (
    f"SELECT * FROM ( "
    f"{word_count_query} AS t " 
    f"WHERE word_count >= {args.wordcount} "
)

# execute the query
print("Executing Postgres Query...")
pg_cursor.execute(query=pg_query)

# insert data from Postgres to ES in a lazy manner
print("Insert data from Postgres into Elastic Search...")

for data in tqdm(iterate(cursor=pg_cursor, attributes=args.attributes, size=1000)):
    # insert data into ES
    try:
        # parse the id to avoid duplicates
        es_client.index(index=args.index, document=data, id=data["id"])
    except Exception as exc:
        print("Exception during data insertion!\n", exc)
        exit(1)


print("Finished feeding process.")
es_client.close()
pg_client.close()

exit(0)