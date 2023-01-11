import os
import json
import configparser

from datetime import datetime

from pipeline.text_processor import TextProcessor, trim_symbols
from pipeline.embedding import Word2Vec, FastText
from pipeline.elasticsearch import ElasticsearchClient


def run(queries: list, spacy_model: str, embedding_params: json, elastic_params:json) -> json:
    """
    Execute the complete Query Expansion Pipeline. This includes Query pre-processing, the application of Word Embeddings
    to find similar terms and the retrieval of Tweets.
    The parameters and results of the pipeline are stored in the specified output file.

    Parameters
    ----------
    queries: list
        A list of queries.

    spacy_model: str
        The name of the SpaCy model.

    embedding_params: json
        Parameters defining embedding-specific configurations.
        
    elastic_params:json
        Parameters defining elastic-specific configurations.

    Returns
    ----------
    res: json
        The resulting Tweets.
    """    
    if embedding_params["type"] == "word2vec":
        embedding_model = 'models/word2vec/german.model' 
    elif embedding_params["type"] == "fasttext":
        embedding_model = "models/fasttext/cc.de.300.model"
    else:
        raise ValueError("Type of Embedding not found. Use 'word2vec' or 'fasttext'")

    # prepare logging
    log = {
        "timestamp": datetime.now().strftime("%d-%m-%y_%H:%M:%S"),
        "queries": queries,
        "spacy_model": spacy_model,
        "embedding_model": embedding_model,
        "embedding_params": embedding_params,
        "elastic_params": elastic_params,
    }


    # ------------------ TEXT PROCESSING ------------------ 
    print('Processing text using SpaCy...')
    pipe = TextProcessor(model=spacy_model)

    docs = []

    # for each query, invoke the SpaCy pipeline
    for query in queries:
        doc = pipe.invoke(query)
        docs.append(doc)
    log["docs"] = [d.text for d in docs]


    query_tokens = []

    # for each processed query, filter the tokens depending on the specified parameters
    for doc in docs:
        filtered_tokens = pipe.get_filtered_tokens(doc, embedding_params)
        query_tokens.append(filtered_tokens)
    log["query_tokens"] = [[token.text for token in tokens] for tokens in query_tokens]

    del pipe

    # ------------------ WORD EMBEDDINGS ------------------
    print(f'Loading {embedding_params["type"]} model...')

    if embedding_params["type"] == "word2vec":
        model = Word2Vec(embedding_model)
    elif embedding_params["type"] == "fasttext":
        model = FastText(embedding_model) 
    else:
        raise ValueError("Invalid Embedding")

    similar_terms = []

    # find similar terms using embedding model 
    for tokens in query_tokens:
        similar_terms.append(model.get_similar_terms(trim_symbols(tokens), embedding_params["num_nearest_terms"]))
    log["similar_terms"] = similar_terms

    # free space
    del model


    # ------------------ ELASTIC SEARCH ------------------
    # read Elastic Search credentials
    config = configparser.ConfigParser()
    config.read('auth/es-credentials.ini')

    print('Connecting to Elastic Search...')

    # connect to Elastic Search
    es_client = ElasticsearchClient(credentials=config["ELASTIC"], index=elastic_params["index"])
    es_client.connect(config["ELASTIC"]["PWD"])

    print('Retrieving Tweets...')

    expansion_terms = []

    # find most suitable expansion terms
    for i in range(len(queries)):
        expansion_terms.append(es_client.get_expansion_terms(trim_symbols(query_tokens[i]), similar_terms[i]))
    log["expansion_terms"] = expansion_terms


    results = []

    # execute query to retrieve tweets using the final expanded query
    for i in range(len(queries)):

        search = elastic_params
        search["terms"] = trim_symbols(query_tokens[i]) + expansion_terms[i]
        search["hashtags"] = [h.lower() for h in trim_symbols([t for t in query_tokens[i] if t._.is_hashtag ])]
        search["users"] = trim_symbols([t for t in query_tokens[i] if t._.is_user ])
        search["entities"] = trim_symbols([t for t in query_tokens[i] if t.ent_type_ ])

        results.append(es_client.get_tweets(search))
    
    del es_client

    # ------------------ LOG RESULTS ------------------
    now = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
    out_path = os.path.join("out", embedding_params["type"], now)
    
    print(f'Writing results to {out_path}')

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    with open(os.path.join(out_path, "log.json"), "w") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)
    file.close()

    with open(os.path.join(out_path, "results.json"), "w") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)
    file.close()

    print('Done!')

    return results