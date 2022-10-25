from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd

def governments(root, gov_df, minister_df, xml_ns=None):
    gov_df_alt = gov_df[(gov_df["start"] < "2022-08-01") & (gov_df["start"] > "2016-01-01")]
    gov_df = gov_df[gov_df["end"] > "2015-01-01"]
    gov_df = pd.concat([gov_df,gov_df_alt])
    gov_df = gov_df.where(pd.notnull(gov_df), None)
    gov_df = gov_df.drop_duplicates("wikidata_item_id")
    gov_df = gov_df.sort_values("start")

    listOrg = root
    
    print(gov_df)
    org = etree.SubElement(listOrg, "org")
    org.attrib[f"{xml_ns}id"] = "GOV"
    org.attrib["role"] = "government"

    orgName = etree.SubElement(org, "orgName")
    orgName.text = "Sveriges regering"
    orgName.attrib[f"{xml_ns}lang"] = "sv"
    orgName.attrib["full"] = "yes"
    listEvent = etree.SubElement(org, "listEvent")
    for _, gov in gov_df.iterrows():
        event = etree.SubElement(listEvent, "event")
        event.attrib[f"{xml_ns}id"] = gov["wikidata_item_id"]
        event.attrib["from"] = gov["start"]
        if gov.get("end") is not None:
            event.attrib["to"] = gov["end"]
        label1 = etree.SubElement(event, "label")

        label1.text = gov["government"]

    return root

def parties(root, df):
    return root

def main(args):
    path = Path(args.metadata_db)
    party_df = pd.read_csv(path / "party_abbreviation.csv")
    gov_df = pd.read_csv(path / "government.csv")
    minister_df = pd.read_csv(path / "minister.csv")
    people_df = pd.read_csv(path / "person.csv")
    mp_df = pd.read_csv(path / "member_of_parliament.csv")
    people_df = people_df.merge(mp_df, on="wiki_id", how="left")
    print(people_df)

    # Populate root with basic elements
    nsmap = {None: args.tei_ns.replace("{", "").replace("}", "")}
    root = etree.Element("listOrg", nsmap=nsmap)
    listOrg = root
    org = etree.SubElement(listOrg, "org") # Stats on the parliament
    org.attrib[f"{args.xml_ns}id"] = "Riksdagen"
    org.attrib["role"] = "parliament"
    org.attrib["ana"] = "#parla.uni #parla.national"
    orgName = etree.SubElement(org, "orgName") # Name
    orgName.attrib["full"] = "yes"
    orgName.attrib[f"{args.xml_ns}lang"] = "sv"
    orgName.text = "Sveriges riksdag"
    orgName = etree.SubElement(org, "orgName") # Name
    orgName.text = "Riksdagen"
    orgName.attrib["full"] = "abb"
    orgName.attrib[f"{args.xml_ns}lang"] = "sv"
    listEvent = etree.SubElement(org, "listEvent") # Sessions
    mandate_periods = [("2014-09-29","2018-09-24"), ("2018-09-24", "2018-09-11")]
    for start, end in mandate_periods:
        event = etree.SubElement(listEvent, "event") # Sessions
        event.attrib["from"] = start
        event.attrib["to"] = end
        label = etree.SubElement(event, "label")
        label.text = "Riksdagen {start} - {end}"

    # Populate with metadata
    root = governments(root, gov_df, minister_df, xml_ns=args.xml_ns)
    root = parties(root, party_df)

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    with open("ParlaMint-SE-listOrg.xml", "wb") as f:
        f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata_db", type=str)
    parser.add_argument("--tei_ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()
    main(args)
