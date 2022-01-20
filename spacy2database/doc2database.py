from _spacy.spacify import spacify
from database.api import db
from loguru import logger

def doc2database(db, doc_id, text):
    logger.debug(f"doc2database: {doc_id} : {text}")

    doc = spacify(text)

    sentences = []
    for sent_index, sent in enumerate(doc.sents):
        words = []
        for word in sent:
            def morph(str):
                return word.morph.get(str)[0] if word.morph and word.morph.get(str) and word.morph.get(str)[0] else None

            word = {
                "word_id": f"{doc_id}_{sent_index}_{word.i}",
                "word": word.text,
                "whitespace": word.whitespace_,
                "lemma": word.lemma_,
                "pos": word.pos_,
                "tag": word.tag_,

                "morph_number": morph("Number"),
                "morph_gender": morph("Gender"),
                "morph_case": morph("Case"),
                "morph_person": morph("Person"),
                "morph_degree": morph("Degree"),
                "morph_tense": morph("Tense"),
                "morph_mood": morph("Mood")
            }

            words.append(word)

        sentence = {
            "sentence_id": f"{doc_id}_{sent_index}",
            "graph_root": "??",
            "words": words
        }

        sentences.append(sentence)

    logger.debug(f"normal form: {doc_id} : {sentences}")

    # In Datenbankform bringen.
    db.begin()

    db.upsert_article({
        "article_id": doc_id
    })

    for sent_index, sent in enumerate(sentences):
        sentence = {
            "article_id": doc_id,
            "order": sent_index,
            "sentence_id": sent["sentence_id"],
            "graph_root": sent["graph_root"]
        }

        db.upsert_sentence(sentence)

        words = []
        for word_index, word in enumerate(sent["words"]):
            words.append({
                "article_id": doc_id,
                "sentence_id": sent["sentence_id"],
                "order": word_index,
                "word_id": word["word_id"],
                "word": word["word"],
                "whitespace": word["whitespace"],
                "lemma": word["lemma"],
                "pos": word["pos"],
                "tag": word["tag"],

                "morph_number": word["morph_number"],
                "morph_gender": word["morph_gender"],
                "morph_case": word["morph_case"],
                "morph_person": word["morph_person"],
                "morph_degree": word["morph_degree"],
                "morph_tense": word["morph_tense"],
                "morph_mood": word["morph_mood"]
            })

        db.upsert_words(words)

    db.commit()

    return sentences


