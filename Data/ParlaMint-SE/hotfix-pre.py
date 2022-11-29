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
            introDetected = False
            for elem in div:
                # Only remove utterances up until the first speaker introduction
                if introDetected:
                    pass
                elif elem.tag == f"{tei_ns}note" and elem.attrib.get("type") == "speaker":
                    introDetected = True
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
                print(elem)
                if elem.tag == f"{tei_ns}u":
                    if "next" in elem.attrib:
                        del elem.attrib["next"]
                    if "prev" in elem.attrib:
                        del elem.attrib["prev"]
                    if prev_who == elem.attrib.get("who", "unknown"):
                        print(prev_elem, elem)
                        for seg in elem:
                            prev_elem.append(seg)
                        parent = elem.getparent()
                        parent.remove(elem)
                    else:
                        prev_elem = elem
                        prev_who = elem.attrib.get("who")
                else:
                    prev_elem = None
                    prev_who = None

    return root

def convert_applause(root):
    for note in root.findall(f".//{tei_ns}note"):
        content = "".join(note.text.split())
        if content == "(Applåder)":
            print("apploder")
            note.tag = f"{tei_ns}kinesic"
            note.text = None
            note.attrib["type"] = "applause"
            del note.attrib[f"{xml_ns}id"]
            desc = etree.SubElement(note, "desc")
            desc.text = content

    return root

def convert_headers(root):
    headerStrs = set()
    for note in root.findall(f".//{tei_ns}note"):
        content = " ".join(note.text.split())
        if content[0] == "§" and content not in headerStrs:
            note.tag = f"{tei_ns}head"
            headerStrs.add(content)

    bodies = root.findall(f".//{tei_ns}body")
    assert len(bodies) == 1
    body = bodies[0]
    oldDiv = body[0]

    currentDiv = etree.SubElement(body, f"{tei_ns}div")
    firstDiv = currentDiv
    for elem in oldDiv:
        if elem.tag == f"{tei_ns}head":
            currentDiv = etree.SubElement(body, f"{tei_ns}div")
        currentDiv.append(elem)

        currentDiv.attrib["type"] = "debateSection"

    parent = oldDiv.getparent()
    parent.remove(oldDiv)

    if len(firstDiv) == 0:
        parent = firstDiv.getparent()
        parent.remove(firstDiv)

    for div in root.findall(f".//{tei_ns}div"):
        for elem in div[1:]:
            if elem.tag == f"{tei_ns}head":
                elem.tag = f"{tei_ns}note"

    return root

def _contains_toc_elem(root, toc_str="Innehållsförteckning"):
    notes = root.findall(f".//{tei_ns}note")
    notes = [note.text.strip() for note in notes]
    if toc_str in notes:
        return notes.index(toc_str)
    else:
        return None

def remove_toc(root):
    bodies = root.findall(f".//{tei_ns}body")
    assert len(bodies) == 1
    body = bodies[0]

    last_div = body[-1]
    
    if _contains_toc_elem(last_div) is not None:
        index = _contains_toc_elem(last_div)
        if index == 0:
            body.remove(last_div)
            return root
        else:
            for ix, subelem in enumerate(list(last_div)):
                if ix >= index:
                    last_div.remove(subelem)
    elif len(body) >= 2:
        penultimate_div = body[-2]
        index = _contains_toc_elem(penultimate_div)
        if index == 0:
            body.remove(penultimate_div)
            body.remove(last_div)
            return root
        elif index is not None and index >= 1:
            body.remove(last_div)
            for ix, subelem in enumerate(list(penultimate_div)):
                if ix >= index:
                    penultimate_div.remove(subelem)

    return root

def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)

    for path in progressbar.progressbar(list(p.glob("ParlaMint-SE_*.xml"))):
        if ".ana" in path.suffixes:
            continue

        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        if args.phase == 0:
            print("Phase 1")
            root = convert_headers(root)
            root = remove_u_frontmatter(root)
            root = convert_applause(root)
            root = merge_utterances(root)
        elif args.phase == 1:
            print("Phase 1")
            root = remove_toc(root)
        else:
            print("Phase not recognized")


        # Write on disk
        b = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        with path.open("wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata_path", type=str, default=None)
    parser.add_argument("--phase", type=int, default=0)
    args = parser.parse_args()
    main(args)
