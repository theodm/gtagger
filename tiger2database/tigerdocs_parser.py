import csv
import sys

from loguru import logger


class TigerDocs:
    def __init__(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter="\t")

            logger.debug(f"[TigerDocs] Opened File: {file_path}")

            self.sentence_to_doc_id = {}
            for row in reader:
                self.sentence_to_doc_id['s' + row[1]] = row[0]

                logger.trace(f"[TigerDocs] Row: {row[1]} {row[0]}")

            logger.info(f"[TigerDocs] Read {len(self.sentence_to_doc_id)} lines from {file_path}.")
