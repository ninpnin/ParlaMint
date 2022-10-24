from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd

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
                                    # Wrap named entities in a 'name' element
                                    if token.attrib.get("pos") == "PM":
                                        name = etree.SubElement(s, "name")
                                        name.append(token)
                                    # Other words are included directly
                                    else:
                                        s.append(token)
                                    token.tag = f"{args.tei_ns}w"
                                s = etree.SubElement(s, f"{args.tei_ns}linkGrp")
                    elif elem.tag == f"{args.tei_ns}note":
                        print(elem, len(elem))
                        elemtext = []
                        for token in elem:
                            token.getparent().remove(token)
                            elemtext.append(token.text)
                            
                        elem.text = " ".join(elemtext)
                        print(elem, len(elem))
                        del elem.attrib[f"id"]
        
        # Add IDs for 'w' elements
        for w in text.findall(f".//{args.tei_ns}w"):
            w.attrib["lemma"] = w.attrib["baseform"]
            w.attrib["msd"] = "UPosTag=" + w.attrib["upos"] +  w.attrib["ufeats"]
            w_id = uuid.uuid1()
            w_id = base58.b58encode(w_id.bytes).decode("utf-8")
            w_id = f"i-{w_id}"
            w.attrib[f"{args.xml_ns}id"] = w_id

        # Format dependency parsing
        mambda_to_ud = pd.read_csv("mamba_ud.csv", na_filter = False)
        mambda_to_ud = {m: ud for m, ud, in zip(mambda_to_ud["mamba"], mambda_to_ud["ud"])}
        print(mambda_to_ud)
        for linkGrp in list(text.findall(f".//{args.tei_ns}linkGrp")):
            linkGrp.attrib[f"targFunc"] = "head argument"
            linkGrp.attrib[f"type"] = "UD-SYN"

            s = linkGrp.getparent()
            w_ids = {w.attrib["ref"]: w.attrib[f"{args.xml_ns}id"] for w in s.findall(f".//{args.tei_ns}w")}

            for w in s.findall(f".//{args.tei_ns}w"):
                dephead_ref = w.attrib.get("dephead_ref")
                deprel = w.attrib.get("deprel")
                this_id = w.attrib[f"{args.xml_ns}id"]
                other_id = w_ids.get(dephead_ref)
                if dephead_ref is not None and deprel is not None and other_id is not None:
                    deprel_str = mambda_to_ud.get(deprel)
                    if deprel_str is None:
                        deprel_str =  mambda_to_ud.get(f"*{deprel[1:]}")
                    if deprel_str is None:
                        deprel_str =  mambda_to_ud.get(f"{deprel[:1]}*")
                    if deprel_str is None:
                        #print(f"{deprel} not found in mapping")
                        continue
                    link = etree.SubElement(linkGrp, "link")
                    link.attrib["ana"] = "ud-syn:" + deprel_str
                    link.attrib["target"] = f"#{this_id} #{other_id}"

        
        # Delete unnecessary arguments in 'w' elements
        for w in text.findall(f".//{args.tei_ns}w"):
            for attrib in list(w.attrib):
                if attrib not in ["lemma", "msd", f"{args.xml_ns}id"]:
                    del w.attrib[attrib]

        # Convert punctuation from 'w' into 'pc'        
        for w in text.findall(f".//{args.tei_ns}w"):
            if "UPosTag=PUNCT" in w.attrib.get("msd", ""):
                w.tag = f"{args.tei_ns}pc"
                del w.attrib["lemma"]

        # Convert plain ids and TEI ids into XML ids
        for elem in list(text.findall(f".//{args.tei_ns}seg")) + list(text.findall(f".//{args.tei_ns}u")):
            elem_id = elem.attrib.get(f"{args.tei_ns}id")
            if elem_id is None:
                elem_id = elem.attrib.get("id")
                del elem.attrib["id"]
            else:
                del elem.attrib[f"{args.tei_ns}id"]
            if elem_id is not None:
                elem.attrib[f"{args.xml_ns}id"] = elem_id
    
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
