import os
import sys
import json
import argparse
import configparser

from datetime import datetime

# add directory to path, to make import work
sys.path.append(os.path.dirname(sys.path[0]))

"""
-------------- PARSE ARGUMENTS --------------
"""

# Read command line arguments
parser = argparse.ArgumentParser(description='Run Query Expansion Pipeline.')
parser.add_argument('-q', '--queries', required=False, default="data/queries.json", help='List of queries to run pipeline.')
parser.add_argument('-e', '--embedding', required=False, default="word2vec", choices=["word2vec","fasttext"], help='Choose between "word2vec" and "fasttext" embedding model.')
parser.add_argument('-i', '--index', required=False, default="tweets", help='Elastic Search Index.')
parser.usage = parser.format_help()
args = parser.parse_args() 


"""
---------------- BASE ARGUMENTS ----------------
"""
OUTPUT_PATH = os.path.join("out", args.embedding)

SPACY_MODEL = "de_core_news_lg"

W2V_MODEL = 'data/word2vec/german.model'
FT_MODEL = 'data/fasttext/cc.de.300.bin'

# TODO: read params from file (?)
EMBEDDING_PARAMS = {
    "pos_list": ["NOUN","ADJ","VERB"],
    "entity": True,
    "hashtag": False,
    "user": False,
    "num_nearest_terms": 3
}

ELASTIC_PARAMS = {
    "retweet": False,
    "hashtag_boost": 0.5,
    "tweet_range": ("2021-01-01", "2023-01-01")
}

"""
---------------- LOGGING ----------------
"""
log = {
    "timestamp": datetime.now().strftime("%d-%m-%y_%H:%M:%S"),
    "spacy_model": SPACY_MODEL,
    "w2v_model": W2V_MODEL,
    "ft_model": FT_MODEL,
    "embedding_params": EMBEDDING_PARAMS,
    "elastic_params": ELASTIC_PARAMS,
    "embedding": args.embedding,
    "index": args.index
}


"""
------------------ TEXT PROCESSING ------------------ 
"""
from pipeline.utils import load_queries
from pipeline.text_processing import TextProcessingPipeline

queries = load_queries(args.queries)
log["queries"] = args.queries

pipe = TextProcessingPipeline(model=SPACY_MODEL)

docs = []

# for each query, invoke the SpaCy pipeline
for query in queries:
    doc = pipe.invoke(query)
    docs.append(doc)
log["docs"] = [d.text for d in docs]


query_tokens = []

# for each processed query, filter the tokens depending on the specified parameters
for doc in docs:
    filtered_tokens = pipe.get_filtered_tokens(doc, EMBEDDING_PARAMS)
    query_tokens.append(filtered_tokens)
log["query_tokens"] = [[token.text for token in tokens] for tokens in query_tokens]


"""
------------------ WORD EMBEDDINGS ------------------
"""
from pipeline.embedding import Word2Vec
from pipeline.embedding import FastText

if args.embedding == "word2vec":
    model = Word2Vec(W2V_MODEL)
elif args.embedding == "fasttext":
    model = FastText(FT_MODEL) 
else:
    raise ValueError("Invalid Embedding")


similar_terms = []

# find similar terms using embedding model 
for tokens in query_tokens:
    similar_terms.append(model.get_similar_terms(pipe.trim_symbols(tokens), EMBEDDING_PARAMS["num_nearest_terms"]))
log["similar_terms"] = similar_terms

# free space
del model


"""
------------------ ELASTIC SEARCH ------------------
"""
from pipeline.elasticsearch import ElasticsearchClient

# read Elastic Search credentials
config = configparser.ConfigParser()
config.read('auth/es-credentials.ini')

# connect to Elastic Search
es_client = ElasticsearchClient(credentials=config["ELASTIC"], index=args.index)
es_client.connect(config["ELASTIC"]["PWD"])


expansion_terms = []

# find most suitable expansion terms
for i in range(len(queries)):
    expansion_terms.append(es_client.get_expansion_terms(pipe.trim_symbols(query_tokens[i]), similar_terms[i]))
log["expansion_terms"] = expansion_terms


results = []

# execute query to retrieve tweets using the final expanded query
for i in range(len(queries)):

    search = ELASTIC_PARAMS
    search["terms"] = pipe.trim_symbols(query_tokens[i]) + expansion_terms[i]
    search["hashtags"] = [h.lower() for h in pipe.trim_symbols([t for t in query_tokens[i] if t._.is_hashtag ])]
    search["users"] = pipe.trim_symbols([t for t in query_tokens[i] if t._.is_user ])
    search["entities"] = pipe.trim_symbols([t for t in query_tokens[i] if t.ent_type_ ])

    results.append(es_client.get_tweets(search))
log["tweets"] = results



"""
------------------ LOG RESULTS ------------------
"""

if not os.path.exists(OUTPUT_PATH):
     os.makedirs(OUTPUT_PATH)

with open(os.path.join(OUTPUT_PATH, datetime.now().strftime('%d-%m-%y_%H:%M:%S')+".log.json"), "w") as outfile:
    json.dump(log, outfile)
outfile.close()

exit(0)