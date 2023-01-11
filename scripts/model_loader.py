import os
import urllib.request
import zipfile
import gzip

from gensim.models import KeyedVectors

MODELS_PATH = "./models"


def load_model(type: str, url: str) -> None:
    """
    Load an Word Embedding model from some specified url.
    The model is stored under './models' in a folder named by 'type'.

    Parameters
    ----------
    type: str
        The type of the embedding.

    url: str
        The models download link.
    """

    dir = f"{MODELS_PATH}/{type}/"

    if not os.path.exists(dir):
        os.makedirs(dir)

    # Get the filename from the url
    filename = os.path.basename(url)
    
    # Download the file
    print("Downloading model - this may take a while...")
    try:
        urllib.request.urlretrieve(url, dir + filename)
    except Exception:
        print("Exception while downloading model")

    # Unzip the file if it's a .zip or .gz file
    if filename.endswith(".zip"):
        with zipfile.ZipFile(dir + filename, "r") as zip:
            zip.extractall(path=dir)
        os.remove(dir + filename)

    elif filename.endswith(".gz"):
        with gzip.open(dir + filename, "rb") as gz:
            with open(dir + type.replace(".gz", ""), "wb") as out:
                out.write(gz.read())
        os.remove(dir + filename)
    
    compress(dir + filename)
   

def compress(path: str) -> None:
    """
    Load a Word Embedding model using Gensim's KeyedVectors library.
    Compress the model according to the L2-norm and save it in the specified directory.

    path: str
        The directory of the model file.
    """
    print("Compress model...")
    model = KeyedVectors.load_word2vec_format(path)
    model.fill_norms()
    model.save(f"{path}.model")
