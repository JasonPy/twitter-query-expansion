import json
import psycopg2

from elasticsearch import Elasticsearch
from pathlib import Path


def get_project_root() -> Path:
    """
    Get the absolute path of the project's directory
    """
    return Path(__file__).parent.parent


def pg_connect(credentials: json) -> any:
    """
    Connect to a PostgreSQL database.
    """
    try:
        print("Connecting to PostgreSQL database...")
        pg = psycopg2.connect(
            dbname=credentials["DB"], user=credentials['USER'], password=credentials['PWD'])
    except Exception:
        print("Failed to connect to PostgresQL database ", credentials['URL'])
        exit(1)
    print("Successfully connected to", credentials['URL'])
    return pg


def get_expansion_terms(candidate_terms: list, synonyms: dict, aggregations: dict, threshold: float = 0.6):
    """
    Given some candidate terms and their related synonyms, check if the synonyms
    can act es expansion terms. This is done by looking at the co-ocurrence of both terms.
    """
    expansion_terms = []

    for term in candidate_terms:
        if term in aggregations.keys():
            df = aggregations[term]

            for synonym in synonyms[term]:
                if f"{synonym}&{term}" in aggregations.keys():

                    tf = aggregations[f"{synonym}&{term}"]
                    tf_idf = tf / df

                    if tf_idf > threshold:
                        expansion_terms.append(synonym)

    return expansion_terms



def load_queries(path="data/queries.json"):
    with open(path, 'r') as q:
        queries = json.load(q)
    return queries