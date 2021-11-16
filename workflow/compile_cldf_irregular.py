import pycldf
import pandas as pd
import re
from segments import Profile, Tokenizer

pd.set_option("display.max_rows", 500)
pd.options.mode.chained_assignment = None

print("Reading files")
lgs = pd.read_csv("../../../tools/cariban_cldf/raw/cariban_language_list.csv")
verbs = pd.read_csv("../data/verb_stem_data.csv")
v_forms = pd.read_csv("../data/inflection_data.csv")
bathe = pd.read_csv("../data/bathe_data.csv")
cogsets = pd.read_csv("../data/cognate_sets.csv")
examples = pd.read_csv("../data/examples.csv")
v_forms = v_forms[v_forms["Inflection"].isin(["1"])]
v_forms.reset_index(inplace=True, drop=True)
lex_df = pd.read_csv("../data/other_lexemes.csv")

print("Compiling meanings")
bathe["Meaning_ID"] = bathe["Transitivity"].apply(
    lambda x: "bathe_tr" if x == "TR" else "bathe_intr"
)

par_names = {"bathe_tr": "bathe.TR", "bathe_intr": "bathe.INTR"}

id_desc = {"bathe_tr": "bathe (TR)", "bathe_intr": "bathe (INTR)"}

verb_meanings = (
    v_forms[["Meaning_ID"]].append(verbs[["Meaning_ID"]]).append(bathe[["Meaning_ID"]])
)
verb_meanings.drop_duplicates(subset=["Meaning_ID"], inplace=True)
verb_meanings["Name"] = verb_meanings.apply(
    lambda x: par_names[x["Meaning_ID"]]
    if x["Meaning_ID"] in par_names
    else x["Meaning_ID"].replace("_", "."),
    axis=1,
)
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
form_meanings.drop(columns=["Inflection", "Meaning_ID"], inplace=True)
form_meanings.drop_duplicates(subset=["ID"], inplace=True)

lex_meanings = lex_df[["Meaning"]]
lex_meanings["Name"] = lex_meanings["Meaning"].str.replace(" ", ".")
lex_meanings["Description"] = "'" + lex_meanings["Meaning"] + "'"
lex_meanings["ID"] = lex_meanings["Meaning"].str.replace(" ", "_")
lex_meanings.drop(columns=["Meaning"], inplace=True)
lex_meanings.drop_duplicates(subset=["ID"], inplace=True)
lex_meanings = lex_meanings[~(lex_meanings["ID"].isin(verb_meanings["ID"]))]

meanings = verb_meanings.append(form_meanings).append(lex_meanings)

print("Processing examples")
# prepare examples
examples.drop(columns=["Comment"], inplace=True)
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
examples["Analyzed_Word"] = examples["Analyzed_Word"].str.replace(" ", "\t")
examples["Gloss"] = examples["Gloss"].str.replace(" ", "\t")

print("Tokenizing forms and splitting cognate sets")
# tokenize inflected forms and stems, create cognates (links between forms and cognatesets)
segments = open("../data/segments.txt").read()
segment_list = [{"Grapheme": x, "mapping": x} for x in segments.split("\n")]
t = Tokenizer(Profile(*segment_list))


def segmentify(form):
    form = re.sub("[()\[\]]", "", form)
    form = form.replace("-", "+")
    form = form.strip("+")
    return t(form)


def split_cogset_ids(
    df,
    cogset_col="Cognateset_ID",
    id="ID",
    sep="+",
    suffixes=["1", "2"],
    bare="cog",
    step=0,
):
    out = []
    for i, row in df[[id, cogset_col]].iterrows():
        if pd.isnull(row[cogset_col]): continue
        if sep in row[cogset_col]:
            for j, cog in enumerate(row[cogset_col].split(sep)):
                if cog == "?": continue
                out.append(
                    {
                        "ID": row[id] + "_" + bare + "_" + suffixes[j],
                        "Form_ID": row[id],
                        "Cognateset_ID": cog,
                        "Segment_Slice": str(j + 1 + step),
                    }
                )
        else:
            if row[cogset_col] == "?": continue
            out.append(
                {
                    "ID": row[id] + "_" + bare,
                    "Form_ID": row[id],
                    "Cognateset_ID": row[cogset_col],
                    "Segment_Slice": str(1 + step),
                }
            )
    return pd.DataFrame.from_dict(out)


verbs = verbs.append(bathe)
verbs.rename(columns={"Meaning_ID": "Parameter_ID"}, inplace=True)
verbs.reset_index(inplace=True, drop=True)
verbs.index = verbs["Language_ID"] + "_stem_" + verbs.index.astype(str)
verbs.index.name = "ID"
verbs.reset_index(inplace=True)
verb_cogs = split_cogset_ids(verbs, suffixes=["1", "2", "3"])

verbs.drop(columns=["Cog_Cert", "Class", "Transitivity"], inplace=True)
verbs["Segments"] = verbs["Form"].map(segmentify)

cogsets["Comment"].fillna("", inplace=True)
cogsets["Description"] = (
    "*"
    + cogsets["Form"].astype(str)
    + " '"
    + cogsets["Meaning"].astype(str)
    + "' . "
    + cogsets["Comment"].astype(str)
)
cogsets.drop(columns=["Form", "Meaning", "Comment"], inplace=True)

