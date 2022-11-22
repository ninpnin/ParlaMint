"""
1) Update word and speech counts in the corpus files (ParlaMint-SE.xml and ParlaMint-SE.ana.xml).
2) Generate <setting> 'from' and 'to' attributes from protocol dates on the corpus level
"""
from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def setting_dates(root, dates):
    start = min(dates)
    end = max(dates)

    # TODO: set
    print(start, end)

    settingDescs = root.findall(f".//{tei_ns}settingDesc")
    assert len(settingDescs) == 1
    settingDesc = settingDescs[0]
    for date in settingDesc.findall(f".//{tei_ns}date"):
        date.attrib["from"] = start
        date.attrib["to"] = end
        date.text = f"{start} - {end}"

    return root

def main(args):
    p = Path(".")
    parser = etree.XMLParser(remove_blank_text=True)

    rows = []
    all_dates = set()
    for path in p.glob("ParlaMint-SE_*.xml"):
        # Skip .ana files
        if ".ana" in path.suffixes:
            continue

        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        wds = 0
        for elem in root.findall(f".//{tei_ns}u"):
            t = " ".join(elem.itertext())
            wds += len(t.split())

        notes = root.findall(f".//{tei_ns}note")
        intros = [note for note in notes if note.attrib.get("type") == "speaker"]
        speeches = len(intros)

        rows.append([wds, speeches, path.stem])

        # Get protocol dates
        settingDescs = root.findall(f".//{tei_ns}settingDesc")
        assert len(settingDescs) == 1
        settingDesc = settingDescs[0]
        for date in settingDesc.findall(f".//{tei_ns}date"):
            all_dates.add(date.attrib["when"])

    df = pd.DataFrame(rows, columns=["wds", "speeches", "protocol"])
    total_words, total_speeches = sum(df["wds"]), sum(df["speeches"])

    print(df)
    print(f"Total words: {total_words}, total speeches: {total_speeches}")

    # Write to 'extent' element in the corpus files
    for path in p.glob("ParlaMint-SE.*"):
        with path.open() as f:
            root = etree.parse(f, parser).getroot()

        fileDescs = root.findall(f".//{tei_ns}fileDesc")
        assert len(fileDescs) == 1
        fileDesc = fileDescs[0]

        extents = fileDesc.findall(f".//{tei_ns}extent")
        if len(extents) > 0:
            for extent in extents:
                parent = extent.getparent()
                parent.remove(extent)

        editionStmts = fileDesc.findall(f".//{tei_ns}editionStmt")
        assert len(editionStmts) == 1
        editionStmt = editionStmts[0]

        extent = etree.Element("extent")
        parent = editionStmt.getparent()
        parent.insert(parent.index(editionStmt)+1, extent)

        # Speeches, en
        measure = etree.SubElement(extent, "measure")
        measure.attrib[f"{xml_ns}lang"] = "en"
        measure.attrib["unit"] = "speeches"
        measure.attrib["quantity"] = f"{total_speeches}"
        measure.text = f"{total_speeches} speeches"

        # Speeches, sv
        measure = etree.SubElement(extent, "measure")
        measure.attrib[f"{xml_ns}lang"] = "sv"
        measure.attrib["unit"] = "speeches"
        measure.attrib["quantity"] = f"{total_speeches}"
        measure.text = f"{total_speeches} tal"

        # Words, en
        measure = etree.SubElement(extent, "measure")
        measure.attrib[f"{xml_ns}lang"] = "en"
        measure.attrib["unit"] = "words"
        measure.attrib["quantity"] = f"{total_words}"
        measure.text = f"{total_words} words"

        # Words, sv
        measure = etree.SubElement(extent, "measure")
        measure.attrib[f"{xml_ns}lang"] = "sv"
        measure.attrib["unit"] = "words"
        measure.attrib["quantity"] = f"{total_words}"
        measure.text = f"{total_words} ord"

        root = setting_dates(root, all_dates)
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
