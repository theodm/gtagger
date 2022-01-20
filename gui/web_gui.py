from datetime import datetime
from random import random

import eel as eel

from database.api import Database, db

eel.init("web")

classifications = {
    "KeinePersonenbezeichnung": {
        "text": "Vorkommen ist keine Personenbezeichnung und kann es in der Regel auch nicht sein.",
        "color": "",

    },

    "ImKonkretenFallKeinePersonenbezeichnung": {
        "text": "Vorkommen kann Personenbezeichnung sein. Im konkreten Fall bezieht sich das Vorkommen jedoch auf "
                "eine Nicht-Person oder einen Nicht-Personenkreis. (z.B. Das iPhone ist im Alltag ein großer *Helfer*.)"
    },

    "NiemalsPersonenbezeichnung": {
        "text": "Vorkommen ist nach dem Wortlaut her niemals eine Personenbezeichnung."
    },

    "PersonenbezeichnungMitSicheremBezug": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist nicht korrekturbedürftig, da es sich sicher auf "
                "eine männliche Person oder einen männlichen Personenkreis bezieht."
    },
    "PersonenbezeichnungMitWahrscheinlichemBezug": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist nicht korrekturbedürftig, da es sich "
                "wahrscheinlich auf "
                "eine männliche Person oder einen männlichen Personenkreis bezieht."

    },
    "PersonenbezeichnungMitBezugWortGeschlechtslos": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist nicht korrekturbedürftig, da es sich "
                "wahrscheinlich "
                "auf eine männliche Person oder einen männlichen Personenkreis bezieht. Das Wort selbst wird "
                "jedoch selbst auch in der Regel nicht gegendert. (Bsp.: Hans ist ein *Mensch*.)"
    },

    "PersonenbezeichnungBereitsNeutral": {
        "text": "Vorkommen ist Personenbezeichnung. Im konkreten Kontext wird jedoch auch bereits die gegenderte Form"
                "verwendet. Ein Korrekturbedarf besteht nicht."
    },

    "PersonenbezeichnungWahrscheinlichAbstrahierend": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist korrekturbedürftig, da es sich wahrscheinlich auf "
                "einen unbestimmten oder verschiedengeschlechtlichen Personenkreis bezieht."


    },
    "PersonenbezeichnungSicherAbstrahierend": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist korrekturbedürftig, da es sich sicher auf "
                "einen unbestimmten oder verschiedengeschlechtlichen Personenkreis bezieht."

    },
    "PersonenbezeichnungAbstrahierendWortGeschlechtslos": {
        "text": "Vorkommen ist Personenbezeichnung. Das Vorkommen ist grundsätzlich korrekturbedürftig, da es sich sicher auf "
                "einen unbestimmten oder verschiedengeschlechtlichen Personenkreis bezieht. Jedoch wird das Wort selbst"
                " in der Regel nicht gegendert."
    },

    "ZurzeitNichtBestimmbar": {


    }
}

class Tester:
    def __init__(self, db: Database, user_name):
        self.user_name = user_name
        self.db = db

        self._reload()

    def _current_word(self):
        for s in self.current_article["sentences"]:
            for w in s["words"]:
                # Nicht zu klassifizieren.
                if not ((w["pos"] == "NOUN" and w["morph_gender"] == "Masc") or (w["tag"] in ["PDS", "PIS", "PPER", "PPOSS", "PRELS", "PWS"] and w["morph_gender"] == "Masc" and w["morph_number"] == "Sing")):
                    continue

                # Bereits klassifiziert.
                if w["word_id"] in self.current_classifications:
                    continue

                return w["word_id"]
        return None

    def get_text_as_html(self):
        current_word = self._current_word()

        html = '<div class="text-sm">'

        for s in self.current_article["sentences"]:
            for w in s["words"]:
                classes = []

                if w["word_id"] == current_word:
                    classes.append("underline")

                if w["word_id"] in self.current_classifications:
                    classification = self.current_classifications[w["word_id"]]["classification"]

                    classification_map = {
                        "KEINE_PERSONENBEZEICHNUNG": "bg-slate-400",
                        "NIEMALS_PERSONENBEZEICHNUNG": "bg-slate-600",
                        "PERSONENBEZEICHNUNG_SICHER_KEINE_ABSTRAHIERENDE_VERWENDUNG": "bg-blue-600",
                        "PERSONENBEZEICHNUNG_WAHRSCHEINLICH_KEINE_ABSTRAHIERENDE_VERWENDUNG": "bg-blue-400",
                        "PERSONENBEZEICHNUNG_KEINE_ABSTRAHIERENDE_VERWENDUNG_OHNE_KORREKTURBEDARF": "bg-stone-400",
                        "PERSONENBEZEICHNUNG_BEREITS_NEUTRAL": "bg-green-400",
                        "PERSONENBEZEICHNUNG_WAHRSCHEINLICH_ABSTRAHIEREND": "bg-red-400",
                        "PERSONENBEZEICHNUNG_ABSTRAHIEREND": "bg-red-600",
                        "PERSONENBEZEICHNUNG_ABSTRAHIEREND_OHNE_KORREKTURBEDARF": "bg-stone-400",
                        "NICHT_BESTIMMBAR": "bg-stone-600"
                    }



                    classes.append(classification_map[classification])

                if classes:
                    html += '<div class="inline ' + (" ".join(classes)) + '">'

                html += w["word"]

                if classes:
                    html += '</div>'

                html += w["whitespace"]

            html += "<br>"

        html += '</div>'

        return html

    def get_stats(self):
        return self.db.stats_for_user(self.user_name)

    def _reload(self):
        self.db.update_classifications_auto(self.user_name)
        self.current_article = self.db.find_article_with_missing_classification(self.user_name)
        self.current_classifications = self.db.find_classifications_for_article(self.current_article["article_id"],
                                                                                self.user_name)

    def classificate(self, classification):
        current_word_id = self._current_word()

        new_classification = {
            "user_name": self.user_name,
            "word_id": current_word_id,
            "classification": classification
        }

        self.current_classifications[current_word_id] = new_classification
        self.db.upsert_classification(new_classification)

        if self._current_word() is None:
            # Es gibt kein zu klassifizierendes Wort mehr. Neuen Artikel laden.
            self._reload()

tester = Tester(db, "THEO")

@eel.expose
def next_occurence():
    stats = tester.get_stats()

    return {
        "text_html": tester.get_text_as_html(),
        "occurences": stats["occurences"],
        "occurences_tagged": stats["occurences_tagged"]
    }


@eel.expose
def classificate(classification):
    tester.classificate(classification)
    return

eel.start('index.html')
