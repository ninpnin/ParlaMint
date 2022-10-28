from lxml import etree
from pathlib import Path
import argparse
import uuid
import base58
import pandas as pd

tei_ns ="{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

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

def parties(root, party_df, party_aff_df, relevant_people):
    print("parties:")
    party_aff_df = party_aff_df.merge(relevant_people[["wiki_id"]], on="wiki_id", how="inner")
    party_aff_df = party_aff_df.drop_duplicates(["party_id", "party"])
    party_aff_df = party_aff_df.merge(party_df, on="party", how="left")
    party_aff_df = party_aff_df.where(pd.notnull(party_aff_df), None)
    party_aff_df = party_aff_df.sort_values("party")
    print(party_aff_df)

    for _, row in party_aff_df.iterrows():
        org = etree.SubElement(root, "org")
        org.attrib[f"{xml_ns}id"] = row["party_id"]
        org.attrib["role"] = "parliamentaryGroup"
        orgName = etree.SubElement(org, "orgName")
        orgName.text = row["party"]
        orgName.attrib["full"] = "yes"
        orgName.attrib[f"{xml_ns}lang"] = "sv"
        if row.get("abbreviation") is not None:
            orgName = etree.SubElement(org, "orgName")
            orgName.text = row["abbreviation"]
            orgName.attrib["full"] = "abb"
            orgName.attrib[f"{xml_ns}lang"] = "sv"

    return root

def get_relevant_people(person_df, mp_df, minister_df):
    relevant_people = []
    for df, role in zip([mp_df, minister_df], ["mp", "minister"]):
        df_alt = df[df["start"] >= "2015-01-01"]
        df = df[df["end"] >= "2015-01-01"]
        wiki_ids = list(set(df["wiki_id"]))
        rows = [[wid, role] for wid in wiki_ids]
        df = pd.DataFrame(rows, columns=["wiki_id", "relevancy"])
        relevant_people.append(df)

    relevant_people = pd.concat(relevant_people)

    unknown = ['unknown', '2014-09-29', '2022-08-01', None, None, 'mp']
    mp_df.loc[len(mp_df.index)] = unknown
    mp_df = mp_df.drop_duplicates(["wiki_id", "start", "end"])

    relevant_people = relevant_people.merge(person_df, on="wiki_id")
    relevant_people.loc[len(relevant_people.index)] = ['unknown', 'unknown', None, None, 'gender', None, None, 'unknown mp', 'unknown mp']
    relevant_people["lastname"] = relevant_people["name"].str.split().str[-1]
    relevant_people = relevant_people.sort_values(["lastname", "name"])
    relevant_people = relevant_people.drop_duplicates("wiki_id")
    return relevant_people

def people(root, person_df, mp_df, minister_df, party_aff_df, relevant_people):

    for _, row in relevant_people.iterrows():
        person = etree.SubElement(root, "person")
        person.attrib[f"{xml_ns}id"] = row.get("wiki_id")
        persName = etree.SubElement(person, "persName")
        surname = etree.SubElement(persName, "surname")
        surname.text = row["name"].split()[-1]
        forename = etree.SubElement(persName, "forename")
        forename.text = " ".join(row["name"].split()[:-1])
        if row.get("gender") is not None:
            sex = etree.SubElement(person, "sex")
            sex.attrib["value"] = "unknown"
            if row.get("gender") == "man":
                sex.attrib["value"] = "M"
            elif row.get("gender") == "woman":
                sex.attrib["value"] = "F"

        # Terms in office
        riksdagen_periods = set()
        for _, row_prime in mp_df[mp_df["wiki_id"] == row["wiki_id"]].sort_values(["wiki_id", "start"]).iterrows():
            end_date = row_prime.get("end", "2024-01-01")
            if end_date is not None and end_date < "2015-01-01":
                continue
            party = row_prime["party"]
            start = row_prime.get("start")
            end = row_prime.get("end")

            # Do not add overlapping periods
            start_date = row_prime.get("start", "2014-01-01")
            if start_date is None:
                start_date = "2014-01-01"
            if end_date is None:
                end_date = "2024-01-01"

            skip = False
            for start_prime, end_prime in list(riksdagen_periods):
                if start_prime <= start_date and end_prime >= end_date:
                    skip = True
                    
            if skip:
                continue
            riksdagen_periods.add((start_date,end_date))
            affiliation = etree.SubElement(person, "affiliation")
            affiliation.attrib["role"] = "member"
            affiliation.attrib["ref"] = "#Riksdagen"
            affiliation.attrib["from"] = start
            if end is not None:
                affiliation.attrib["to"] = end

        # Party affiliations
        for _, row_prime in party_aff_df[party_aff_df["wiki_id"] == row["wiki_id"]].iterrows():
            end_date = row_prime.get("end", "2024-01-01")
            party_id = row_prime.get("party_id")
            if end_date is not None and end_date < "2015-01-01":
                continue
            if row_prime.get("party_id") is None:
                continue

            start = row_prime.get("start")
            end = row_prime.get("end")
            role = row_prime.get("role")
            affiliation = etree.SubElement(person, "affiliation")
            affiliation.attrib["role"] = "member"
            affiliation.attrib["ref"] = f"#{row_prime['party_id']}"
            if start is not None:
                affiliation.attrib["from"] = start
            if end is not None:
                affiliation.attrib["to"] = end


        # Minister affiliations
        minister_df = minister_df.drop_duplicates(["wiki_id", "role", "start", "end"])
        government_periods = set()
        for _, row_prime in minister_df[minister_df["wiki_id"] == row["wiki_id"]].iterrows():
            start = row_prime.get("start")
            end_date = row_prime.get("end", "2024-01-01")
            if end_date is not None and end_date < "2015-01-01":
                continue

            for affiliationtype in ["member", "minister"]:
                start_date = row_prime.get("start", "2014-01-01")
                if start_date is None:
                    start_date = "2014-01-01"
                if end_date is None:
                    end_date = "2024-01-01"

                if affiliationtype == "member":
                    # Only add 'member' of government once even if
                    # there are multiple minister positions for this period
                    for start_prime, end_prime in list(government_periods):
                        if start_prime <= start_date and end_prime >= end_date:
                            continue
                else:
                    government_periods.add((start_date,end_date))
                if start is None or start < "2015-01-01":
                    continue
                end = row_prime.get("end")
                role = row_prime.get("role")
                affiliation = etree.SubElement(person, "affiliation")
                affiliation.attrib["role"] = affiliationtype
                affiliation.attrib["ref"] = "#GOV"
                affiliation.attrib["from"] = start
                if end is not None:
                    affiliation.attrib["to"] = end
                if affiliationtype != "member" or role is not None:
                    roleName = etree.SubElement(affiliation, "roleName")
                    roleName.attrib[f"{xml_ns}lang"] = "sv"
                    roleName.text = role.strip()

    return root

