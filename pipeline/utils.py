import numpy as np

from pathlib import Path


def get_project_root() -> Path:
    """
    Get the absolute path of the project's directory
    """
    return Path(__file__).parent.parent


def pmi(total, w1, w2, w12) -> float:
    """
    Calculate the Point-wise Mutual Information as log(P(w12) / (P(w1) * P(w2))), where P(w1) 
    is the probability of w1 occurring, P(w2) is the probability of w2 occurring, and P(w1, w2) is 
    the probability of w1 and w2 occurring together.

    Returns
    -------
    pmi : float
        The Point-wise Mutual Information.
    """
    p12 = w12 / total
    p1 = w1 / total
    p2 = w2 / total
    return np.log(p12 / (p1 * p2))


def tf_idf(tf, df) -> float:
    """
    """
    return tf / df