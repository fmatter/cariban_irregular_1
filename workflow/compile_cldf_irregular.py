import os
import re
from pathlib import Path

import lingpy
import pandas as pd
import pybtex
import pycldf
from cldfbench import CLDFSpec
from cldfbench.cldf import CLDFWriter
from pycldf.sources import Source
from segments import Profile, Tokenizer
from writio import load

data_dir = Path("../data")
import logging

log = logging.getLogger("CLDF creation")
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

pd.set_option("display.max_rows", 500)
pd.options.mode.chained_assignment = None

log.info("Reading files")
lgs = load("../../../meta/raw/cariban_language_list.csv")
verb_stems = load(data_dir / "verb_stem_data.csv")
v_forms = load(data_dir / "inflection_data.csv")
v_forms = v_forms[v_forms["Inflection"].isin(["1"])]
v_forms.reset_index(inplace=True, drop=True)
bathe = load(data_dir / "bathe_data.csv")
cogsets = load(data_dir / "cognate_sets.csv")
examples = load(data_dir / "examples.csv")
lex_df = load(data_dir / "other_lexemes.csv")

log.info("Gathering meanings")
bathe["Meaning_ID"] = bathe["Transitivity"].apply(
    lambda x: "bathe_tr" if x == "TR" else "bathe_intr"
)

verb_meanings = (
    v_forms[["Meaning_ID"]]
    .append(verb_stems[["Meaning_ID"]])
    .append(bathe[["Meaning_ID"]])
)
verb_meanings.drop_duplicates(subset=["Meaning_ID"], inplace=True)
par_names = {"bathe_tr": "bathe.TR", "bathe_intr": "bathe.INTR"}
verb_meanings["Name"] = verb_meanings.apply(
    lambda x: par_names[x["Meaning_ID"]]
    if x["Meaning_ID"] in par_names
    else x["Meaning_ID"].replace("_", "."),
    axis=1,
)
id_desc = {"bathe_tr": "bathe (TR)", "bathe_intr": "bathe (INTR)"}
verb_meanings["Description"] = verb_meanings.apply(
    lambda x: id_desc[x["Meaning_ID"]]
    if x["Meaning_ID"] in id_desc
    else x["Name"].replace(".", " "),
    axis=1,
)
verb_meanings["Description"] = verb_meanings["Description"].apply(
    lambda x: "'to " + x + "'"
)
verb_meanings.rename(columns={"Meaning_ID": "ID"}, inplace=True)


par_desc = dict(zip(verb_meanings["ID"], verb_meanings["Description"]))

infl_desc = {"1": "First person form"}

v_forms["Parameter_ID"] = v_forms.apply(
    lambda x: x["Inflection"] + "_" + x["Meaning_ID"], axis=1
)
form_meanings = v_forms[["Parameter_ID", "Inflection", "Meaning_ID"]]
form_meanings["Description"] = form_meanings.apply(
    lambda x: infl_desc[x["Inflection"]] + " of " + par_desc[x["Meaning_ID"]], axis=1
)
form_meanings["Name"] = form_meanings.apply(
    lambda x: par_names[x["Meaning_ID"]]
    if x["Meaning_ID"] in par_names
    else x["Meaning_ID"].replace("_", "."),
    axis=1,
)
form_meanings["Name"] = form_meanings.apply(
    lambda x: x["Inflection"] + "-" + x["Name"], axis=1
)
form_meanings.rename(columns={"Parameter_ID": "ID"}, inplace=True)
form_meanings.drop_duplicates(subset=["ID"], inplace=True)

lex_meanings = lex_df[["Meaning"]]
lex_meanings["Name"] = lex_meanings["Meaning"].str.replace(" ", ".")
lex_meanings["Description"] = "'" + lex_meanings["Meaning"] + "'"
lex_meanings["ID"] = lex_meanings["Meaning"].str.replace(" ", "_")
lex_meanings.drop_duplicates(subset=["ID"], inplace=True)
lex_meanings = lex_meanings[~(lex_meanings["ID"].isin(verb_meanings["ID"]))]

meanings = verb_meanings.append(form_meanings).append(lex_meanings)

