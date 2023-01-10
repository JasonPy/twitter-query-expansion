{
    "settings": {
        "index": {
            "number_of_shards": 16,
            "number_of_replicas": 1,
            "max_ngram_diff": 20
        },
        "analysis": {
            "analyzer": {
                "tweet_analyzer": {
                    "type": "custom",
                    "char_filter": [
                        "tweet_syntax",
                        "html_strip"
                    ],
                    "tokenizer": "punctuation",
                    "filter": [
                        "tweet_syntax_marker",
                        "length_filter",
                        "custom_ascii_folding",
                        "lowercase",
                        "apostrophe",
                        "decimal_digit",
                        "german_stop",
                        "german_normalization",
                        "german_n_gram",
                        "german_stemmer",
                        "unique"
                    ]
                }
            },
            "char_filter": {
                "hashtag_separator": {
                    "type": "pattern_replace",
                    "pattern": "((?:#\\w+|\\w+))(?=#\\w+|#)",
                    "replacement": "$1 "
                },
                "tweet_syntax": {
                    "type": "mapping",
                    "mappings": [
                        "RT => _retweet_",
                        "@ => _user_"
                    ]
                }
            },
            "tokenizer": {
                "punctuation": {
                    "type": "pattern",
                    "pattern": "[ -.,;:!?/#]"
                }
            },
            "filter": {
                "length_filter": {
                    "type": "length",
                    "min": 2,
                    "max": 20
                },
                "german_stop": {
                    "type": "stop",
                    "stopwords": "_german_"
                },
                "german_stemmer": {
                    "type": "stemmer",
                    "language": "light_german"
                },
                "custom_ascii_folding": {
                    "type": "asciifolding",
                    "preserve_original": true
                },
                "tweet_syntax_marker": {
                    "type": "keyword_marker",
                    "keywords": ["_hashtag_", "_retweet_", "_user_"]
                },
                "german_n_gram": {
                    "type": "ngram",
                    "min_gram": 3,
                    "max_gram": 8,
                    "preserve_original": true
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "txt": {
                "type": "text",
                "analyzer": "tweet_analyzer"
            },
            "hashtags": {
                "type": "keyword"
            },
            "created_at": {
                "type": "date"
            }
        }
    }
}