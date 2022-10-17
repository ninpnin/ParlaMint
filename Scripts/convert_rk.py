from lxml import etree
import argparse
from pathlib import Path

def main(args):
    print(args)
    parser = etree.XMLParser(remove_blank_text=True)

    root = etree.parse(args.path, parser).getroot()
    root = root.findall(f".//{args.ns}TEI")[0]

    ## EXTRACT DATA ##
    # Find protocol ID
    protocol_id = None
    for div in root.findall(f".//{args.ns}div"):
        if div.attrib.get("type") == "preface":
            for head in div.findall(f".//{args.ns}head"):
                protocol_id = head.text
    protocol_no = protocol_id.split("prot-")[-1]

    # Find protocol date
    date = None
    for docDate in root.findall(f".//{args.ns}docDate"):
        date = docDate.attrib["when"]

    # Find number of introductions
    intros = [note for note in root.findall(f".//{args.ns}note") if note.attrib.get("type") == "speaker"]
    no_of_speeches = len(intros)

    ## ADUST TO SCHEMA ##
    ## HEADER
    # Add language, ID and tags
    root.attrib[f"{args.xml_ns}lang"] = "sv"
    root.attrib[f"{args.xml_ns}id"] = f"ParlaMint-SE_{protocol_no}-commons"
    if date >= "2020-01-01":
        root.attrib["ana"] = "#parla.sitting #covid"
    else:
        root.attrib["ana"] = "#parla.sitting #reference"

    # Fix 'title' content, add type
    for title in root.findall(f".//{args.ns}title"):
        title.attrib["type"] = "main"
        title.text = f"Riksdagens protokoll {protocol_no}"

    # Remove all 'authority' sections
    for authority in root.findall(f".//{args.ns}authority"):
        authority.getparent().remove(authority)

    # Remove all 'editorialDecl' sections
    for editorialDecl in root.findall(f".//{args.ns}editorialDecl"):
        editorialDecl.getparent().remove(editorialDecl)

    # Add 'extent' section
    for editionStmt in root.findall(f".//{args.ns}editionStmt"):
        fileDesc = editionStmt.getparent()
        newelem = etree.Element("extent")
        measure = etree.SubElement(newelem, "measure")
        measure.attrib[f"{args.xml_ns}lang"] = "sv"
        measure.attrib["unit"] = "speeches"
        measure.attrib["quantity"] = f"{no_of_speeches}"
        measure.text = f"{no_of_speeches} tal"
        #<measure xml:lang="sv" unit="speeches" quantity="1">1 tal</measure>
        fileDesc.insert(fileDesc.index(editionStmt)+1, newelem)

    ## TEXT
    # Remove 'front' section from text
    for text in root.findall(f".//{args.ns}text"):
        for front in text.findall(f".//{args.ns}front"):
            front.getparent().remove(front)

    # Tag plaintext section divs with 'debateSection'
    for body in root.findall(f".//{args.ns}body"):
        for div in body.findall(f".//{args.ns}div"):
            div.attrib["type"] = "debateSection"

    # Mark whether we have covid or reference section
    for text in root.findall(f".//{args.ns}text"):
        if date >= "2020-01-01":
            text.attrib["ana"] = "#covid"
        else:
            text.attrib["ana"] = "#reference"

    # Format and annotate 'u'
    for u in root.findall(f".//{args.ns}u"):
        # Remove line breaks
        for seg in u:
            seg.text = " ".join(seg.text.split())
        # TODO: find chair or regular participant in the meeting
        u.attrib["ana"] = "#regular"

    # Format and annotate 'note'
    for note in root.findall(f".//{args.ns}note"):
        # Remove line breaks
        note.text = " ".join(note.text.split())

    filename = f"ParlaMint-SE_{protocol_no}-commons.xml"
    print(filename)

    # Write to file
    root_bytes = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)
    p = Path("data/ParlaMint-SE") / filename
    with p.open("wb") as f:
        f.write(root_bytes)
    #with 


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=str)
    parser.add_argument("--ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()

    main(args)