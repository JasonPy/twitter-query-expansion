# _Twitter Query Expansion_
Modify an initial user query by enriching it with suitable expansion terms. Different word embedding models are applied such as FastText and Word2Vec to find expansions. Elastic Search is used to find relevant tweets by using the reformulated user query.

**Outline**

[[_TOC_]]

# Structure
- **Pipeline** - The Pipeline itself is in the `pipeline` module folder, which contains the three main components e.g. [text_processor.py](), [embedding.py]() and [elasticsearch.py](). Custom tokenizer and matcher for SpaCy's text processing are listed under `pipeline/tokenizer` and `pipeline/matcher` respectively. 
The Word Embeddings make use of downloaded models in the `models` directory. Have a look into the `templates` folder to inspect the files for generating an Elastic Search index and queries. 
<br>

- **Scripts** - In the `scripts` folder all executable files for working with this package are contained. The [model_loader.py]() downloads a specified *Word2Vec* or *Fasttext* model and converts it into the expected format. For parsing Tweets from a PostgreSQL database into an ElasticSearch index, the [tweet_feeder.py]() is utilized. It allows to filter Tweets to have some minimum number of words. The script [pipeline.py]() handles the invocation of the full pipeline. 
<br>

- **Demo** - In the root directory a [demo.ipynb]() file is provided which demonstrates the use of the Pipeline. This includes downloading the embedding models as well as executing the Pipeline and describing different parameters. It is referred to this file for detailed information.  


# Setup
First of all clone the present repository to your local machine.
```sh
git clone https://git-dbs.ifi.uni-heidelberg.de/practicals/2022-jason-pyanowski
```

This project uses [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today). Make sure it is installed and run the following command in the root of this project to collect all dependencies.

```sh
pipenv install
```
The required python version and installed packages are listed within the [Pipfile]().


# 1. Introduction


## 1.1 Motivation

## 1.2 Goals
- Implement a Pipeline to expand a query with suitable expansion terms
- ...


# 2. Data
The Pipeline requires a collection of Tweets and a Word Embedding model. The employed Twitter data and Word Embeddings are stated below and described briefly.

