# Twitter Query Expansion
This project aims at reformulating a user query by enriching it with suitable terms. For this purpose different word embedding models are applied such as FastText and Word2Vec. The selection of candidate terms to enrich the query are determined using spaCy. Elastic Search is used to find relevant tweets by using the reformulated user query.

**Contents**
[[_TOC_]]



## Project Description
In order to find relevant Tweets within a large collection, it is useful to expand the initial user query with suitable terms. These expansion terms are determined using the provided Pipeline which consists of:
1. Text Preprocessing  
2. Word Embedding
3. Elastic Search

This project aims at reformulating a query by enriching it with suitable expansion terms. For this purpose the initial query is preprocessed using *SpaCy*. This first part of the pipeline includes the following steps:
- tokenize text
- remove stop-word
- detect entities
- find Part-of-Speech (POS) tags
- mark hashtags
- mark Twitter users

For the remaining terms, suitable expansions need to be found. Different word embedding models are therefore applied such as *FastText* and *Word2Vec*. Based on the vector representation of terms, similar terms are retrieved and consequently analyzed. To determine if an expansion term is suitable, the Point-wise Mutual Information (PMI) measure is applied, with respect to the co-occurrences of the initial query term and the expansion term. 

Finally, Elastic Search is used to obtain relevant tweets by using the reformulated user query.  

## Structure
In the root directory a `demo.ipynb` file is provided which demonstrates the use of the Pipeline. This includes downloading the dataset and models as well as executing the Pipeline and describing different parameters. It is referred to this file for detailed information.  

The Pipeline itself is in the `pipeline` module folder, which contains the three main components e.g. `text_processor.py`, `embedding.py` and `elasticsearch.py`. Custom tokenizer and matcher for SpaCy's text processing are listed under `pipeline/tokenizer` and `pipeline/matcher` respectively. The Word Embeddings make use of downloaded models in the `models` directory. Have a look into the `templates` folder to inspect the files for generating an Elastic Search index and queries. 

In the `scripts` folder all executable files for working with this package are contained. The `model_loader.py` downloads a specified *Word2Vec* or *Fasttext* model and converts it into the expected format. For parsing Tweets from a PostgreSQL database into an ElasticSearch index, the `tweet_feeder.py` is utilized. It allows to filter Tweets to have some minimum number of words. The script `pipeline.py` handles the invocation of the full pipeline. 

## Setup
This project uses `pipenv`. Make sure it is installed. (See [installation guide](https://pipenv.pypa.io/en/latest/#install-pipenv-today).)


To work with some data, the Database Systems Research Group provided a PostgreSQL database dump. This includes german Tweets over a period of about two years related with politics. To make use of them, an Elastic Search index is fed with this data. Make sure to have access to a database and a running Elastic Cluster.

## Twitter Data

## Results

## Limitations

## Contact 
