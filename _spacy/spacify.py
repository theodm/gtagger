import os

import spacy
from joblib import Memory

memory = Memory(os.path.dirname(os.path.realpath(__file__)) + '/cache')

nlp = spacy.load("de_dep_news_trf")


@memory.cache
def spacify(text):
    return nlp(text)