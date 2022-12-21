import json

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