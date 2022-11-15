"""
Rename protocols so that they include the protocol date in their title and xml id.
"""
from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)

    for path in p.glob("ParlaMint-SE_*.xml"):
        if "prot" in path.stem:
            continue
        # Skip .ana files
        if ".ana" in path.suffixes:
            pass

        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        protocols_date = None
        for profileDesc in root.findall(f".//{tei_ns}profileDesc"):
            for date in profileDesc.findall(f".//{tei_ns}date"):
                protocols_date = date.attrib.get("when")

        newstem = path.stem.replace("ParlaMint-SE_", f"ParlaMint-SE_{protocols_date}-prot-")
        newpath = path.parents[0] / f"{newstem}{''.join(path.suffix)}"

        root.attrib[f"{xml_ns}id"] = newstem

        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )


        with newpath.open("wb") as f:
            f.write(b)

        if path.stem != newstem:
            print(path.stem, newstem)
            path.unlink()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tei_ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()
    main(args)