## 2.1 Twitter Dataset
The Twitter data collection was provided by the [Database Systems Research Group](https://dbs.ifi.uni-heidelberg.de/). It contains about 300,000 german Tweets over a period of about two years related to politics. Initially, this data set is provided in form of a [PostgresSQL](https://www.postgresql.org/) database. The respective scheme is displayed in Figure 2.1. Of particular interest are the Tweets itself and their respective hashtags, user names and named entities.

2.1 Twitter Database ER-Diagram | 2.2 Word Count statistic
:---:|:---:
|<img src="img/twitterdb-er-diagram.png" align="left" /> | <img src="img/tweet-words.png" align="right" />


To search Tweets performantly, an [Elastic Search](https://www.elastic.co/elasticsearch/) index is fed with data from the PostgreSQL database. The indexing is configured by the [es-config.tpl]() template. Tokenization is applied and each token is split at `[ -.,;:!?/#]`. Consequently the following filters are applied to the obtained tokens:
- **Tweet syntax marker**
To identify Twitter-specific symbols like `#`, `@` and Retweets
- **Length Filter**
To keep words with some length in `[2, ... ,20]` 
- **ASCII folding**
Converts non-acsii characters into valid ascii characters
- **Lowercase**
- **Decimal digits**
- **Stop-word removal**
- **Normalization**
For example replaces `ä` with `a`
- **N-Grams**
Especially good for compound words in german language
- **Word stemming**
Use only the root form of a term
- **Unique**
Keep only unique tokens 

To stream Tweets from PostgreSQL to an Elastic Search index, use the provided script [tweet_feeder.py](). The credentials must be specified within the `auth` folder. You can also specify the minimum number of words for Tweets to include. Make sure to have access to a database and a running Elastic Search Cluster and execute
```sh
python3 scripts/tweet_feeder.py
```
```sh
usage: tweet_feeder.py [-h] -i INDEX -t TABLE [-ec ELASTIC_CREDENTIALS]
                       [-pc POSTGRES_CREDENTIALS] [-es ELASTIC_SETTINGS]
                       [-wc WORDCOUNT]

Feed Postgres data into Elastic Search Index

options:
  -h, --help            show this help message and exit
  -i INDEX, --index INDEX
                        Name of Elastic Search index
  -t TABLE, --table TABLE
                        Name of Postgres table
  -ec ELASTIC_CREDENTIALS, --elastic_credentials ELASTIC_CREDENTIALS
                        Path to Elastic Search credentials file
  -pc POSTGRES_CREDENTIALS, --postgres_credentials POSTGRES_CREDENTIALS
                        Path to Postgres credentials file
  -es ELASTIC_SETTINGS, --elastic_settings ELASTIC_SETTINGS
                        Template for new Index (es-config.tpl)
  -wc WORDCOUNT, --wordcount WORDCOUNT
                        Minimum number of words per Tweet
```
An example Tweet within the resulting Index looks as follows:

```yaml
{
    "retweet_count": 30,
    "reply_count": 0,
    "like_count": 0,
    "created_at": "2021-09-01T15:04:20+02:00",
    "txt": "RT @THWLeitung: Seit sieben Wochen ist das #THW im Einsatz, um die Folgen der #Flutkatastrophe zu beseitigen. Dabei sind die Fähigkeiten aller THW-Fachgruppen gefordert. Bisher haben die 13.566 Einsatzkräfte des THW 1.530.000 Einsatzstunden geleistet. Foto: Kai-Uwe Wärner https://t.co/3N7xqdFb21",
    "hashtags": [
        "flutkatastrophe",
        "thw"
    ],
    "word_count": 38
}
```
## 2.2 Word Embedding Models
For the purpose of finding similar terms, word embeddings are utilized. These models are trained on a large corpus of german text data and allow to describe terms in form of multidimensional vectors. The two following models are evaluated regarding this project:

- **Word2Vec:** [German Word2Vec Model](https://devmount.github.io/GermanWordEmbeddings/) 
- **Fasttext:** [German Fasttext Model](https://fasttext.cc/docs/en/crawl-vectors.html) 

This Fasttext[^1] model is trained on Common Crawl and Wikipedia data. The dimension of the vector space is 300 which results in a fairly large model of about 4.5 GB. The Word2Vec[^2] model is small in comparison since it only provides the word vectors. It is trained on german wikipedia data and news articles.

To reduce memory consumption the models are post-processed (see [model_loader.py]()). Each models vectors are compressed by using the L2-norm, reducing the size significantly. However, the drawbacks are that the model can not be used for training anymore, out of vocabulary words are no longer available and the overall performance is slightly reduced.


# 3. Pipeline
In order to find relevant Tweets within a large collection, it is useful to expand the initial user query with suitable terms. Therefore, a structural approach is provided - a configurable pipeline. This pipeline handles the expansion of the user query by firstly processing the initial query terms by the component [Text Processor](#31-text-processing). It outputs a list of tokens with specific information. Based on this, tokens are identified for finding similar terms. 

The selected terms are feed into the Word Embedding models. The component [Word Embedding](#32-word-embedding) handles the process of retrieving $`n`$ possible expansion terms for each selected term. The pipeline allows to download and process arbitrary pre-trained Word Embeddings. 

To determine, if a possible expansion term is suitable, the component [Elastic Search](#33-elastic-search) receives the previously computed terms. By looking at the co-occurrences of the initial term and the expansion term, the most appropriate expansions are chosen. Finally, the query is executed and the Top K Tweets returned.

Depending on the objective, it is possible to configure the terms that should be replaced based on Natural Language properties and is further described in the following subsections and explicitly shown in the [demo.ipynb](). The overall structure of the Pipeline is displayed below.
<p align="center">
  <img src="img/pipeline.png" />
</p>
<div align="center"><i>A. Query Expansion Pipeline</i></div>
</br>

## 3.1 Text Processing
The initial query is processed using [SpaCy](https://spacy.io/). This first part of the pipeline includes the following steps:
- **Tokenize text**
- **Remove stop-words**
- **Detect entities**
- **Determine Part-of-Speech (POS) tags**
- **Mark hashtags**
- **Mark Twitter users**

The output of this processing step is a _SpaCy_ document which consist of tokens. Based on the 

## 3.2 Word Embedding
For finding suitable expansions, different word embedding models can be applied. In the scope of this project, the following two models were used.
- FastText
- Word2Vec

In order to determine the $`n`$ most similar terms based on some input, the vector representation of terms within Word Embeddings is utilized. The similarity between the initial term $`x`$ and the possible expansion term $`y`$ is determined using the cosine similarity of their vector representation $`X, Y \in \mathbb{R}^N`$ respectively. The similarity can then be computed as
```math
SIM_{cos}(X,Y) = \frac{X \cdot Y}{\lVert X \rVert \lVert Y \rVert}
```
For each term the $`n`$ most similar terms are returned and investigated if they can act as an expansion using Elastic Search.

todo: maximum n of Y are new y
word count genauer sagen

## 3.3 Elastic Search
The similar terms - obtained by the Word Embeddings - are ranked based on the Tweet Collection. In order to decide if a found similar term can act as an expansion, the Point-wise Mutual Information[^3] (PMI) is applied. Therefore, Elastic Search [Adjacency Matrix Aggregations](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-adjacency-matrix-aggregation.html) determine the number of co-occurrences $`N_{x,y}`$ of the initial term $`x`$ and the similar term $`y`$, their separate occurrence across the whole document collection $`N_x`$, $`N_y`$. The attribute `word_count` for each Tweet comes in handy now and simplifies the calculation of the total number of words $`N`$. Thus, the probabilities can be computed as
```math
P(x,y) = \frac{N_{x,y}}{N},
P(x) = \frac{N_x}{N},
P(y) = \frac{N_y}{N},
```
and consequently inserted into the formula 
```math
PMI(x,y) = log \left( \frac{P(x,y)}{P(x)P(y)} \right).
```
If a similar term's $`PMI`$ exceeds some threshold $`\tau \in \mathbb{R}`$ it is added as expansion term. These terms are then combined with the terms of the initial user query. The provided template [es-query.tpl]() is filled with the extracted data and the corresponding Elastic Search index is scanned. Finally, the Top $`k`$ Tweets are returned. 


---

# 4. Results
In order to get some intuition on how the selection of expansion terms affect the 

## 4.1 Effects of Structural Procedure
The whole pipeline is configurable - this means that it can be adjusted which part of the query is expanded. The following table shows which parts of the query lead to which expansion terms.

| Initial Query | Noun | Verb | Adjective | Proper Noun | Location | Organization | Hashtag | 
|:---|---|---|---|---|---|---|---|
|`[große Koalition gescheitert unter Merkel? #Groko #SPD #CDU]`||||`[Kanzlerin, Bundeskanzlerin]`| | |`[GroKo, SPD, AFD, CDU, FDP, CSU, Linkspartei]`|
|`[Lauterbach Deutschland Corona-Maßnahmen #Impfung}`|| | |`[Bundesrepublik]`|`[Bundesrepublik]`| |`[impfung, Schutzimpfung]`|
|`[@bundestag Bundestagswahl 2021 Ergebnisse]`|`[Endergebnis, Ergebniss, Gesamtergebnis, Zwischenergebnis]`| | | | | | | |
|`[Gesetzliche Rentenversicherung Rente Mit 67]`| | | | | | | | |
|`[Bundeswehr Afghanistan Krieg stoppen]`|`[bundeswehr, Bundeswehrverwaltung, Kriegs]`| | |`[Pakistan, Hindukusch]` |`[Pakistan, Hindukusch]` | `[bundeswehr, Bundeswehrverwaltung]`| | 

Describe...

## 4.2 Resulting Tweets
How do the results differ for the initial and the expanded user query? To get an intuition, the Top 3 Tweets obtained for each of the two queries are listed. 

| Parameter | Value |
|---|---|
|POS Tags|`['ADJ', 'NOUN', 'PROPN', 'VERB']`|
|Entity Types|`['LOC', 'ORG']`|
|Hashtag|`True`|
|User|`True`|
|Number most similar terms|`5`|


| Rank | Tweets from Initial Query | Tweets from Expanded Query | 
|:---:|---|---|
|1|Die #GroKo #SPD #CDU #CSU will kein #Löschmoratorium zur Sicherung von Akten, sie will keinen Untersuchungsausschuss, sondern eine Enquete zum Desaster in #Afghanistan -  niemand übernimmt Verantwortung und parlamentarische Aufklärung wird blockiert. Das ist die Lage.|Die erste #GroKo in Deutschland vereinte 1966 noch 86,9% der Wähler:innen hinter sich. Das lässt sich heute nicht mal mit einer Mosambik-Koalition erreichen. Aber wenn man #CDU und #FDP einerseits und #SPD und #Grüne anderseits beobachtet, könnte man das glatt als Lösung sehen.|
|2|#SPD und #CDU sind sich bis zur Unkenntlichkeit ähnlich geworden und natürlich wäre eine Neuauflage der #GroKo die bequemste Koa von allen. Kann man nur zuverlässig verhindern, wenn #CSU + + #SPD + #CDU keine eigene Mehrheit bekommen. #triell|6. Als @GrueneBundestag haben wir die Aufklärung im Untersuchungsausschuss #Breitscheidplatz gegen massive Widerstände der #Bundesregierung und #GroKo #CDU #CSU #SPD maßgeblich vorangetrieben. Hier eine Bilanz: https://t.co/Y8fb7v6oa8|
|3|Wenn die Partei des Versagens beim Glasfaserausbau #CDU auf #Digitalisierung macht, und die #Kohlepartei #SPD plötzlich vorgibt,  #KlimaSchutz betreiben zu wollen, weißt Du, die #GroKo erzählt 3 Wochen vor der #btw21 alles mögliche, um an der Macht zu bleiben.|Aber…. Ach so, das wollten ja #SPD #CDU und #CSU explizit nicht. Obwohl Grüne, FDP und Linke das beantragt hatten. Die #GroKo nimmt es schlicht billigend in Kauf, dass bis zu 300 Abgeordnete mehr in den Bundestag kommen. Es wäre schlicht verheerend.|

*Number of overlaps*
*Eventull sortieren nach likes, RT?*


## 4.3 Comparison of Fasttext and Word2Vec
For each query, the respective tokens (after Text Processing) are displayed in the table below. In the right column the _possible_ expansion terms from the Word2Vec Embedding are stated. A total of the 5 most similar terms was obtained using the configuration of the pipeline stated in table .

|Word2Vec Expansions|Query Token|Fasttext Expansions|
|---:|:---:|:---|
a|`groß` <br> `Koalition`<br> `scheitern`<br> `Merkel`<br> `Groko`<br> `SPD`<br> `CDU`|`[riesengroß,gross,klein,große,riesig]` <br>`[Regierungskoalition,Koalitionsrunde,Koalitionspartei,Koalitionen,Koalitionskrise]` <br> `[scheitert,gescheitert,scheiterten,scheitern, scheiterte]`<br> `[Kanzlerin,Merkels,Bundeskanzlerin,Steinmeier,Schäuble]`<br> `[GROKO,Groko,SPD,CDU-CSU,AFD]` <br> `[CDU,FDP,CDU,Linkspartei,Sozialdemokraten]` <br> `[SPD,FDP,CSU,CSU-MdB,SPD-MdB]`
<|`Lauterbach` <br> `Deutschland`<br> `Impfung`|`[Lauterbachs,Lauterbach-Schlitz,Reichenbach,Stickendorf,Lauterbrunn]` <br> `[Österreich,Europa,Bundesrepublik,Schweiz,Frankreich]` <br> `[Impfungen,impfung,Schutzimpfung,B-Impfung,FSME-Impfung]` 
a|`Bundestagswahl` <br> `Ergebnis` | `[Bundestagswahlen,Landtagswahl,Bundestagwahl,Bundestagswahljahr,Landtagswahlen]` <br> `[Resultat,Endergebnis,Ergebniss,Gesamtergebnis,Zwischenergebnis]`
a|`Gesetzliche` <br> `Rentenversicherung` <br> `Rente`| `[gesetzliche,Rechtliche,Vertragliche,gesetzlichen,Vertragsrechtliche]` <br> `[Rentenversicherungen,Rentenversicherer,Rentenversicherungsanstalt,Rentenversorgung,Rentenversicherungsträger]` <br> `[Altersrente,Renten,Rentenbeiträge,Rentenleistung,Rentenalter]`
a|`Bundeswehr`<br> `Afghanistan` <br> `Krieg`<br> `stoppen`| `[Bundeswehreinheiten,bundeswehr,Bundeswehr-Kasernen,Bundeswehrverwaltung,Bundeswehrführung]` <br> `[Irak,Pakistan,Afghanistans,Syrien,Hindukusch]` <br> `[Kriege,Krieges,Bürgerkrieg,Kriegen,Kriegs]` <br> `[unterbinden,verhindern,aufzuhalten,stoppen,beenden]` |



# 5. Conclusion
## 5.1 Limitations
- model vectors, no OOV
- no synonyms

## 5.2 Outlook
- include named entities
- news articles

# References
[^1]: P. Bojanowski, E. Grave, A. Joulin, and T. Mikolov, “Enriching Word Vectors with Subword Information,” 2016, doi: 10.48550/ARXIV.1607.04606.
[^2]: T. Mikolov, K. Chen, G. Corrado, and J. Dean, “Efficient Estimation of Word Representations in Vector Space,” 2013, doi: 10.48550/ARXIV.1301.3781.
[^3]: D. Jurafsky and C. Manning, “Natural language processing,” Instructor, vol. 212, no. 998, p. 3482, 2012.