def listorg(args):
    path = Path(args.metadata_db)
    party_df = pd.read_csv(path / "party_abbreviation.csv")
    party_aff_df = pd.read_csv(path / "party_affiliation.csv")
    gov_df = pd.read_csv(path / "government.csv")
    minister_df = pd.read_csv(path / "minister.csv")
    minister_df = minister_df.where(pd.notnull(minister_df), None)
    people_df = pd.read_csv(path / "person.csv")
    people_df = people_df.where(pd.notnull(people_df), None)
    mp_df = pd.read_csv(path / "member_of_parliament.csv")
    mp_df = mp_df.where(pd.notnull(mp_df), None)
    name_df = pd.read_csv(path / "name.csv")
    name_df = name_df[name_df["primary_name"] == True]
    people_df = people_df.merge(name_df, on="wiki_id", how="left")
    relevant_people = get_relevant_people(people_df, mp_df, minister_df)

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
    root = parties(root, party_df, party_aff_df, relevant_people)

    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    with open("SE-listOrg.xml", "wb") as f:
        f.write(b)

def listperson(args):
    path = Path(args.metadata_db)
    party_aff_df = pd.read_csv(path / "party_affiliation.csv")
    party_aff_df = party_aff_df.where(pd.notnull(party_aff_df), None)
    gov_df = pd.read_csv(path / "government.csv")
    minister_df = pd.read_csv(path / "minister.csv")
    minister_df = minister_df.where(pd.notnull(minister_df), None)
    people_df = pd.read_csv(path / "person.csv")
    people_df = people_df.where(pd.notnull(people_df), None)
    mp_df = pd.read_csv(path / "member_of_parliament.csv")
    mp_df = mp_df.where(pd.notnull(mp_df), None)
    name_df = pd.read_csv(path / "name.csv")
    name_df = name_df[name_df["primary_name"] == True]
    people_df = people_df.merge(name_df, on="wiki_id", how="left")
    relevant_people = get_relevant_people(people_df, mp_df, minister_df)
    print(people_df)

    # Populate root with basic elements
    nsmap = {None: args.tei_ns.replace("{", "").replace("}", "")}
    root = etree.Element("listPerson", nsmap=nsmap)
    listPerson = root
    head = etree.SubElement(listPerson, "head")
    head.text = "List of speakers"

    # Populate with metadata
    root = people(root, people_df, mp_df, minister_df, party_aff_df, relevant_people)

    # Write to disk
    b = etree.tostring(
        root, pretty_print=True, encoding="utf-8", xml_declaration=True
    )
    with open("SE-listPerson.xml", "wb") as f:
        f.write(b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata_db", type=str)
    parser.add_argument("--tei_ns", type=str, default="{http://www.tei-c.org/ns/1.0}")
    parser.add_argument("--xml_ns", type=str, default="{http://www.w3.org/XML/1998/namespace}")
    args = parser.parse_args()
    listorg(args)
    listperson(args)
