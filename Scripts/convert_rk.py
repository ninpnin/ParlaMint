from lxml import etree
import argparse
from pathlib import Path
import datetime

def main(args):
    print(args)
    todays_date = datetime.date.today().strftime("%Y-%m-%d")
    print(f"NOW {todays_date}")
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
    session = protocol_no.split("-")[0]
    session_str = f"{session[:4]}/{session[4:]}"
    protocol_no = protocol_no.split("--")[-1]

    # Find protocol date
    protocols_date = None
    for docDate in root.findall(f".//{args.ns}docDate"):
        protocols_date = docDate.attrib["when"]

    # Find number of introductions
    intros = [note for note in root.findall(f".//{args.ns}note") if note.attrib.get("type") == "speaker"]
    no_of_speeches = len(intros)

    ## ADUST TO SCHEMA ##
    ## HEADER
    # Add language, ID and tags
    root.attrib[f"{args.xml_ns}lang"] = "sv"
    root.attrib[f"{args.xml_ns}id"] = f"ParlaMint-SE_{session}--{protocol_no}-commons"
    if protocols_date >= "2020-01-01":
        root.attrib["ana"] = "#parla.sitting #covid"
    else:
        root.attrib["ana"] = "#parla.sitting #reference"

    # Fix 'title' content, add type
    for title in root.findall(f".//{args.ns}title"):
        title.attrib["type"] = "main"
        title.text = f"Riksdagens protokoll {session_str} nr. {protocol_no}"

    # Remove all 'authority' sections
    for authority in root.findall(f".//{args.ns}authority"):
        authority.getparent().remove(authority)

    # Remove all 'editorialDecl' sections
    for editorialDecl in root.findall(f".//{args.ns}editorialDecl"):
        editorialDecl.getparent().remove(editorialDecl)

    # Add 'meeting' section
    # <meeting ana="#parla.term #parla.lower #parliament.PSP7" n="ps2013">ps2013</meeting>
    for titleStmt in root.findall(f".//{args.ns}titleStmt"):
        title = titleStmt.findall(f".//{args.ns}title")[-1]
        meeting = etree.Element("meeting")
        meeting.text = session_str
        meeting.attrib["n"] = session
        meeting.attrib["ana"] = "#parla.uni #parla.term"
        titleStmt.insert(titleStmt.index(title)+1, meeting)

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

    # Add 'publisher' to 'publicationStmt'
    publicationStmts = list(root.findall(f".//{args.ns}publicationStmt"))
    assert len(publicationStmts) == 1
    publicationStmt = publicationStmts[0]
    publisher = etree.SubElement(publicationStmt, "publisher")
    orgName = etree.SubElement(publisher, "orgName")
    orgName.attrib[f"{args.xml_ns}lang"] = "en"
    orgName.text = "CLARIN research infrastructure"
    ref = etree.SubElement(publisher, "ref")
    ref.attrib["target"] = "https://www.clarin.eu/"
    ref.text = "www.clarin.eu"

    # Add 'idno' to 'publicationStmt'
    idno = etree.SubElement(publicationStmt, "idno")
    idno.text = "https://github.com/clarin-eric/ParlaMint"
    idno.attrib["type"] = "URI"

    # Add 'availability' to 'publicationStmt'
    availability = etree.SubElement(publicationStmt, "availability")
    availability.attrib["status"] = "free"
    licence = etree.SubElement(availability, "licence")
    licence.text = "http://creativecommons.org/licenses/by/4.0/"
    p = etree.XML('<p xml:lang="en">This work is licensed under the <ref target="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</ref>.</p>')
    availability.append(p)

    # Add 'date' to 'publicationStmt'
    date = etree.SubElement(publicationStmt, "date")
    date.text = todays_date
    date.attrib["when"] = todays_date

    # Add 'idno' to 'bibl'
    bibls = list(root.findall(f".//{args.ns}bibl"))
    assert len(bibls) == 1
    bibl = bibls[0]
    idno = date = etree.SubElement(bibl, "idno")
    idno.attrib["type"] = "URI"
    idno.attrib["subtype"] = "parliament"
    idno.text = "https://data.riksdagen.se/data/dokument/"
    idno = date = etree.SubElement(bibl, "idno")
    idno.attrib["type"] = "URI"
    idno.text = "https://github.com/welfare-state-analytics/riksdagen-corpus"

    project_desc_str = """<projectDesc>
        <p xml:lang="sv">
            <ref target="https://www.clarin.eu/content/parlamint">ParlaMint</ref>
        </p>
        <p xml:lang="en">
            <ref target="https://www.clarin.eu/content/parlamint">ParlaMint</ref> is a project that aims to (1) create a multilingual set of comparable corpora of parliamentary proceedings uniformly encoded according to the <ref target="https://github.com/clarin-eric/parla-clarin">Parla-CLARIN recommendations</ref> and covering the COVID-19 pandemic from November 2019 as well as the earlier period from 2015 to serve as a reference corpus; (2) process the corpora linguistically to add Universal Dependencies syntactic structures and Named Entity annotation; (3) make the corpora available through concordancers and Parlameter; and (4) build use cases in Political Sciences and Digital Humanities based on the corpus data.
        </p>
    </projectDesc>
    """
    project_desc = etree.XML(project_desc_str)
    encodingDescs = list(root.findall(f".//{args.ns}encodingDesc"))
    assert len(encodingDescs) == 1
    encodingDesc = encodingDescs[0]
    encodingDesc.insert(0, project_desc)

    # Add 'tagsDecl'
    text = root.findall(f".//{args.ns}text")[0]
    tagsDecl = etree.Element("tagsDecl")
    namespace = etree.SubElement(tagsDecl, "namespace")
    namespace.attrib["name"] = args.ns.replace("{", "").replace("}", "")
    for tag in ["text", "body", "div", "note", "pb", "u", "seg", "kinesic", "vocal", "incident", "gap", "desc", "time"]:
        tagUsage = etree.SubElement(namespace, "tagUsage")
        tagUsage.attrib["gi"] = tag
        tagUsage.attrib["occurs"] = str(len(text.findall(f".//{args.ns}{tag}")))
    encodingDesc.insert(encodingDesc.index(project_desc) + 1, tagsDecl)

    # Add 'profileDesc' 
    for encodingDesc in root.findall(f".//{args.ns}encodingDesc"):
        teiHeader = encodingDesc.getparent()
        profileDesc = etree.Element("profileDesc")
        settingDesc = etree.SubElement(profileDesc, "settingDesc")
        setting = etree.SubElement(settingDesc, "setting")
        name_org = etree.SubElement(setting, "name")
        name_org.attrib["type"] = "org"
        name_org.text = "Sveriges riksdag"
        name_address = etree.SubElement(setting, "name")
        name_address.attrib["type"] = "address"
        name_address.text = "Riksgatan 1"
        name_city = etree.SubElement(setting, "name")
        name_city.attrib["type"] = "city"
        name_city.text = "Stockholm"
        name_country = etree.SubElement(setting, "name")
        name_country.attrib["type"] = "country"
        name_country.text = "Sweden"
        name_country = etree.SubElement(setting, "date")
        name_country.attrib["when"] = protocols_date
        name_country.attrib["ana"] = "#parla.sitting"
        name_country.text = protocols_date

        teiHeader.insert(teiHeader.index(encodingDesc)+1, profileDesc)

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
        if protocols_date >= "2020-01-01":
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

    filename = f"ParlaMint-SE_{session}--{protocol_no}-commons.xml"
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