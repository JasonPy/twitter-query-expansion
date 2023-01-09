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

