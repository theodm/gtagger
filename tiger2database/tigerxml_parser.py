from lxml import etree as ET
from loguru import logger


class TigerXMLParser:
    def __init__(self, file_path):
        self.iterator = ET.iterparse(file_path, events=("end",), tag=f"s")

        logger.debug(f"[TigerXMLParser] Opened file: {file_path}")

    def __iter__(self):
        self.iterator.__iter__()
        return self

    def __next__(self):
        logger.trace("[TigerXMLParser] Next sentence queried...")

        event, s_tag = self.iterator.__next__()
        sentence_id = s_tag.attrib["id"]

        logger.trace(f"[TigerXMLParser] sentence id: {sentence_id}")

        graph_tag = s_tag.find(f"graph")
        graph_root = graph_tag.attrib["root"]

        logger.trace(f"[TigerXMLParser] root id: {sentence_id}")

        terminals_tag = graph_tag.find(f"terminals")
        nonterminals_tag = graph_tag.find(f"nonterminals")
        nt_tags = nonterminals_tag.findall(f"nt")
        t_tags = terminals_tag.findall(f"t")

        sentence = {}

        words = []
        for t_tag in t_tags:
            word = {
                "word_id": t_tag.attrib["id"],
                "word": t_tag.attrib["word"],
                "lemma": t_tag.attrib["lemma"],
                "pos": t_tag.attrib["pos"],
                "morph_number": t_tag.attrib["number"],
                "morph_gender": t_tag.attrib["gender"],
                "morph_case": t_tag.attrib["case"],
                "morph_person": t_tag.attrib["person"],
                "morph_degree": t_tag.attrib["degree"],
                "morph_tense": t_tag.attrib["tense"],
                "morph_mood": t_tag.attrib["mood"]
            }

            words.append(word)

        sentence["sentence_id"] = sentence_id
        sentence["graph_root"] = graph_root
        sentence["words"] = words

        logger.trace(f"[TigerXMLParser] sentence: {sentence}")

        return sentence

