from elasticsearch import Elasticsearch
from pipeline.utils import pmi, tf_idf

import json

class ElasticsearchClient:
    """
    This class represents an Elastic Search client to handle the connection to an Index.
    """

    def __init__(self, credentials, index) -> None:
        self._host = credentials['URL']
        self._user = credentials['USER']
        self._cert_path = credentials['CERT']
        self._index = index
        self._connection = None


    def connect(self, password) -> None:
        """
        Establishes a connection to an elastic search API.

        Parameters
        ----------
        password : str
            The password to connect to an Elastic Search cluster.
        """
        try:
            self._connection = Elasticsearch(self._host, basic_auth=(self._user, password), ca_certs=f"auth/{self._cert_path}")
            print("Successfully connected to", self._host)
        except Exception:
            print("Unable to connect to", self._host)
            exit(1)


    def get_total_number_of_tweets(self) -> int:
        """
        Count the number of documents in the index.

        Returns
        ----------     
        count: int
            The number of documents in _index.  
        """
        try:
            # run search request
            res = self._connection.count(index=self._index)
        except Exception:
            print("Error while executing count query for index", self._index)
        
        return res["count"]


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
            res = self._connection.search(index=self._index, size=query["size"], query=query["query"], aggregations=query["aggs"])
        except Exception:
            print("Error while executing search query for index", self._index)

        tweets = {}

        # collect results
        tweets["hits"] = res["hits"]["total"]["value"]
        tweets["took"] = res["took"]
        tweets["tweets"] = res["hits"]["hits"]

        return tweets


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

        # filter retweets
        if params["retweet"]:
            del query['bool']['must_not']['term']
        
        # boost hashtags
        if params["hashtag_boost"] is not None:
            query['bool']['should'][1]['terms']["boost"] = params["hashtag_boost"]
        
        # if present, insert hashtags from query
        if len(params["hashtags"]) > 0 :
            query['bool']['must']['terms_set']['hashtags']['terms'] = [h for h in params["hashtags"]]
        else:
            del query['bool']['must']
        
        # set date range for tweets
        query['bool']['filter'][0]['range']['created_at']['gte'] = params["tweet_range"][0]
        query['bool']['filter'][1]['range']['created_at']['lte'] = params["tweet_range"][1]

        # insert the query terms
        query['bool']['should'][0]['match']['txt']['query'] = ' '.join(params["terms"])
        query['bool']['should'][1]['terms']['hashtags'] = [q.lower() for q in params["hashtags"]]

        return search_query


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
            res = self._connection.search(index=self._index, size=agg_query["size"], aggregations=agg_query["aggs"])
        except Exception:
            print("Error while executing aggregation query for index", self._index)
        
        co_occurrences = {}
        co_occurrences.update((t["key"], t["doc_count"]) for t in res["aggregations"]["interactions"]["buckets"])

        return co_occurrences


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


    def get_expansion_terms(self, candidate_terms: list, similar_terms: json, threshold: float=0.01) -> list:
        """
        Given some candidate terms and their corresponding similar terms, check if the terms
        can act as expansion terms. This is done by looking at the co-occurrence of both terms using TF-IDF.

        Parameters
        ----------
        candidate_terms: list
            The initial terms of the query.

        similar_terms: json
            The possible expansion terms.

        threshold: float = 0.01
            The threshold to include a term based on TF-IDF. 

        Returns
        -------
        expansion_terms : list
            The terms that are suitable to expand a query.
        """
        if not similar_terms:
            return

        co_occurrences = self.get_co_occurring_terms(similar_terms)
        num_of_tweets = self.get_total_number_of_tweets()

        expansion_terms = []

        for term in candidate_terms:
            if term in co_occurrences.keys():

                term_freq = co_occurrences[term]

                for synonym in similar_terms[term]:
                    if synonym in co_occurrences.keys():
                        synonym_freq = co_occurrences[synonym]

                        # calc how often it occurs
                        alpha = synonym_freq / num_of_tweets

                        # occurs often itself, good term
                        if alpha >= 0.01:
                            expansion_terms.append(synonym)
                            continue

                        if f"{synonym}&{term}" in co_occurrences.keys():
                            joint_freq = co_occurrences[f"{synonym}&{term}"]

                            beta = pmi(num_of_tweets, term_freq, synonym_freq, joint_freq)
                            # joint occurrence often, good expansion
                            if beta >= 0.1:
                                expansion_terms.append(synonym)
                    else:
                        continue

        return expansion_terms

# measure if they occur seperatly more often