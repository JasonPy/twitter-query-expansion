import spacy

from spacy.language import Language
from spacy.matcher import Matcher
from spacy.tokens import Token

@Language.factory("user_matcher")
def create_user_matcher(nlp, name):
    return UserMatcher(nlp.vocab)

class UserMatcher:
    """
    The purpose of this class is to detect users and mark them.
    This is done by looking for an @-symbol.
    """
    def __init__(self, vocab):
        patterns = [ [{"ORTH": {"REGEX": "@\w+"}}] ]

        # Register a new token extension to mark users
        Token.set_extension("is_user", default=False)
        self.matcher = Matcher(vocab)
        self.matcher.add("user_matcher", patterns)

    def __call__(self, doc):
        # This method is invoked when the component is called on a Doc
        matches = self.matcher(doc)
        users = []  # Collect the matched spans here

        for match_id, start, end in matches:
            if doc.vocab.strings[match_id] == "user_matcher":
                users.append(doc[start:end])
            
        with doc.retokenize() as retokenizer:
            for span in users:
                retokenizer.merge(span)
                for token in span:
                    token._.is_user = True  # Mark token as user
        return doc