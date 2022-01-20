import json
import sys

from loguru import logger

from spacy2database.doc2database import doc2database
from tigerxml_parser import TigerXMLParser
from tigerdocs_parser import TigerDocs

from database.api import db

logger.remove()
logger.add(sys.stderr, level="INFO")

docs = TigerDocs("./tigerfiles/docs/documents.tsv")
parser = TigerXMLParser("./tigerfiles/tiger/tiger_release_aug07.corrected.16012013.xml")

last_article_id = None
last_article_text = ""

for s in parser:
    article_id = docs.sentence_to_doc_id[s["sentence_id"]]

    if article_id != last_article_id:
        if last_article_id:
            logger.info(f"Inserting: {last_article_id} : {len(last_article_text)} chars")
            logger.debug(f"article text: {last_article_text}")

            doc2database(db, last_article_id, last_article_text)

        last_article_id = article_id
        last_article_text = ""

    def make_sentence(words):
        text = ""

        for word in words:
            if word == "(" or word == "``":
                text += word
                continue

            if word == "," or word == "." or word == "?" or word == ")" or word == ":" or word == "''" or word == ";" or word == "!":
                text = text[0:-1]

            text += word + " "

        return text


    sentence = "".join(make_sentence([x["word"] for x in s["words"]]))
    logger.debug(f"sentence: {s['sentence_id']} -> {sentence}")
    last_article_text = last_article_text + sentence + "\n"
