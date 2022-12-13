# Twitter Query Expansion

This project aims at reformulating a user query by enriching it with suitable terms. For this purpose different word embedding models are applied such as *FastText* and *Word2Vec*. The selection of candidate terms to enrich the query are determined using spaCy. 

# Feed Tweets from Postgres to Elastic Search
In order to work with some data, a twitter data dump was provided. The data is stored in form of a PostgreSQL database. For a fast and rich full text search, Elastic Search (ES) is utilized. Therefore, the data must be parsed from the database into an index of ES. The script `TweetFeeder.py` handles this crucial task. 

# Run Query Reformulation Pipeline
To evaluate and modify the processing of the initial user query, spaCy is used. The jupyter notebook `query-reformulation-pipeline.ipynb` covers all the steps from preprocessing over the application of word embeddings up to formulating the final query for Elastic Search.

