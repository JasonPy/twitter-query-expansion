def compose_aggregation_query(query, terms):
    """
    """
    filters = query["aggs"]["interactions"]["adjacency_matrix"]["filters"]

    # compose the aggregation query with the candidate terms
    for term in terms:
        filters[term] = { "term" : { "txt" : term.lower() }}

        for synonym in terms[term]:
            filters[synonym] = { "term" : { "txt" : synonym.lower() }}

    return query


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