from lxml import etree
import argparse
from pathlib import Path
import datetime
import progressbar

tei_ns = "{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"
xi_ns = "{http://www.w3.org/2001/XInclude}"
parser = etree.XMLParser(remove_blank_text=True)

def find_links(root, args):
    folder = Path(args.path).parent
    root_id = root.attrib[f"{xml_ns}id"]   
    corpus_is_annotated = ".ana" in root_id
    
    print("Remove old links...")
    for xi in root.findall(f".//{xi_ns}include"):
        if "ParlaMint-SE_" in xi.attrib.get("href", ""):
            parent = xi.getparent()
            parent.remove(xi)
    
    print("Add links...")
    for p in sorted(folder.glob("ParlaMint-SE_*.xml")):
        file_is_annotated = ".ana" in p.suffixes
        if corpus_is_annotated == file_is_annotated:
            nsmap = {"xi": xi_ns.replace("{", "").replace("}", "")}
            include = etree.SubElement(root, f"{xi_ns}include", nsmap=nsmap)
            include.attrib["href"] = f"{p.stem}{p.suffix}"

    print("Write to original file with updated links...")
    root_bytes = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)
    with Path(args.path).open("wb") as f:
        f.write(root_bytes)

    print("Populate includes from individual protocol files...")
    for xi in progressbar.progressbar(list(root.findall(f".//{xi_ns}include"))):
        ref = xi.attrib["href"]
        print(ref)
        if "ParlaMint-SE_" in ref:
            continue
        with (folder / ref).open() as f:
            linked_root = etree.parse(f, parser).getroot()

        xi_parent = xi.getparent()
        if "taxonomy" in ref or "list" in ref:
            print(ref, linked_root)
            xi_parent.insert(xi_parent.index(xi) + 1, linked_root)
        xi_parent.remove(xi)
    teiHeaders = root.findall(f".//{tei_ns}teiHeader")
    assert len(teiHeaders) == 1
    teiHeader = teiHeaders[0]

    return root

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(args.path, parser).getroot()
    root = find_links(root, args)

    print("Write to outfile...")
    root_bytes = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)
    with Path(args.outpath).open("wb") as f:
        f.write(root_bytes)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument("--path", type=str, required=True)
    argparser.add_argument("--outpath", type=str, default="out.xml")
    args = argparser.parse_args()

    main(args)