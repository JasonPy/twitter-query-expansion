import spacy

from spacy.language import Language
from spacy.matcher import Matcher
from spacy.tokens import Token

@Language.factory("hashtag_matcher")
def create_hashtag_matcher(nlp, name):
    return HashtagMatcher(nlp.vocab)

class HashtagMatcher:
    """
    The purpose of this class is to detect hashtags and mark them.
    This is done by looking for an #-symbol.
    """
    def __init__(self, vocab):
        patterns = [ [{"ORTH": {"REGEX": "#\w+"}}] ]

        # Register a new token extension to mark hashtags
        Token.set_extension("is_hashtag", default=False)
        self.matcher = Matcher(vocab)
        self.matcher.add("hashtag_matcher", patterns)

    def __call__(self, doc):
        # This method is invoked when the component is called on a Doc
        matches = self.matcher(doc)
        hashtags = []  # Collect the matched spans here

        for match_id, start, end in matches:
            if doc.vocab.strings[match_id] == "hashtag_matcher":
                hashtags.append(doc[start:end])
            
        with doc.retokenize() as retokenizer:
            for span in hashtags:
                retokenizer.merge(span)
                for token in span:
                    token._.is_hashtag = True  # Mark token as hashtag
        return doc