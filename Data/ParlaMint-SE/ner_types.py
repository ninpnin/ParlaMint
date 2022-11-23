"""
Add NER types to predetected NER segments using KBs BERT NER tool
"""
from transformers import pipeline
from lxml import etree
from pathlib import Path
import argparse
import progressbar

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"


def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)
    ner_pipeline = pipeline('ner', model='KB/bert-base-swedish-cased-ner', tokenizer='KB/bert-base-swedish-cased-ner')

    for path in progressbar.progressbar(list(p.glob("ParlaMint-SE_*.ana.xml"))):
        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        bodies = root.findall(f".//{tei_ns}body")
        assert len(bodies) == 1
        body = bodies[0]

        for name in  progressbar.progressbar(list(body.findall(f".//{tei_ns}name"))):
            nametext = " ".join(name.itertext())
            results = ner_pipeline(nametext)
            ner_type = "MISC"
            if len(results) >= 1:
                d = results[0]
                if d["entity"] in ["PER", "LOC", "ORG"]:
                    ner_type = d["entity"]

            name.attrib["type"] = ner_type

        b = etree.tostring( 
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        with path.open("wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    main(args)
