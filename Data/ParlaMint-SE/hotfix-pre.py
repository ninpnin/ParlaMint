"""
Make some hotfixes to the protocols before the SPARV annotation pipeline has been run.

These include:
1) Convert 'notes' starting with § into headers 2) Convert 'notes' containing "(Applåder)" into kinesic
"""
from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd
import progressbar
import numpy as np
import datetime

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def remove_u_frontmatter(root):
    for body in root.findall(f".//{tei_ns}body"):
        for div in root.findall(f".//{tei_ns}div"):
            for elem in div:
                # Only remove utterances up until the first speaker introduction
                if elem.tag == f"{tei_ns}note" and elem.attrib.get("type") == "speaker":
                    return root
                elif elem.tag == f"{tei_ns}u":
                    # 
                    for seg in elem:
                        seg.tag = f"{tei_ns}note"
                        parent = elem.getparent()
                        index = parent.index(elem)
                        parent.insert(index, seg)
                        #pass

                    parent = elem.getparent()
                    parent.remove(elem)

    return root

def merge_utterances(root):
    for body in root.findall(f".//{tei_ns}body"):
        for div in root.findall(f".//{tei_ns}div"):
            prev_elem = None
            prev_who = None
            for elem in div:
                if elem.tag == f"{tei_ns}u":
                    if prev_who == elem.attrib["who"]:
                        print(prev_elem, elem)
                        for seg in elem:
                            prev_elem.append(seg)
                        parent = elem.getparent()
                        parent.remove(elem)
                    else:
                        prev_elem = elem
                        prev_who = elem.attrib["who"]
                else:
                    prev_elem = None
                    prev_who = None

    return root


"""
<kinesic type="applause">
    <desc>(Applåder)</desc>
</kinesic>
"""
def convert_applause(root):
    for note in root.findall(f".//{tei_ns}note"):
        content = " ".join(note.text.split())
        if content == "(Applåder)":
            print("apploder")
            note.tag = f"{tei_ns}kinesic"
            note.text = None
            note.attrib["type"] = "applause"
            del note.attrib[f"{xml_ns}id"]
            desc = etree.SubElement(note, "desc")
            desc.text = content

    return root

def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)

    for path in progressbar.progressbar(list(p.glob("ParlaMint-SE_*.xml"))):
        if ".ana" in path.suffixes:
            continue

        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        root = merge_utterances(root)
        root = convert_applause(root)
        root = remove_u_frontmatter(root)

        # Write on disk
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        with path.open("wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata_path", type=str, default=None)
    args = parser.parse_args()
    main(args)
