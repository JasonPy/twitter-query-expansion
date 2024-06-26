import os
import json
import configparser

from datetime import datetime

from pipeline.text_processor import TextProcessor
from pipeline.embedding import WordEmbedding
from pipeline.elasticsearch import ElasticsearchClient


def run(queries: list, embedding_params: json, elastic_params:json) -> json:
    """
    Execute the complete Query Expansion Pipeline. This includes Query pre-processing, the application of Word Embeddings
    to find similar terms and the retrieval of Tweets.
    The parameters and results of the pipeline are stored in the specified output file.

    Parameters
    ----------
    queries: list
        A list of queries.

    embedding_params: json
        Parameters defining embedding-specific configurations.
        
    elastic_params:json
        Parameters defining elastic-specific configurations.

    Returns
    ----------
    res: json
        The resulting Tweets.
    """    
    # prepare logging
    log = {
        "timestamp": datetime.now().strftime("%d-%m-%y_%H:%M:%S"),
        "queries": queries,
        "embedding_params": embedding_params,
        "elastic_params": elastic_params,
    }


    # ------------------ TEXT PROCESSING ------------------ 
    print('Processing text using SpaCy...')
    text_processor = TextProcessor()

    docs = []

    # for each query, invoke the SpaCy pipeline
    for query in queries:
        doc = text_processor.invoke(query)
        docs.append(doc)
    log["docs"] = [d.text for d in docs]


    query_tokens = []

    # for each processed query, filter the tokens depending on the specified parameters
    for doc in docs:
        filtered_tokens = text_processor.get_filtered_tokens(doc, embedding_params)
        query_tokens.append(filtered_tokens)
    log["query_tokens"] = [[token.text for token in tokens] for tokens in query_tokens]


    # ------------------ WORD EMBEDDINGS ------------------
    print(f'Evaluating {embedding_params["type"]} model...')
    model = WordEmbedding(model=embedding_params["model"])

    similar_terms = []

    # find similar terms using embedding model 
    for tokens in query_tokens:
        similar_terms.append(model.get_similar_terms(text_processor.trim_symbols(tokens), embedding_params["num_nearest_terms"]))
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

    print('Retrieving Tweets...')

    expansion_terms = []

    # find most suitable expansion terms
    for i in range(len(queries)):
        expansion_terms.append(es_client.get_expansion_terms(text_processor.trim_symbols(query_tokens[i]), similar_terms[i]))
    log["expansion_terms"] = expansion_terms

    results = []

    # execute query to retrieve tweets using the final expanded query
    for i in range(len(queries)):
        search = elastic_params.copy()
        search["terms"] = text_processor.trim_symbols(query_tokens[i]) + expansion_terms[i]
        search["hashtags"] = [h.lower() for h in text_processor.trim_symbols([t for t in docs[i] if t._.is_hashtag ])]
        search["users"] = text_processor.trim_symbols([t for t in docs[i] if t._.is_user ])
        search["entities"] = text_processor.trim_symbols([t for t in docs[i] if t.ent_type_ ])

        results.append(es_client.get_tweets(search))
    
    del es_client

    # ------------------ LOG RESULTS ------------------
    now = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
    out_path = os.path.join("output", embedding_params["type"], now)
    
    print(f'Writing results to {out_path}')

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    with open(os.path.join(out_path, "log.json"), "w") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)
    file.close()

    with open(os.path.join(out_path, "results.json"), "w") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)
    file.close()

    print('Finished!')

    return results