v_forms = v_forms[~(v_forms["Form"] == "–")]
v_forms = v_forms[~(v_forms["Form"].str.contains("?", regex=False))]
v_forms.index = v_forms["Language_ID"] + "_form_" + v_forms.index.astype(str)
v_forms.index.name = "ID"
v_forms.reset_index(inplace=True)
v_forms["Segments"] = v_forms["Form"].map(segmentify)

form_cogs1 = split_cogset_ids(
    v_forms, cogset_col="Prefix_Cognateset_ID", suffixes=["pfx1", "pfx2"], bare="infl"
)
form_cogs2 = split_cogset_ids(
    v_forms, cogset_col="Verb_Cognateset_ID", suffixes=["pfx", "root"], bare="stem"
)

lex_df.rename(columns={"Meaning": "Parameter_ID"}, inplace=True)
lex_df["Parameter_ID"] = lex_df["Parameter_ID"].str.replace(" ", "_")
lex_df.index = lex_df["Language_ID"] + "_other_" + lex_df.index.astype(str)
lex_df.index.name = "ID"
lex_df.reset_index(inplace=True)
lex_df["Segments"] = lex_df["Form"].map(segmentify)
lex_df["Comment"] = "Form in source: " + lex_df["Full_Form"] + "."
lex_df.drop(columns=["Full_Form"], inplace=True)

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


form_cogs2["Segment_Slice"] = form_cogs2.apply(
    lambda x: fix_cog_count(x, form_cogs1), axis=1
)

v_forms["Cognateset_ID"] = (
    v_forms["Prefix_Cognateset_ID"] + "+" + v_forms["Verb_Cognateset_ID"]
)
v_forms["Full_Form"] = "Form in source: " + v_forms["Full_Form"] + "."

v_forms["Comment"] = v_forms[["Comment", "Full_Form"]].values.tolist()
v_forms["Comment"] = v_forms.apply(lambda row: " ".join([x for x in row["Comment"] if not pd.isnull(x)]), axis=1)
v_forms.drop(
    columns=["Verb_Cognateset_ID", "Prefix_Cognateset_ID", "Full_Form", "Inflection"],
    inplace=True,
)

print("Compiling dataframes")
cognates = verb_cogs.append(form_cogs1).append(form_cogs2)
cognates.sort_values(by=["Form_ID", "Segment_Slice"], inplace=True)
cognates.reset_index(inplace=True, drop=True)

forms = v_forms.append(verbs).append(lex_df)
forms["Form"] = forms["Form"].str.replace("+", "", regex=False)
forms.drop(columns=["Cognateset_ID", "Meaning_ID"], inplace=True)

print("Getting languages")
# extract relevant languages
found_lgs = set(list(forms["Language_ID"]) + list(examples["Language_ID"]))
lgs = lgs[lgs["ID"].isin(found_lgs)]
lgs.drop(
    columns=[
        "IPA",
        "Shorthand",
        "Dialect_Of",
        "Todo",
        "Comment",
        "Alternative_Names",
        "Sampled",
        "Alive",
        "CLLD_Name",
        "ISO",
    ],
    inplace=True,
)
lgs.rename(
    columns={"Orthographic": "Name", "long": "Longitude", "lat": "Latitude"},
    inplace=True,
)
lgs = lgs[["ID", "Name", "Glottocode", "Longitude", "Latitude"]]

print("Saving files")
lgs.to_csv("../data/cldf/languages.csv", index=False)
lgs.to_csv("../data/languages.csv", index=False)
forms.to_csv("../data/cldf/forms.csv", index=False)
meanings.to_csv("../data/cldf/parameters.csv", index=False)
cogsets.to_csv("../data/cldf/cognatesets.csv", index=False)
examples.to_csv("../data/cldf/examples.csv", index=False)
cognates.to_csv("../data/cldf/cognates.csv", index=False)

print("Bib stuff")
import pandas as pd
import cldf_helpers
import os
from pybtex.database.input import bibtex
from pybtex.database import BibliographyData

data_path = "../data"
found_refs = []
for filename in os.listdir(data_path):
    if not filename.endswith(".csv"):
        continue
    if filename in ["extensions.csv", "cognate_sets.csv", "languages.csv"]:
        continue
    df = pd.read_csv(os.path.join(data_path, filename))
    for i in df["Source"]:
        if pd.isnull(i):
            continue
        found_refs.append(cldf_helpers.split_ref(i)[0])
found_refs = list(set(found_refs))
found_refs.remove("pc")

bibfile = "../../../tools/cariban_cldf/raw/cariban_resolved.bib"
bib_parser = bibtex.Parser()
bib_data = bib_parser.parse_file(bibfile)
filtered_bib_data = BibliographyData()
for key, entry in bib_data.entries.items():
    if key in found_refs:
        # print(entry)
        filtered_bib_data.add_entry(entry.key, entry)

s = filtered_bib_data.to_string("bibtex")
f = open(os.path.join(data_path, "cldf", "references.bib"), "w")
f.write(s)
f.close()
