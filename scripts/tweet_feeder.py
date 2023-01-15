import json
import argparse
import configparser
import sys
import os
import json
import psycopg2

from elasticsearch.helpers import streaming_bulk
from elasticsearch import Elasticsearch
from tqdm import tqdm

# add root directory (temporary) to path in order to make imports work
#sys.path.append(os.path.dirname(sys.path[0]))
#from pipeline.utils import get_project_root

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


def es_connect(credentials: json) -> Elasticsearch:
    """
    Connect to an elastic search API.
    """
    try:
        print("Connecting to Elastic Search...")
        es = Elasticsearch(credentials['URL'], basic_auth=(credentials['USER'], credentials['PWD']), ca_certs="auth/"+credentials['CERT'])
    except Exception:
        print("Unable to connect to", credentials['URL'])
        exit(1)
    print("Successfully connected to", credentials['URL'])
    return es


def pg_connect(credentials: json) -> any:
    """
    Connect to a PostgreSQL database.
    """
    try:
        print("Connecting to PostgreSQL database...")
        pg = psycopg2.connect(dbname=credentials["DB"], user=credentials['USER'], password="auth/"+credentials['PWD'])
    except Exception:
        print("Failed to connect to PostgresQL database ", credentials['URL'])
        exit(1)
    print("Successfully connected to", credentials['URL'])
    return pg


def main():
    """
    This script ingests data from an PostgreSQL instance into an Elastic Search index.
    The processing is based on streaming and arguments can be passed via the command line interface.
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Feed Postgres data into Elastic Search Index')
    parser.add_argument('-i', '--index', required=True, help='Elastic Search index')
    parser.add_argument('-t', '--table', required=True, help='Postgres table')
    parser.add_argument('-ec','--elastic_credentials', required=False, default="auth/es-credentials.ini", help='Path to Elastic Search credentials file')
    parser.add_argument('-pc', '--postgres_credentials', required=False, default="auth/pg-credentials.ini", help='Path to Postgres credentials file')
    parser.add_argument('-es', '--elastic_settings', required=False, default="templates/es-config.tpl", help='Settings for new Index; Look at "/templates/es-config.conf"')
    parser.add_argument('-wc', '--wordcount', required=False, default=25, help='Minimum number of words per Tweet')
    args = parser.parse_args()                    

    # connect to postgres and elastic search
    config = configparser.ConfigParser()
    config.read([args.elastic_credentials, args.postgres_credentials])

    es_client = es_connect(credentials=config["ELASTIC"])
    pg_client = pg_connect(credentials=config["POSTGRES"])

    pg_cursor = pg_client.cursor()

    # create index if it not exists
    if not es_client.indices.exists(index=args.index):
        print(f"Creating new index {args.index} using {args.elastic_settings} ...")
        es_conf = json.load(open(file=args.elastic_settings))
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
    for ok, action in streaming_bulk(client=es_client, index=args.index ,actions=iterate(cursor=pg_cursor, attributes=ATTRIBUTES, size=1000)):
        progress.update(1)
        successes += ok

    print(f"Finished - ingested {successes} tweets")

    es_client.close()
    pg_client.close()

    exit(0)

if __name__ == "__main__":
    main()