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
import numpy as np
import datetime

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

def get_speaker_df(folder):
    p = Path(folder) / "speaker.csv"

    with p.open() as f:
        df = pd.read_csv(f)

    # Filter out nulls
    df = df.replace({np.nan: None})
    df["start"] = pd.to_datetime(df["start"]).dt.date

    # Filter to only have modern talmän
    df = df[df["start"] >= datetime.date(2013, 1, 1)]
    df["end"] = df["end"].replace({None: datetime.date(2026, 1, 1)})

    df["start"] = df["start"].astype(str)
    df["end"] = df["end"].astype(str)

    print(df)
    return df

def remove_unknowns(root):
    for u in root.findall(f".//{tei_ns}u"):
        if u.attrib.get("who") == "#unknown":
            del u.attrib["who"]
    return root

def main(args):
    # Add talmän as 'chair'
    talman = None
    if args.metadata_path is not None:
        print("Load metadata from", args.metadata_path)
        talman = get_speaker_df(args.metadata_path)

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

        if talman is not None:
            for u in root.findall(f".//{tei_ns}u"):
                who = u.attrib.get("who", "")[1:]
                #print(who)

                ctm = talman[talman["wiki_id"] == who]
                ctm = ctm[(ctm["start"] <= protocols_date) & (ctm["end"] >= protocols_date)]
                if len(ctm) >= 1:
                    #print(ctm)
                    print(talman)
                    print(protocols_date, who)
                    u.attrib["ana"] = "#chair"

        root = remove_unknowns(root)
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
