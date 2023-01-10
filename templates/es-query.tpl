{
    "size": 10,
    "query": {
        "bool" : {
            "should": [ 
                { 
                "match": {
                    "txt": {
                        "query": "",
                        "operator": "OR"
                    }
                  }
                }, 
                { 
                "terms": {
                    "hashtags": [],
                    "boost": 1.0
                  }
                }
            ],
            "must": {
                "terms_set": {
                    "hashtags": {
                        "terms": [],
                        "minimum_should_match_script": {
                            "source": "Math.min(params.num_terms, 1)"
                        }
                    }
                }
            },
            "must_not": {
                "term": {"txt": "_retweet_"}
            },
            "filter": [
                { "range": {"created_at": {"gte": ""}}},
                { "range": {"created_at": {"lte": ""}}}
            ]
        }
    },
    "aggs": {
        "sample": {
            "sampler": {
                "shard_size": 500
            },
            "aggs": {
                "keywords": {
                    "significant_terms": {
                        "field": "hashtags"
                    }
                }
            }
        }
    },
    "collapse": {},
    "sort": {}
}

