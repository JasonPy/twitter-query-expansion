import spacy as sp

from pipeline.tokenizer.tweet_tokenizer import separate_hashtags, add_hashtag_pattern

import pipeline.matcher.hashtag_matcher
import pipeline.matcher.user_matcher


class TextProcessingPipeline:
    """
    A natural language processing pipeline that uses a spaCy model to process text.
    """

    def __init__(self, model: str) -> None:
        """
        Initialize the pipeline with a spaCy model.
        Add custom tokenization rules and matchers.

        Parameters
        ----------
        model : str, optional
            The name or path of the spaCy model to use.
        """
        self.nlp = sp.load(model)

        # Custom tokenization pattern for hashtags
        pattern = r'#\w+|\w+-\w+'

        # Add the custom pattern to the tokenizer
        add_hashtag_pattern(self.nlp, pattern)

        # Add the custom matchers
        self.nlp.add_pipe("hashtag_matcher") 
        self.nlp.add_pipe("user_matcher") 

    

    def invoke(self, text: str) -> sp.tokens.doc.Doc:
        """
        Process the input text with the pipeline.

        Parameters
        ----------
        text : str
            The input text to process.

        Returns
        -------
        doc : spacy.tokens.doc.Doc
            The processed `Doc` object.
        """
        text = separate_hashtags(text)
        return self.nlp(text)



    def get_filtered_tokens(self, doc: sp.tokens.doc.Doc, params: any) -> list[sp.tokens.token.Token]:
        """
        Filter the tokens in the Doc to include only the specified parts of the text.
        Hashtags, entities and users have priority over POS tags. If one of them is false, the token
        must not be included even if it is in the POS list.

        Parameters
        ----------
        doc : spacy.tokens.doc.Doc
            The input document to process.
        params : object
            The parameters on the basis of which filtering is performed.

        Returns
        -------
        tokens : list
            The filtered tokens from the input document.Doc` object
        """
        tokens = [ token for token in doc 
            if (token._.is_hashtag and params["hashtag"])
            or (token._.is_user and params["user"])
            or (token.ent_type_ and params["entity"])
            or (token.pos_ in params["pos_list"] and not token._.is_hashtag and not token._.is_user and not token.ent_type_)
        ]
           
        return tokens


    def trim_symbols(self, tokens: sp.tokens.token.Token, symbols = ['#', '@']) -> list[str]:
        """
        Truncate specified symbols from tokens and returns them as string list.

        Parameters
        ----------
        tokens : spacy.tokens.doc.Token
            The input tokens.
        symbols : list
            The symbols that are truncated from each token.

        Returns
        -------
        text : list
            The truncated tokens as string list.

        """
        text = []
         
        # Iterate over the tokens in the doc
        for token in tokens:
            # Check if the token begins with sym
            if token.text[0] in symbols:
                # Remove the symbol from the token text
                text.append(token.text[1:])
            else:
                text.append(token.text)
        return text
