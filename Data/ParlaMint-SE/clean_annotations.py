from lxml import etree
from pathlib import Path
import argparse

def main(args):
    parser = etree.XMLParser(remove_blank_text=True)
    export_folder = Path("./export/xml_export.pretty/")
    for path in export_folder.glob("*.xml"):
        with path.open() as f:
            root = etree.parse(f, parser).getroot()
        newstem = path.stem.replace("_export", "")
        newpath = Path(".") / f"{newstem}.ana.xml"
        unannotated_path =  Path(".") / f"{newstem}.xml"
        with unannotated_path.open() as f:
            unnann_root = etree.parse(f, parser).getroot()

        texts = unnann_root.findall(f".//{args.tei_ns}text")
        assert len(texts) == 1
        text = texts[0]
        
        text.getparent().remove(text)
        
        texts = root.findall(f".//{args.tei_ns}text")
        assert len(texts) == 1
        text = texts[0]

        for body in text:
            for div in body:
                for elem in div:
                    if elem.tag == f"{args.tei_ns}u":
                        for seg in elem:
                            sentences = [[]]
                            for token in seg:
                                sentences[-1].append(token)
                                
                                # Create new sentence upon punctuation
                                if token.text in [".", "?", "!"]:
                                    sentences.append([])
                                token.getparent().remove(token)
                                
                            for sentence in sentences:
                                if len(sentence) == 0:
                                    continue
                                s = etree.SubElement(seg, "s")
                                for token in sentence:
                                    s.append(token)
                                    token.tag = f"{args.tei_ns}w"
                    elif elem.tag == f"{args.tei_ns}note":
                        print(elem, len(elem))
                        elemtext = []
                        for token in elem:
                            token.getparent().remove(token)
                            elemtext.append(token.text)
                            
                        elem.text = " ".join(elemtext)
                        print(elem, len(elem))
                        del elem.attrib[f"id"]
                            

        for w in text.findall(f".//{args.tei_ns}w"):
            w.attrib["lemma"] = w.attrib["baseform"]
            w.attrib["msd"] = "UPosTag=" + w.attrib["upos"] +  w.attrib["ufeats"]
            for attrib in list(w.attrib):
                if attrib not in ["lemma", "msd"]:
                    del w.attrib[attrib]
        tei = unnann_root
        tei.append(text)

        b = etree.tostring(
            unnann_root, pretty_print=True, encoding="utf-8", xml_declaration=True
        )

        with newpath.open("wb") as f:
            f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tei_ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()
    main(args)
