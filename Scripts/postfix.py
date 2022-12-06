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
    
    print("Populate includes from individual protocol files...")
    for xi in progressbar.progressbar(list(root.findall(f".//{xi_ns}include"))):
        ref = xi.attrib["href"]
        if "ParlaMint-SE_" in ref:
            if args.titles:
                prot_path = Path("Data/ParlaMint-SE") / ref
                prot_root = etree.parse(prot_path, parser).getroot()
                for title in prot_root.findall(f".//{tei_ns}title"):
                    if title.text is not None:
                        title.text = title.text.replace("ParlaMint SAMPLE]", "ParlaMint]")
                        title.text = title.text.replace("ParlaMint.ana SAMPLE]", "ParlaMint.ana]")

                prot_bytes = etree.tostring(prot_root, pretty_print=True, encoding="utf-8", xml_declaration=True)
                with prot_path.open("wb") as f:
                    f.write(prot_bytes)

            year = ref.replace("ParlaMint-SE_", "")[:4]
            ref = ref.split("/")[-1]
            print(ref)
            if args.linkfolders:
                ref = f"{year}/{ref}"
            xi.attrib["href"] = ref

    return root

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(args.path, parser).getroot()
    root = find_links(root, args)

    print("Write to outfile...")
    root_bytes = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)
    with Path(args.path).open("wb") as f:
        f.write(root_bytes)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument("--path", type=str, required=True)
    argparser.add_argument("--linkfolders", type=bool, default=False)
    argparser.add_argument("--titles", type=bool, default=False)
    args = argparser.parse_args()

    main(args)