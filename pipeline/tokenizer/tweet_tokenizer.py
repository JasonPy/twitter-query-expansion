import re
from spacy.tokenizer import _get_regex_pattern


def add_hashtag_pattern(nlp, pattern) -> None:
    """
    Add a regex pattern to the tokenizer.

    Parameters
    ----------
    nlp : spacy.language.Language
        The spaCy model to modify.

    pattern: str
        Some regular expression.
    """

    # get default pattern for tokens that don't get split
    re_token_match = _get_regex_pattern(nlp.Defaults.token_match)

    # add your patterns
    re_token_match = f"({re_token_match}|{pattern})"

    # overwrite token_match function of the tokenizer
    nlp.tokenizer.token_match = re.compile(re_token_match).match


def separate_hashtags(text: str) -> str:
    """
    Insert a whitespace if hashtags are missing a gap in between. 

    Parameters 
    ----------
    text: str
        the text to modify.

    Returns
    ----------
    text: str
        The modified text.
    """

    for i, j in enumerate(text):
        if (text[i] == "#" and i > 0):
            if text[i-1] != " ":
                    text = text[:i] + " " + text[i:]
                    i+=1
    return text

