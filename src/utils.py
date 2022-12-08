import json
import psycopg2

from elasticsearch import Elasticsearch


def es_connect(credentials: json):
    """
    Connect to an elastic search API.
    """
    try:
        print("Connecting to Elastic Search...")
        es = Elasticsearch(credentials['URL'], basic_auth=(credentials['USER'], credentials['PWD']), ca_certs=credentials['CERT'])
    except Exception:
        print("Unable to connect to", credentials['URL'])
        exit(1)
    print("Successfully connected to", credentials['URL'])
    return es


def pg_connect(credentials: json):
    """
    Connect to a PostgreSQL database.
    """
    try:
        print("Connecting to PostgreSQL database...")
        pg = psycopg2.connect(dbname=credentials["DB"], user=credentials['USER'], password=credentials['PWD'])
    except Exception:
        print("Failed to connect to PostgresQL database ", credentials['URL'])
    print("Successfully connected to", credentials['URL'])
    return pg
