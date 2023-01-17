import elasticsearch
import json

from pipeline.utils import pmi, npmi

class ElasticsearchClient(elasticsearch.Elasticsearch):
    """
    This class represents an Elastic Search client to handle the connection to an Index.
    """

    def __init__(self, credentials, index) -> None:
        self._host = credentials['URL']
        self._user = credentials['USER']
        self._cert_path = credentials['CERT']
        self._index = index

        super().__init__(self._host, basic_auth=(self._user, credentials['PWD']), ca_certs=f"auth/{self._cert_path}")


    def get_total_word_count(self) -> int:
        """
        Count the number of documents in the index.

        Returns
        ----------     
        count: int
            The number of documents in _index.  
        """

        query = {
            "size": 0,
            "aggs": {
                "total_word_count": { "sum": { "field": "word_count" } }
            }
        }
        try:
            # run search request
            res = self.search(index=self._index, size=query["size"], aggregations=query["aggs"])
        except elasticsearch.ApiError:
            print("Error while executing count query for index", self._index)
        
        return res["aggregations"]["total_word_count"]["value"]


    def get_tweets(self, params: json) -> json:
        """
        Get all tweets from an index given a query.

        Parameters
        ----------
        params : json
            The parameters to execute a search query.

        Returns
        -------
        tweets : json
            The retrieved Tweets.
        """

        # compose the query based on predefined template
        query = self.compose_search_query('templates/es-query.tpl', params)

        try:
            # run search request
            res = self.search(index=self._index, size=query["size"], query=query["query"], aggregations=query["aggs"])
        except elasticsearch.ApiError:
            print("Error while executing search query for index", self._index)

        tweets = {}

        # collect results
        tweets["hits"] = res["hits"]["total"]["value"]
        tweets["took"] = res["took"]
        tweets["tweets"] = res["hits"]["hits"]

        return tweets


    def get_co_occurring_terms(self, terms) -> json:
        """
        Execute search query in order to determine co-occurring terms.
        Done by using Matrix Aggregation and finding mutual occurrences in a tweet.

        Parameters
        ----------
        terms : list
            The terms to include in the co-occurrence finding process.

        Returns
        -------
        co_occurrences : json
            The co-occurrences.
        """

        agg_query = self.compose_aggregation_query('templates/es-adjacency-matrix.tpl', terms)

        try:
            res = self.search(index=self._index, size=agg_query["size"], aggregations=agg_query["aggs"])
        except elasticsearch.ApiError:
            print("Error while executing aggregation query for index", self._index)
        
        co_occurrences = {}
        co_occurrences.update((t["key"], t["doc_count"]) for t in res["aggregations"]["interactions"]["buckets"])

        return co_occurrences


    def get_expansion_terms(self, candidate_terms: list, similar_terms: json, threshold: float=.5, measure=npmi) -> list:
            """
            Given some candidate terms and their corresponding similar terms, check if the terms
            can act as expansion terms. This is done by looking at the co-occurrence of both terms using TF-IDF.

            Parameters
            ----------
            candidate_terms: list
                The initial terms of the query.

            similar_terms: json
                The possible expansion terms.

            threshold: float
                The threshold to include a term based on TF-IDF. 

            measure: func
                A function that exhibits some measure to calculate similarity of terms.

            Returns
            -------
            expansion_terms : list
                The terms that are suitable to expand a query.
            """
            if not similar_terms:
                return []

            co_occurrences = self.get_co_occurring_terms(similar_terms)
            total_word_count = self.get_total_word_count()

            expansion_terms = []

            for term in candidate_terms:
                if term in co_occurrences.keys():

                    term_freq = co_occurrences[term]

                    for synonym in similar_terms[term]:
                        if synonym in co_occurrences.keys():
                            synonym_freq = co_occurrences[synonym]

                            if f"{synonym}&{term}" in co_occurrences.keys():
                                joint_freq = co_occurrences[f"{synonym}&{term}"]

                            elif f"{term}&{synonym}" in co_occurrences.keys():
                                joint_freq = co_occurrences[f"{term}&{synonym}"]

                            else:
                                continue

                            beta = measure(total_word_count, term_freq, synonym_freq, joint_freq)
                            if beta >= threshold:
                                expansion_terms.append(synonym)
                        else:
                            continue

            return expansion_terms


    def compose_aggregation_query(self, query_path, terms) -> json:
        """
        Based on a template, compose an Matrix Aggregation query. 

        Parameters
        ----------
        query_path : str
            The path to the query template.

        terms: json
            The terms to fill into the template. 

        Returns
        -------
        agg_query : json
            The aggregation query.
        """

        # load the predefined aggregation query
        with open(query_path, 'r') as q:
            agg_query = json.load(q)

        filters = agg_query["aggs"]["interactions"]["adjacency_matrix"]["filters"]

        # compose the aggregation query with the candidate terms
        for term in terms:
            filters[term] = { "term" : { "txt" : term.lower() }}

            for synonym in terms[term]:
                filters[synonym] = { "term" : { "txt" : synonym.lower() }}

        return agg_query


    def compose_search_query(self, query_path: str, params: json) -> json:
            """
            Load a predefined template and manipulate it according to specific configurations.

            Parameters
            ----------
            query_path : str
                The path to the query template..
            
            params: json
                The parameters to fill into the template.

            Returns
            -------
            search_query : json
                The search object with filled in data.
            """

            with open(query_path, 'r') as q:
                search_query = json.load(q)
            query = search_query['query']

            if params["num_of_tweets"]:
                search_query["size"] = params["num_of_tweets"]

            # filter retweets
            if params["retweet"]:
                del query['bool']['must_not']['term']
            
            # boost hashtags
            if params["hashtag_boost"]:
                query['bool']['should'][1]['terms']["boost"] = params["hashtag_boost"]
            
            # if present, insert hashtags from query
            if len(params["hashtags"]) > 0 :
                query['bool']['must']['terms_set']['hashtags']['terms'] = [h for h in params["hashtags"]]
            else:
                del query['bool']['must']
            
            # set date range for tweets
            if params["tweet_range"]:
                query['bool']['filter'][0]['range']['created_at']['gte'] = params["tweet_range"][0]
                query['bool']['filter'][1]['range']['created_at']['lte'] = params["tweet_range"][1]

            # insert the query terms
            if params["terms"]:
                query['bool']['should'][0]['match']['txt']['query'] = ' '.join(params["terms"])

            if params["hashtags"]:
                query['bool']['should'][1]['terms']['hashtags'] = [q.lower() for q in params["hashtags"]]

            return search_query

    