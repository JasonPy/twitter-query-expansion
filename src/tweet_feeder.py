import json
import argparse
import time
import configparser

from elasticsearch.helpers import streaming_bulk
from utils import es_connect, pg_connect, get_project_root
from tqdm import tqdm

# mapped attributes
ATTRIBUTES = ["_id", "retweet_count", "reply_count", "like_count", "created_at", "txt", "hashtags", "word_count"]


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
    parser.add_argument('--es_credentials', required=False, default="auth/es-credentials.ini", help='Elastic Search credentials file')
    parser.add_argument('--pg_credentials', required=False, default="auth/pg-credentials.ini", help='Postgres credentials file')
    parser.add_argument('--es_config', required=False, default="config/es-config.conf", help='Settings for new Index')
    parser.add_argument('--wordcount', required=False, default=25, help='Minimum number of words per Tweet')
    args = parser.parse_args()                    

    # connect to postgres and elastic search
    config = configparser.ConfigParser()
    config.read([get_project_root()/args.es_credentials, get_project_root()/args.pg_credentials])

    es_client = es_connect(credentials=config["ELASTIC"])
    pg_client = pg_connect(credentials=config["POSTGRES"])

    pg_cursor = pg_client.cursor()

    # create index if it not exists
    if not es_client.indices.exists(index=args.index):
        print(f"Creating new index {args.index} using {args.es_config} ...")
        es_conf = json.load(open(file=get_project_root()/args.es_config))
        es_client.indices.create(index=args.index, settings=es_conf["settings"], mappings=es_conf["mappings"])

    # count entries in data base
    wordcount_query = (
        "Select count(*) from ( "
            f"SELECT array_length(string_to_array(regexp_replace(txt,  '[^\w\s]', '', 'g'), ' '), 1) AS word_count FROM {args.table} "
        ") as wc "
        f"where wc.word_count >= {args.wordcount}"
    )

    pg_cursor.execute(query=wordcount_query)
    doc_count = pg_cursor.fetchall()[0][0]

    # compose query to retrieve tweets with corresponding hashtags and specified min. number of words
    query = (
        "SELECT * FROM ( "
            "SELECT tw.id, tw.retweet_count, tw.reply_count, tw.like_count, "
            "tw.created_at, tw.txt, array_agg(ht.txt) AS hashtags, "
            "array_length(string_to_array(regexp_replace(tw.txt,  '[^\w\s]', '', 'g'), ' '), 1) AS word_count "
            f"FROM {args.table} tw "
            "LEFT OUTER JOIN hashtag_posting hp ON hp.tweet_id = tw.id "
            "LEFT OUTER JOIN hashtag ht ON ht.id = hp.hashtag_id "
            "GROUP BY tw.id "
        ") as q "
        f"WHERE q.word_count >= {args.wordcount} "
    )

    # execute the query
    print("Executing Postgres Query...")
    pg_cursor.execute(query=query)

    # insert data from Postgres to ES in a lazy manner
    print(f"Ingesting {doc_count} tweets from Postgres into Elastic Search...")

    # feed tweets using streaming API
    progress= tqdm(unit=" tweets", total=doc_count)
    successes = 0
    for ok, action in streaming_bulk(client=es_client, index=args.index ,actions=iterate(cursor=pg_cursor, attributes=ATTRIBUTES, size=10000)):
        progress.update(1)
        successes += ok

    print(f"Finished - ingested {successes} tweets")

    es_client.close()
    pg_client.close()

    exit(0)

if __name__ == "__main__":
    main()