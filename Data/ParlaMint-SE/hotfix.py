"""
Make some hotfixes to the protocols after the whole pipeline has been run.

These include:
1) Add number of protocol as a <meeting ana="sitting"> element
"""
from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd
import progressbar

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)

    for path in progressbar.progressbar(list(p.glob("ParlaMint-SE_*.xml"))):

        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        protocols_date = None
        for profileDesc in root.findall(f".//{tei_ns}profileDesc"):
            for date in profileDesc.findall(f".//{tei_ns}date"):
                protocols_date = date.attrib.get("when")

        #ParlaMint-SE_2015-11-18-prot-201516--29.ana -> 29
        protocol_number = root.attrib[f"{xml_ns}id"].split(".")[0].split("--")[-1]

        titleStmts = root.findall(f".//{tei_ns}titleStmt")
        assert len(titleStmts) == 1
        titleStmt = titleStmts[0]

        meetings = titleStmt.findall(f".//{tei_ns}meeting")
        if len(meetings) == 1:
            term = meetings[0].attrib["n"]
            term_str = meetings[0].text
            meeting = etree.SubElement(titleStmt, "meeting")
            meeting.attrib["ana"] = "#parla.sitting #parla.uni"
            meeting.attrib["n"] = f"{term}--{protocol_number}"
            meeting.text = f"{term_str}--{protocol_number}"
        elif len(meetings) >= 2:
            pass
        else:
            print("ERORORR")
            return

        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )


        with path.open("wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tei_ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()
    main(args)
