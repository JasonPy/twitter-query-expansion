# Twitter Query Expansion
This project aims at reformulating a user query by enriching it with suitable terms. For this purpose different word embedding models are applied such as *FastText* and *Word2Vec*. The selection of candidate terms to enrich the query are determined using spaCy. Finally, Elastic Search is used to find relevant tweets by using the reformulated user query.  

# Feed Tweets from Postgres to Elastic Search
In order to work with some data, a twitter data dump was provided. The data is stored in form of a PostgreSQL database. For a fast and rich full text search, Elastic Search (ES) is utilized. Therefore, the data must be parsed from the database into an index of ES. The script `scripts/tweet_feeder.py` handles this crucial task. 

Make sure to run `pipenv shell` to activate the virtual environment. Also consider the command line arguments and execute the script from the projects root directory. 

# Query Reformulation Pipeline
To evaluate and modify the processing of the initial user query, spaCy is used. The jupyter notebook `query-reformulation-pipeline.ipynb` covers all the steps from preprocessing over the application of word embeddings up to formulating the final query for Elastic Search.

