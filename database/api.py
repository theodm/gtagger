import logging
import os

import dataset as dataset
from loguru import logger

from database.utils.dataset import result_iter_first


class Database:
    def __init__(self, db_file):
        self.db = dataset.connect(db_file)

        self.article_table = self.db["article"]
        self.sentence_table = self.db["sentence"]
        self.word_table = self.db["word"]
        self.word_classification_table = self.db["word_classification"]

        # DataSet legt die Tabellen automatisch an, wenn eine Zeile hinzugefügt wird.
        # Daher legen wir einen Datensatz an und löschen ihn direkt wieder, damit diese
        # Tabelle immer da ist.
        self.word_classification_table.upsert({
            "user_name": "DUMMY",
            "word_id": "DUMMY",
            "classification": "DUMMY",
        }, ["user_name", "word_id"])
        self.word_classification_table.delete(user_name="DUMMY", word_id="DUMMY")

    def begin(self):
        self.db.begin()

    def stats_for_user(self, user_name):
        result = self.db.query("""
        SELECT
            (SELECT COUNT(*) FROM word
                LEFT JOIN word_classification wc ON word.word_id = wc.word_id AND user_name = :user_name
                WHERE ((pos = 'NOUN' AND morph_gender = 'Masc') OR (tag IN ('PDS', 'PIS', 'PPER', 'PPOSS', 'PRELS', 'PWS') AND morph_gender = 'Masc' AND morph_number = 'Sing')))
            occurences,
            (SELECT COUNT(*) FROM word
                LEFT JOIN word_classification wc ON word.word_id = wc.word_id AND user_name = :user_name
                WHERE ((pos = 'NOUN' AND morph_gender = 'Masc') OR (tag IN ('PDS', 'PIS', 'PPER', 'PPOSS', 'PRELS', 'PWS') AND morph_gender = 'Masc' AND morph_number = 'Sing')) AND classification IS NOT NULL)
            occurences_tagged
        """, user_name=user_name)

        row = result_iter_first(result)

        return {
            "occurences": row["occurences"],
            "occurences_tagged": row["occurences_tagged"]
        }

    def find_classifications_for_article(self, article_id, user_name):
        logger.debug(f"[Database] Querying classification for user {user_name} and article {article_id}")

        qresult = self.db.query(
            """
                SELECT * FROM word_classification wc
                INNER JOIN word w on w.word_id = wc.word_id
                WHERE wc.user_name = :user_name AND article_id = :article_id;
            """, user_name=user_name, article_id=article_id
        )

        result = {}

        for r in qresult:
            result[r["word_id"]] = r

        return result

    def find_article_with_missing_classification(self, user_name):
        logger.debug(f"[Database] Querying next article with missing classification for user {user_name}")

        result = self.db.query(
            """
               SELECT DISTINCT article_id FROM word 
               LEFT JOIN word_classification wc ON word.word_id = wc.word_id AND user_name = :user_name 
               WHERE ((pos = 'NOUN' AND morph_gender = 'Masc') OR (tag IN ('PDS', 'PIS', 'PPER', 'PPOSS', 'PRELS', 'PWS') AND morph_gender = 'Masc' AND morph_number = 'Sing')) AND classification IS NULL 
               ORDER BY RANDOM() 
               LIMIT 1
            """, user_name=user_name
        )

        row = result_iter_first(result)
        article_id = row["article_id"] if row else None

        logger.debug(f"[Database] Found article: {article_id}")

        if article_id:
            sent_rows = self.sentence_table.find(article_id=article_id, order_by=["order"])

            sents = []
            for s in sent_rows:
                word_rows = self.word_table.find(sentence_id=s["sentence_id"], order_by=["order"])

                words = []
                for w in word_rows:
                    words.append(w)

                s["words"] = words

                sents.append(s)

            return {
                "article_id": article_id,
                "sentences": sents
            }

        return None

    def upsert_article(self, article):
        self.article_table.upsert(dict(article), ["article_id"])

        logger.debug(f"[Database] Upserted Article: {article}")

    def upsert_sentence(self, sentence):
        self.sentence_table.upsert(sentence, ["article_id", "sentence_id"])

        logger.debug(f"[Database] Upserted Sentence: {sentence}")

    def upsert_words(self, words):
        self.word_table.upsert_many(words, ["article_id", "sentence_id", "word_id"])

        logger.debug(f"[Database] Upserted Words: {words}")

    def commit(self):
        self.db.commit()
    #
    # def update_classification_auto_single(self, user_name, word):
    #     # Erstellt automatisch Klassifikationen, wenn der Eintrag
    #     # als niemals Personenbezeichnung klassifiziert wurde.
    #     logger.debug(f"Klassifikationen 'Niemals Personenbezeichnung' für Benutzer {user_name} und Wort {word} werden appliziert.")
    #
    #     result = self.db.query("""
    #     SELECT * FROM word w
    #     LEFT JOIN word_classification wc ON w.word_id = wc.word_id AND user_name = :user_name
    #     WHERE w.word = :word AND classification IS NULL
    #     """, user_name=user_name, word=word)
    #
    #     classifications = []
    #     for r in result:
    #         classifications.append({
    #             "user_name": user_name,
    #             "word_id": r["word_id"],
    #             "classification": "NIEMALS_PERSONENBEZEICHNUNG"
    #         })
    #
    #     self.word_classification_table.upsert_many(classifications, ["user_name", "word_id"])
    #     logger.debug(f"[Database] Upserted Classifications: {classifications}")
    #

    def update_classifications_auto(self, user_name):
        # Erstellt automatisch Klassifikationen, wenn ein Eintrag
        # als niemals Personenbezeichnung klassifiziert wurde.
        logger.debug("Klassifikationen 'Niemals Personenbezeichnung' werden appliziert")

        result = self.db.query("""
        SELECT *, word.word_id AS word_id FROM word
        LEFT JOIN word_classification c on word.word_id = c.word_id AND user_name = :user_name
        WHERE classification IS NULL AND word IN (
            SELECT word FROM word_classification wc
            INNER JOIN word w on w.word_id = wc.word_id
            WHERE user_name = :user_name AND wc.classification = 'NIEMALS_PERSONENBEZEICHNUNG'
        )""", user_name=user_name)

        classifications = []
        for r in result:
            classifications.append({
                "user_name": user_name,
                "word_id": r["word_id"],
                "classification": "NIEMALS_PERSONENBEZEICHNUNG"
            })

        self.word_classification_table.upsert_many(classifications, ["user_name", "word_id"])
        logger.debug(f"[Database] Upserted Classifications: {classifications}")

        pass

    def upsert_classification(self, new_classification):
        self.word_classification_table.upsert(new_classification, ["user_name", "word_id"])

        logger.debug(f"[Database] Upserted Classification: {new_classification}")


db_location = 'sqlite:///' + os.path.dirname(os.path.realpath(__file__)) + '/default_db.db'
logger.info(f"Database Location: {db_location}")
db = Database(db_location)