log.info("Processing examples")
# prepare examples
examples.rename(
    columns={
        "Sentence": "Primary_Text",
        "Segmentation": "Analyzed_Word",
        "Translation": "Translated_Text",
        "Segmentation": "Analyzed_Word",
        "Orig_Translation": "Orig_Translated_Text",
        "Orig_Segmentation": "Orig_Analyzed_Word",
        "Orig_Glossing": "Orig_Gloss",
    },
    inplace=True,
)
for tcol in ["Analyzed_Word", "Gloss"]:
    examples[tcol] = examples[tcol].str.replace(" ", "\t")

log.info("Tokenizing forms and splitting cognate sets")
segments = open(data_dir / "segments.txt").read()
segment_list = [{"Grapheme": x, "mapping": x} for x in segments.split("\n")]
t = Tokenizer(Profile(*segment_list))


def segmentify(form):
    form = re.sub("[()\[\]]", "", form)
    form = form.replace("-", "+")
    form = form.strip("+")
    return t(form)


verb_stems = verb_stems.append(bathe)
verb_stems.rename(columns={"Meaning_ID": "Parameter_ID"}, inplace=True)
verb_stems.reset_index(inplace=True, drop=True)
verb_stems["ID"] = verb_stems["Language_ID"] + "_stem_" + verb_stems.index.astype(str)

verb_stems["Segments"] = verb_stems["Form"].map(segmentify)

cogsets["Comment"].fillna("", inplace=True)
cogsets["Description"] = (
    "*"
    + cogsets["Form"].astype(str)
    + " '"
    + cogsets["Meaning"].astype(str)
    + "' . "
    + cogsets["Comment"].astype(str)
)

v_forms = v_forms[~(v_forms["Form"] == "–")]
v_forms = v_forms[~(v_forms["Form"].str.contains("?", regex=False))]
v_forms.index = v_forms["Language_ID"] + "_form_" + v_forms.index.astype(str)
v_forms.index.name = "ID"
v_forms.reset_index(inplace=True)
v_forms["Segments"] = v_forms["Form"].map(segmentify)


lex_df.rename(columns={"Meaning": "Parameter_ID"}, inplace=True)
lex_df["Parameter_ID"] = lex_df["Parameter_ID"].str.replace(" ", "_")
lex_df.index = lex_df["Language_ID"] + "_other_" + lex_df.index.astype(str)
lex_df.index.name = "ID"
lex_df.reset_index(inplace=True)
lex_df["Segments"] = lex_df["Form"].map(segmentify)
lex_df["Comment"] = "Form in source: " + lex_df["Full_Form"] + "."


def fix_cog_count(row, prev_df):
    others = prev_df[prev_df["Form_ID"] == row["Form_ID"]]
    if len(others) < 1:
        return row["Segment_Slice"]
    else:
        prev = int(max(others["Segment_Slice"]))
        if pd.isnull(row["Segment_Slice"]):
            return str(prev + 1)
        else:
            return str(int(row["Segment_Slice"]) + prev)


v_forms["Cognateset_ID"] = (
    v_forms["Prefix_Cognateset_ID"] + "+" + v_forms["Verb_Cognateset_ID"]
)
v_forms["Full_Form"] = "Form in source: " + v_forms["Full_Form"] + "."

v_forms["Comment"] = v_forms[["Comment", "Full_Form"]].values.tolist()
v_forms["Comment"] = v_forms.apply(
    lambda row: " ".join([x for x in row["Comment"] if not pd.isnull(x)]), axis=1
)

log.info("Compiling dataframes")

forms = v_forms.append(verb_stems).append(lex_df)

cognates = forms.copy()
cognates["Segment_Slice"] = cognates.apply(
    lambda rec: "+".join(
        [str(x) for x in range(1, rec["Cognateset_ID"].count("+") + 2)]
    ),
    axis=1,
)
cogcols = ["Cognateset_ID", "Segment_Slice"]
for cogcol in cogcols:
    cognates[cogcol] = cognates[cogcol].apply(lambda x: x.split("+"))
cognates["Segments"] = cognates["Segments"].apply(lambda x: x.split(" + "))

