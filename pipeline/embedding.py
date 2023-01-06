from gensim.models import KeyedVectors
import fasttext

class WordEmbedding():
    """
    Base class
    """
    def get_similar_terms(self, terms, n: int):
        """
        TODO:
        """
        similar_terms = {}

        if isinstance(terms, list):
            # Handle the input as a list of items
            for term in terms:
                similar_term = self.get_similar(term, n)
                if similar_term is not None:
                    similar_terms[f"{term}"] = similar_term
            return similar_terms
        else:
            # Handle the input as a single item
            similar_terms[f"{terms}"] = self.get_similar(terms, n)
            return similar_terms


class Word2Vec(WordEmbedding):
    """
    """

    def __init__(self, model):
        """
        """
        self.model = KeyedVectors.load_word2vec_format(fname=model, no_header=False, binary=True)


    def get_similar(self, term: str, n: int) -> list:
        """
        Get the most similar terms given a single term.

        Parameters
        ----------
        term : str
            The term to find similar terms for.
        n : int
            The number of similar terms returned.

        Returns
        -------
        similar_terms : List[str]
            The similar terms.
        """

        # obtain most similar words terms
        if self.model.has_index_for(term):
            similar_terms = self.model.most_similar(term)[:n]
            return [t[0].replace("_"," ") for t in similar_terms]


class FastText(WordEmbedding):
    """
    """

    def __init__(self, model):
        """
        """
        self.model = fasttext.load_model(model)


    def get_similar(self, term: str, n: int) -> list:
        """
        Get the most similar terms given a single term.

        Parameters
        ----------
        term : str
            The term to find similar terms for.
        n : int
            The number of similar terms returned.

        Returns
        -------
        similar_terms : List[str]
            The similar terms.
        """

        # obtain most similar terms
        similar_terms = self.model.get_nearest_neighbors(term, k=n)
        return [n[1] for n in similar_terms]