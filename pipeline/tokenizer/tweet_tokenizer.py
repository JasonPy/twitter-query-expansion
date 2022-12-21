import re
from spacy.tokenizer import _get_regex_pattern


def add_pattern(nlp, pattern):
    # get default pattern for tokens that don't get split
    re_token_match = _get_regex_pattern(nlp.Defaults.token_match)

    # add your patterns (here: hashtags and in-word hyphens)
    re_token_match = f"({re_token_match}|{pattern})"

    # overwrite token_match function of the tokenizer
    nlp.tokenizer.token_match = re.compile(re_token_match).match

    return nlp


def separate_hashtags(doc):
    """
    Insert a whitespace if hashtags are missing a gap in between.  
    """
    text = " ".join(token.text for token in doc)

    for i, j in enumerate(text):
        if (text[i] == "#" and i > 0):
            if text[i-1] != " ":
                    text = text[:i] + " " + text[i:]
                    i+=1
    return text

