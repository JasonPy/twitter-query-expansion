import json
import argparse
import time

from elasticsearch.helpers import streaming_bulk
from utils import es_connect, pg_connect, get_project_root
from tqdm import tqdm


def iterate(cursor, attributes, size=1000):
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


def main():
    """
    This script ingests data from an PostgreSQL instance into an Elastic Search index.
    The processing is based on streaming and arguments can be passed via the command line interface.
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Feed Postgres data into Elastic Search Index')
    parser.add_argument('-i', '--index', required=True, help='Elastic Search index')
    parser.add_argument('-t', '--table', required=True, help='Postgres table')
    parser.add_argument('--es_credentials', required=False, default="auth/es-credentials.json", help='Elastic Search credentials file')
    parser.add_argument('--pg_credentials', required=False, default="auth/pg-credentials.json", help='Postgres credentials file')
    parser.add_argument('--es_config', required=False, default="es-config.conf", help='Settings for new Index')
    parser.add_argument('-wc', '--wordcount', required=False, default=25, help='Minimum number of words per Tweet')
    parser.add_argument('-a', '--attributes', required=False, default=None, help='Comma-separated attributes of Postgres table to be included')
    args = parser.parse_args()                    

    # connect to postgres and elastic search
    es_cred = json.load(open(file=get_project_root()/args.es_credentials))
    pg_cred = json.load(open(file=get_project_root()/args.pg_credentials))

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
        print(f"Creating new index {args.index} using {args.es_config} ...")
        es_conf = json.load(open(file=get_project_root()/args.es_config))
        es_client.indices.create(index=args.index, settings=es_conf["settings"], mappings=es_conf["mappings"])

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
    print("Ingest data from Postgres into Elastic Search...")

    # feed tweets using streaming API
    progress= tqdm(unit=" tweets")
    successes = 0
    for ok, action in streaming_bulk(client=es_client, index=args.index ,actions=iterate(cursor=pg_cursor, attributes=args.attributes, size=10000)):
        progress.update(1)
        successes += ok


    time.sleep(2)
    print(f"Finished - ingested {successes} tweets")

    es_client.close()
    pg_client.close()

    exit(0)

if __name__ == "__main__":
    main()