cognates = cognates.explode(cogcols + ["Segments"])
cognates["Cognate_ID"] = cognates["ID"] + "_" + cognates["Segment_Slice"]
cognates.rename(columns={"ID": "Form_ID", "Cognate_ID": "ID"}, inplace=True)
cognates = cognates[~(cognates["Cognateset_ID"].isin(["", "?"]))]

alignments = {}
for cogset, cog_df in cognates.groupby("Cognateset_ID"):
    cog_df = cog_df[cog_df["Segments"] != "∅"]
    seglist = lingpy.align.multiple.Multiple(list(cog_df["Segments"]))
    seglist.align(method="library", model="asjp")
    cog_df["Alignment"] = seglist.alm_matrix
    cog_df["Alignment"] = cog_df["Alignment"].apply(lambda x: " ".join(x))
    for i, row_i in cog_df.iterrows():
        alignments[row_i["ID"]] = row_i["Alignment"]

cognates["Alignment"] = cognates.apply(
    lambda x: alignments[x["ID"]] if x["ID"] in alignments else "",
    axis=1,
)

forms["Form"] = forms["Form"].str.replace("+", "", regex=False)

log.info("Getting languages")
found_lgs = set(list(forms["Language_ID"]) + list(examples["Language_ID"]))
lgs = lgs[lgs["ID"].isin(found_lgs)]
lgs.rename(
    columns={"Orthographic": "Name", "long": "Longitude", "lat": "Latitude"},
    inplace=True,
)
lgs = lgs[["ID", "Name", "Glottocode", "Longitude", "Latitude"]]

log.info("Writing")
spec = CLDFSpec(
    dir=data_dir / "cldf", module="Wordlist", metadata_fname="metadata.json"
)

with CLDFWriter(spec) as writer:
    writer.cldf.add_component("CognateTable")
    writer.cldf.remove_columns("CognateTable", "Source")
    writer.cldf.add_component("CognatesetTable")
    writer.cldf.remove_columns("CognatesetTable", "Source")
    writer.cldf.add_component("LanguageTable")
    writer.cldf.add_component("ParameterTable")
    writer.cldf.add_component("ExampleTable")
    writer.cldf.add_columns(
        "ExampleTable",
        {
            "dc:description": "The original object language words in the cited source.",
            "dc:extent": "singlevalued",
            "datatype": "string",
            "required": False,
            "name": "Orig_Analyzed_Word",
        },
        {
            "dc:description": "The original glosses in the cited source.",
            "dc:extent": "singlevalued",
            "datatype": "string",
            "required": False,
            "name": "Orig_Gloss",
        },
        {
            "name": "Orig_Translated_Text",
            "required": False,
            "dc:extent": "singlevalued",
            "dc:description": "The original translation of the example text in the cited source.",
            "datatype": "string",
        },
        {
            "name": "Source",
            "required": False,
            "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
            "datatype": {"base": "string"},
            "separator": ";",
        },
        # {
        #     "name": "Comment",
        #     "required": False,
        #     "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#comment",
        #     "datatype": {"base": "string"},
        # },
    )
    found_refs = []

    for table, df in {
        "LanguageTable": lgs,
        "FormTable": forms,
        "ParameterTable": meanings,
        "CognatesetTable": cogsets,
        "CognateTable": cognates,
        "ExampleTable": examples,
    }.items():
        for sepcol, sep in {
            "Source": "; ",
            "Alignment": " ",
            "Analyzed_Word": "\t",
            "Gloss": "\t",
        }.items():
            if sepcol in df.columns:
                df[sepcol] = df[sepcol].apply(lambda x: x.split(sep))
        for rec in df.to_dict("records"):
            writer.objects[table].append(rec)
            if "Source" in rec:
                for s in rec["Source"]:
                    found_refs.append(s.split("[")[0])

    found_refs = list(set(found_refs))
    bib = pybtex.database.parse_file(data_dir / "cariban.bib")
    sources = [
        Source.from_entry(k, e) for k, e in bib.entries.items() if k in found_refs
    ]
    pc = pybtex.database.Entry(
        "misc",
        [
            ("title", "Placeholder for data obtained from personal communication."),
        ],
    )
    sources.append(Source.from_entry("pc", pc))
    writer.cldf.add_sources(*sources)

    writer.write()
    ds = writer.cldf

ds.validate(log=log)
