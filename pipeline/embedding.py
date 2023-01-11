from gensim.models import KeyedVectors
import json

class WordEmbedding:
    """
    Base class to handle different Word Embeddings.
    """

    def __init__(self, model):
        """
        Initialize and load specified model from a file.
        """
        self.model = KeyedVectors.load(fname=model, mmap='r')

    
    def get_similar_terms(self, terms: list[str], n: int) -> json:
        """
        """
        if not terms:
            return

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
        if self.model.has_index_for(term):
            similar_terms = self.model.most_similar(term)[:n]
            return [t[0].replace("_"," ") for t in similar_terms]
