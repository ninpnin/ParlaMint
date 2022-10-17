from lxml import etree
import argparse
from pathlib import Path

def main(args):
    print(args)
    parser = etree.XMLParser(remove_blank_text=True)

    root = etree.parse(args.path, parser).getroot()
    root = root.findall(f".//{args.ns}TEI")[0]

    protocol_id = None
    for div in root.findall(f".//{args.ns}div"):
        if div.attrib.get("type") == "preface":
            for head in div.findall(f".//{args.ns}head"):
                protocol_id = head.text

    for u in root.findall(f".//{args.ns}u"):
        # TODO: find chair or regular participant in the meeting
        u.attrib["ana"] = "#regular"
        print(u)

    protocol_no = protocol_id.split("prot-")[-1]
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
    args = parser.parse_args()

    main(args)