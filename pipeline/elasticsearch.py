from elasticsearch import Elasticsearch
import json

class ElasticsearchClient:
    def __init__(self, credentials, index) -> None:

        self._host = credentials['URL']
        self._user = credentials['USER']
        self._cert_path = credentials['CERT']
        self._index = index
        self.connection = None


    def connect(self, password) -> Elasticsearch:
        """
        Connect to an elastic search API.
        """
        try:
            self.connection = Elasticsearch(self._host, basic_auth=(self._user, password), ca_certs=f"auth/{self._cert_path}")
            print("Successfully connected to", self._host)

        except Exception:
            print("Unable to connect to", self._host)
            exit(1)


    def compose_aggregation_query(self, query_path, terms) -> json:
        """
        TODO:
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


    def get_cooccurring_terms(self, query, terms):
        """
        TODO:
        """
        agg_query = self.compose_aggregation_query(query, terms)

        try:
            res = self.connection.search(index=self._index, size=agg_query["size"], aggregations=agg_query["aggs"])
        except Exception:
            print("Error while executing aggregation query.")
        
        cooccurrences = {}
        cooccurrences.update((t["key"], t["doc_count"]) for t in res["aggregations"]["interactions"]["buckets"])

        return cooccurrences


    def compose_search_query(search, terms, hashtags, entities, params) -> json:
        
        query = search['query']

        # filter retweets
        if params["retweet"]:
            del query['bool']['must_not']['term']
        
        # boost hashtags
        if params["hashtag_boost"] is not None:
            query['bool']['should'][1]['terms']["boost"] = params["hashtag_boost"]
        
        # if present, insert hashtags from query
        if len(hashtags) > 0 :
            query['bool']['must']['terms_set']['hashtags']['terms'] = [h[1:].lower() for h in hashtags]
        else:
            del query['bool']['must']
        
        # set date range for tweets
        query['bool']['filter'][0]['range']['created_at']['gte'] = params["tweet_range"][0]
        query['bool']['filter'][1]['range']['created_at']['lte'] = params["tweet_range"][1]

        # insert the query terms
        query['bool']['should'][0]['match']['txt']['query'] = ' '.join(terms)
        query['bool']['should'][1]['terms']['hashtags'] = [q.lower() for q in terms]

        return search