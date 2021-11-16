import pyradigms as pyd
import warnings
import json

warnings.filterwarnings("ignore")
import pandas as pd

pd.options.mode.chained_assignment = None
import cariban_helpers as cah
import cldf_helpers as cldfh
import pynterlinear as pynt
import numpy as np
import re
from segments import Tokenizer, Profile
from lingpy_alignments import calculate_alignment

lg_list = list(cah.lg_order().keys())
cognate_list = ["go", "say", "come", "be_1", "be_2", "go_down", "bathe_intr"]
cs_df = pd.read_csv("../data/cognate_sets.csv")
v_df = pd.read_csv("../data/verb_stem_data.csv")
v_df.rename(columns={"Meaning_ID": "Parameter_ID"}, inplace=True)
e_df = pd.read_csv("../data/extensions.csv")
i_df = pd.read_csv("../data/inflection_data.csv")
i_df["Form"] = i_df["Form"].str.replace("+", "", regex=True)

m_df = pd.read_csv("../data/cldf/parameters.csv")
m_df["Description"] = m_df["Description"].str.strip("'").map(pynt.get_expex_code)
mean_dic = dict(zip(m_df["ID"], m_df["Description"]))
trans_dic = {x: "\\qu{%s}" % y for x, y in mean_dic.items()}

concept_dic = {
    "DETRZ1+bathe_1": "bathe_intr",
    "DETRZ+come": "come",
    "DETRZ1": "bathe_intr",
}

i_df["Concept"] = i_df.apply(
    lambda x: concept_dic[x["Verb_Cognateset_ID"]]
    if x["Verb_Cognateset_ID"] in concept_dic
    else x["Verb_Cognateset_ID"],
    axis=1,
)

segments = open("../data/segments.txt").read()
segment_list = [{"Grapheme": x, "mapping": x} for x in segments.split("\n")]
t = Tokenizer(Profile(*segment_list))
cognatesets = pd.read_csv("../data/cldf/cognatesets.csv")
cognatesets = cognatesets.append(
    {"ID": "?", "Description": "Unknown material"}, ignore_index=True
)

# lingpy does not like cogid 0
cognatesets.index = cognatesets.index + 1
cognum = dict(zip(cognatesets["ID"], cognatesets.index.astype(str)))
numcog = dict(zip(cognatesets.index.astype(str), cognatesets["ID"]))

cog_verb_df = cs_df[~(cs_df["Form"].str.contains("-"))]
cog_trans_dic = dict(zip(cog_verb_df["ID"], cog_verb_df["Meaning"]))
cog_form_dic = dict(zip(cog_verb_df["ID"], cog_verb_df["Form"]))
cog_form_dic["bathe_intr"] = "e-pɨ"
cog_form_dic["come"] = "(ət-)jəpɨ"
cog_trans_dic["bathe_intr"] = r"bathe"
cog_trans_dic["be_1"] = r"be-1"
cog_trans_dic["be_2"] = r"be-2"

def print_shorthand(abbrev):
    return "\\" + cah.get_shorthand(abbrev)

def str2numcog(cogsets):
    return " ".join([cognum[x] for x in cogsets.split("+")])


def num2strcog(cogids):
    return "+".join([numcog[i] for i in cogids.split(" ")])


def segmentify(form):
    form = re.sub("[()\[\]]", "", form)
    form = form.replace("-", "+")
    form = form.strip("+")
    return t(form)


exported_tables = {}

def export_csv(
    tabular,
    label,
    caption=None,
    keep_index=False,
    sources=None,
    print_i_name=False,
    print_c_name=False,
):
    tabular = tabular.copy()
    # if caption:
    #     print(f"{caption}: ")
    if not print_i_name:
        tabular.index.name = ""
    if not print_c_name:
        if type(tabular.columns) == pd.MultiIndex:
            tabular.columns.names = [None for x in tabular.columns.names]
        # for c in tabular.columns:
        #     if type(c) == tuple:
        #         c = (None for x in c)

    # print(tabular)
    tabular.to_csv(f"data_output/{label}.csv", index=keep_index)
    exported_tables[label] = {"caption": caption}
    if sources:
        src = cldfh.combine_refs(sources)
        # print("(" + ", ".join(src) + ")")
        exported_tables[label]["sources"] = src


# functions for creating latex tables
def print_latex(df, ex=False, keep_index=False):
    if keep_index:
        df.columns.name = df.index.name
        df.index.name = None

    with pd.option_context("max_colwidth", 1000):
        lines = df.to_latex(escape=False, index=keep_index).split("\n")
    lines[0] = lines[0].replace("tabular}{l", "tabular}[t]{@{}l").replace("l}", "l@{}}")
    if ex:
        del lines[1:4]
        del lines[-1]
        del lines[-2]
        return "\n".join(lines)
    else:
        return "\n".join(lines).replace(r"\toprule", "\mytoprule").replace("%", "\\%")


def save_float(tabular, label, caption, filename=None, short=None):
    if not filename:
        filename = label
    if not short:
        shorttext = ""
    else:
        shorttext = f"[{short}]"
    output = f"""\\begin{{table}}
\centering
\caption{shorttext}{{{caption}}}
\label{{tab:{label}}}
{tabular}\end{{table}}"""
    f = open(f"../documents/floats/{filename}.tex", "w")
    f.write(output)
    f.close()


normalfonties = ["Ø", "?", "V", "G", "C", "∅"]


def objectify(string, obj_string="obj"):
    if string in ["", "?", " ", "  ", "–"]:
        return string
    if string is None:
        return ""
    if string[0] == " ":
        return string
    output = []
    entry_list = string.split(" OR ")
    for entry in entry_list:
        out_list = []
        morph_list = entry.split("; ")
        for i, morph in enumerate(morph_list):
            out_list.append(r"\%s{%s}" % (obj_string, morph))
            if i > 0:
                obj_string = "obj"
        output.append("/".join(out_list))
    for i, cell in enumerate(output):
        if r"\env" in cell:
            output[i] = cell.replace(r"\obj", "")
    output = ", ".join(output)
    for normalfonty in normalfonties:
        output = output.replace(normalfonty, r"{\normalfont %s}" % normalfonty)
    return output


def combine_form_meaning(row, latex=True):
    if latex:
        form = objectify(row["Form"])
        meaning = f"""\\qu{{{row["Meaning"]}}}"""
    else:
        form = f"""*{row["Form"]}*"""
        meaning = f"""'{row["Meaning"]}'"""
    out = form + " " + meaning
    return out


def get_sources(df, parens=True, latexify=True):
    tmp = pyd.content_string
    pyd.content_string = "Source"
    table = pyd.compose_paradigm(df)
    pyd.content_string = tmp
    ref_list = [j for i in table.values.tolist() for j in i]
    if not latexify:
        return cldfh.combine_refs(ref_list)
    source_string = cldfh.cite_a_bunch(ref_list, parens=parens)
    return source_string

def upper_repl(match):
     return match.group(1).upper()
     
def repl_latex(string):
    string = re.sub(r"\\rc\{(.*?)\}", r"\**\1*", string)
    string = re.sub(r"\\gl\{(.*?)\}", upper_repl, string)
    string = re.sub(r"\\obj\{(.*?)\}", r"*\1*", string)
    string = re.sub(r"\\qu\{(.*?)\}", r"'\1'", string)
    return string

def sort_lg(df):
    df.Language_ID = df.Language_ID.astype("category")
    df.Language_ID.cat.set_categories(lg_list, ordered=True, inplace=True)
    df.sort_values(["Language_ID"], inplace=True)

def extract_sources(df, src_str="Source", keep=False, latexify=True):
    df[src_str] = df[src_str].fillna("")
    src = list(df[src_str])
    if "" in src:
        src.remove("")
    if not keep:
        df.drop(columns=[src_str], inplace=True)
    if not latexify:
        return cldfh.combine_refs(src)
    sources = cldfh.cite_a_bunch(src, parens=True)
    return sources


def proto_lg(lg):
    return lg[0] == "P"


def get_obj_str(lg):
    if proto_lg(lg):
        return "rc"
    else:
        return "obj"


def add_obj_markdown(df, lg_col="Language_ID", form_col="Form"):
    df[form_col] = df.apply(
        lambda x: objectify(x[form_col], get_obj_str(x[lg_col])), axis=1
    )


def repl_lg_id(df):
    df["Language_ID"] = df["Language_ID"].apply(print_shorthand)
    df.rename(columns={"Language_ID": "Language"}, inplace=True)


shorthand_dic = {x: print_shorthand(x) for x in lg_list}
name_dic = {x: cah.get_name(x) for x in lg_list}

ext_lg_dic = {x: y for x, y in dict(zip(e_df["ID"], e_df["Language_ID"])).items()}
ext_form_dic = {x: y for x, y in dict(zip(e_df["ID"], e_df["Form"])).items()}

def extension_string(id, latex=True):
    form = objectify(ext_form_dic[id], obj_string=get_obj_str(ext_lg_dic[id]))
    if latex:
        return print_shorthand(ext_lg_dic[id]) + " " + form
    else:
        return name_dic[ext_lg_dic[id]] + " " + repl_latex(form)

person = ["1", "2", "1+2", "3"]
pyd.x = ["Meaning_ID"]
pyd.y = ["Inflection"]
pyd.y_sort = person
for lg, meanings in {
    "hix": ["fall", "be_afraid", "walk", "cut_self", "be"],
    "tri": ["sleep", "see_self", "bathe_intr", "yawn", "go"],
    "mak": ["eat", "arrive", "go", "be"]
    # "yuk": ["wash_self", "sleep", "fall"],
}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning_ID": meanings, "Inflection": person}
    pyd.x_sort = meanings
    tabular = pyd.compose_paradigm(i_df[i_df["Verb_Cognateset_ID"] != "be_1"], multi_index=False)
    label = lg + "intro"
    tabular_raw = tabular.rename(columns=mean_dic)
    tabular_raw.columns = [repl_latex(f"'{col}'") for col in tabular_raw.columns]
    export_csv(
        tabular_raw,
        label,
        f"Some {name_dic[lg]} verbs",
        keep_index=True,
        sources=get_sources(i_df, latexify=False),
    )
    sources = get_sources(i_df)
    tabular.index = tabular.index.map(pynt.get_expex_code)
    tabular.index.name = None
    tabular.rename(columns=trans_dic, inplace=True)
    tabular = tabular.apply(lambda x: x.apply(objectify))
    tabular.columns.names = [None]
    save_float(
        print_latex(tabular, keep_index=True),
        label,
        f"Some {print_shorthand(lg)} verbs " + sources,
        short=f"Some {print_shorthand(lg)} verbs",
    )


# regular pekodian verbs
tabular = pd.DataFrame()
sources_raw = []
pyd.x = ["Language_ID", "Meaning_ID"]
pyd.y = ["Inflection"]
for lg, meaning in {"bak": "go_up", "ara": "dance", "ikp": "run"}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning_ID": [meaning]}
    pyd.sort_orders = {"Inflection": person}
    temp = pyd.compose_paradigm(i_df, multi_index=True)
    sources_raw.extend(get_sources(i_df, latexify=False))
    tabular = pd.concat([tabular, temp], axis=1)

sources = cldfh.cite_a_bunch(sources_raw, parens=True)
label = "pekreg"
tabular.index.names = [None]
export_csv(
    tabular.rename(columns=name_dic, level="Language_ID"),
    label,
    "Regular Pekodian Sa verbs",
    keep_index=True,
    sources=sources_raw,
)

tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[1])))
tabular.rename(columns=trans_dic, level="Meaning_ID", inplace=True)
tabular.rename(columns=shorthand_dic, level="Language_ID", inplace=True)

tabular.columns.names = [None, None]
tabular.index = tabular.index.map(pynt.get_expex_code)
tabular.columns = [" ".join([x, y]) for x, y in tabular.columns]


save_float(
    print_latex(tabular, keep_index=True),
    label,
    "Regular Pekodian \gl{s_a_} verbs " + sources,
    short="Regular Pekodian \gl{s_a_} verbs",
)


def reconstructed_form_table(lgs, proto, verbs, caption, name):
    pyd.x = ["Language_ID"]
    pyd.y = ["Concept"]
    pyd.filters = {"Inflection": ["1"], "Language_ID": lgs, "Concept": verbs}
    pyd.x_sort = lgs
    pyd.y_sort = verbs
    tabular = pyd.compose_paradigm(i_df)
    sources = get_sources(i_df)
    raw_sources = get_sources(i_df, latexify=False)
    tabular.index.name = None
    export_csv(
        tabular.rename(columns=name_dic),
        name,
        f"Irregular {cah.get_name(proto)} verbs",
        True,
        sources=raw_sources,
    )
    tabular.index = tabular.index.map(lambda x: "\\qu{" + cog_trans_dic[x] + "}")
    tabular = tabular.apply(
        lambda x: x.apply(objectify, obj_string=get_obj_str(x.name))
    )
    tabular.columns = tabular.columns.map(print_shorthand)
    tabular = print_latex(tabular, keep_index=True)

    save_float(
        tabular,
        name,
        caption + " " + sources,
        short=caption,
    )
    pyd.filters = {}


lgs = ["PPek", "ara", "ikp", "bak"]
verbs = ["say", "bathe_intr", "be_1", "be_2", "come", "go_down", "go"]
reconstructed_form_table(
    lgs,
    "PPek",
    verbs,
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PPek",
    "ppekverbs",
)

# regular proto-waiwaian verbs
meanings = ["fall", "sleep"]
lgs = ["PWai", "hix", "wai"]
pyd.x = ["Language_ID", "Meaning_ID"]
pyd.y = ["Inflection"]
pyd.filters = {"Language_ID": lgs, "Meaning_ID": meanings}
pyd.sort_orders = {
    "Language_ID": lgs,
    "Meaning_ID": meanings,
    "Inflection": ["1", "2", "1+2", "3"],
}
tabular = pyd.compose_paradigm(i_df, multi_index=True)
sources = get_sources(i_df)

export_csv(
    tabular.rename(columns=name_dic, level="Language_ID"),
    "pwaireg",
    "Regular 'to fall' (Sa) and 'to sleep' (Sp) in Proto-Waiwaian",
    sources=get_sources(i_df, latexify=False),
)
tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[0])))
tabular.rename(
    columns={"sleep": r"\qu{to sleep}", "fall": "\qu{to fall}"},
    level="Meaning_ID",
    inplace=True,
)
tabular.rename(columns=shorthand_dic, level="Language_ID", inplace=True)
tabular.index = tabular.index.map(pynt.get_expex_code)
tabular.index.names = [None]
tabular.columns.names = [None, None]
save_float(
    print_latex(tabular, keep_index=True),
    "pwaireg",
    "Regular \qu{to fall} (\gl{s_a_}) and \qu{to sleep} (\gl{s_p_}) in \PWai "
    + sources,
    short="Regular \PWai verbs",
)

lgs = ["PWai", "hix", "wai"]
verbs = ["say", "be_1", "be_2", "go"]
reconstructed_form_table(
    lgs,
    "PWai",
    verbs,
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PWai",
    "pwaiverbs",
)

# regular proto-tiriyoan verbs
tir_reg = i_df[~(pd.isnull(i_df["Verb_Cognateset_ID"]))]
meanings = ["bathe_intr", "sleep"]
lgs = ["PTir", "tri", "aku"]
pyd.filters = {"Language_ID": lgs, "Meaning_ID": meanings}
pyd.x = ["Meaning_ID", "Language_ID"]
pyd.y = ["Inflection"]
pyd.sort_orders = {
    "Language_ID": lgs,
    "Meaning_ID": meanings,
    "Inflection": ["1", "2", "1+2", "3"],
}
tabular = pyd.compose_paradigm(tir_reg, multi_index=True)
sources = get_sources(tir_reg)

export_csv(
    tabular.rename(columns=name_dic, level="Language_ID"),
    "ptirreg",
    "Regular Proto-Tiriyoan Sa verbs",
    sources=get_sources(tir_reg, latexify=False),
)

tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[1])))

tabular.rename(columns=trans_dic, level="Meaning_ID", inplace=True)
tabular.rename(columns=shorthand_dic, level="Language_ID", inplace=True)

tabular.index = tabular.index.map(pynt.get_expex_code)
tabular.index.names = [None]
tabular.columns.names = [None, None]
save_float(
    print_latex(tabular, keep_index=True),
    "ptirreg",
    "Regular \PTir \gl{s_a_} verbs " + sources,
    short="Regular \PTir \gl{s_a_} verbs",
)

reconstructed_form_table(
    ["PTir", "tri", "aku"],
    "PTir",
    ["go", "say", "come", "be_1", "be_2"],
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PTir",
    "ptirverbs",
)

akuverbs = i_df[
    (i_df["Language_ID"] == "aku") & (i_df["Prefix_Cognateset_ID"].isin(["k", "1t"]))
]
akuverbs["Form"] = akuverbs["Form"].apply(lambda x: x.split("-", 1)[1])
akuverbs["Meaning"] = akuverbs["Meaning_ID"].map(mean_dic)
akuverbs["String"] = akuverbs.apply(combine_form_meaning, axis=1)

k_list = akuverbs[akuverbs["Prefix_Cognateset_ID"] == "k"]["String"].reset_index(
    drop=True
)
t_list = akuverbs[akuverbs["Prefix_Cognateset_ID"] == "1t"]["String"].reset_index(
    drop=True
)
sources = extract_sources(akuverbs)
out = pd.DataFrame.from_dict(
    {r"first person \obj{k-}": k_list, r"first person \obj{t͡ʃ-}": t_list}
)
out.fillna("", inplace=True)

save_float(
    print_latex(out),
    "aku1sa",
    r"Regular \akuriyo \gl{1}\gl{s_a_} markers " + sources,
    short=r"Regular \akuriyo \gl{1}\gl{s_a_} markers",
)

# regular carijo and yukpa verbs
pyd.x = ["Meaning_ID"]
pyd.y = ["Inflection"]
pyd.y_sort = ["1", "2", "1+2", "3"]
for lg, meanings in {
    "car": ["arrive", "dance"],
    "yuk": ["wash_self", "sleep", "fall"],
}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning_ID": meanings}
    tabular = pyd.compose_paradigm(i_df, multi_index=False)
    label = lg + "reg"
    export_csv(
        tabular,
        label,
        f"Regular {name_dic[lg]} verbs",
        keep_index=True,
        sources=get_sources(i_df, latexify=False),
    )
    sources = get_sources(i_df)
    tabular.index = tabular.index.map(pynt.get_expex_code)
    tabular.index.name = None
    tabular.rename(columns=trans_dic, inplace=True)
    tabular = tabular.apply(lambda x: x.apply(objectify))
    tabular.columns.names = [None]

    save_float(
        print_latex(tabular, keep_index=True),
        label,
        f"Regular {print_shorthand(lg)} verbs " + sources,
        short=f"Regular {print_shorthand(lg)} verbs",
    )

i_df = i_df[~(pd.isnull(i_df["Verb_Cognateset_ID"]))]

# pekodian lexical comparison
forms = pd.read_csv("../data/cldf/forms.csv")
lgs = ["ara", "ikp"]
meanings = [
    "defecate",
    "DAT",
    "dog",
    "capuchin_monkey",
    "sleep",
]
pyd.x = ["Language_ID"]
pyd.y = ["Parameter_ID"]
pyd.filters = {"Language_ID": lgs, "Parameter_ID": meanings}
pyd.x_sort = lgs
pyd.y_sort = meanings
tabular = pyd.compose_paradigm(forms)
label = "pxinw"
export_csv(
    tabular,
    label,
    "Loss of \**w* in Ikpeng",
    keep_index=True,
    sources=get_sources(forms, latexify=False),
)
sources = get_sources(forms)
tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name)))
tabular.columns = tabular.columns.map(print_shorthand)

tabular.index.name = "Meaning"
tabular.reset_index(inplace=True)
tabular["Meaning"] = tabular["Meaning"].map(mean_dic)
tabular["Meaning"] = tabular["Meaning"].map(lambda x: "\\qu{" + x + "}")

save_float(
    print_latex(tabular),
    label,
    r"Loss of \rc{w} in \ikpeng " + sources,
    short=r"Loss of \rc{w} in \ikpeng",
)
pyd.filters = {}

# prepare overviews of class-switching 'go down' and 'defecate'
gd_df = v_df[v_df["Parameter_ID"] == "go_down"]
sources = extract_sources(gd_df, keep=True)
raw_sources = extract_sources(gd_df, latexify=False)

grouped = gd_df.groupby(gd_df.Cog_Cert)
temp_df1 = grouped.get_group(1.0)
temp_df2 = grouped.get_group(0.5)
temp_df1["Segments"] = temp_df1.apply(lambda x: segmentify(x["Form"]), axis=1)
temp_df1["Cognateset_ID"] = temp_df1["Cognateset_ID"].map(str2numcog)
temp_df1 = calculate_alignment(temp_df1, fuzzy=True)
temp_df1["Cognateset_ID"] = temp_df1["Cognateset_ID"].map(num2strcog)
temp_df1.rename(columns={"Cognateset_ID1": "Cognateset_ID"}, inplace=True)
temp_df1["Class"] = temp_df1.apply(
    lambda x: "(" + x["Class"] + ")" if "DETRZ" in x["Cognateset_ID"] else x["Class"],
    axis=1,
)
temp_df2["Form"] = temp_df2.apply(lambda x: "(" + x["Form"] + ")", axis=1)
for i, row in temp_df2.iterrows():
    temp_df1 = temp_df1.append(row)
temp_df1.drop(
    columns=["Cognateset_ID", "Comment", "Cog_Cert", "Parameter_ID", "Segments"],
    inplace=True,
)
gd_df = temp_df1
gd_df.fillna("", inplace=True)
gd_df["Form"] = gd_df["Form"].str.replace("+", "", regex=True)
sort_lg(gd_df)

label = "godown"
export_csv(
    gd_df.replace({"Language_ID": name_dic}).rename(
        columns={"Language_ID": "Language"}
    ),
    label,
    "Reflexes of \**ɨpɨtə* 'to go down'",
    sources=raw_sources,
)

gd_df["Class"] = gd_df.apply(
    lambda x: pynt.get_expex_code(x["Class"])
    if x["Class"] not in ["?", "–"]
    else x["Class"],
    axis=1,
)
add_obj_markdown(gd_df)
repl_lg_id(gd_df)
gd_df.set_index("Language", drop=True, inplace=True)
tabular = print_latex(gd_df, keep_index=True)
save_float(
    tabular,
    label,
    r"Reflexes of \rc{ɨpɨtə} \qu{to go down} " + sources,
    short=r"Reflexes of \rc{ɨpɨtə} \qu{to go down}",
)

print("\nClass membership of 'to defecate':")
s_df = v_df[v_df["Parameter_ID"] == "defecate"]
sources = extract_sources(s_df)
s_df.drop(
    columns=["Parameter_ID", "Cog_Cert", "Comment", "Cognateset_ID"], inplace=True
)
s_df["Form"] = s_df["Form"].str.replace("+", "", regex=True)
sort_lg(s_df)
print(s_df)
s_df["Class"] = s_df.apply(
    lambda x: pynt.get_expex_code(x["Class"])
    if x["Class"] not in ["?", "–"]
    else x["Class"],
    axis=1,
)
add_obj_markdown(s_df)
repl_lg_id(s_df)
s_df.set_index("Language", drop=True, inplace=True)
tabular = print_latex(s_df, keep_index=True)
save_float(
    tabular,
    "defecate",
    r"Reflexes of \qu{to defecate} " + sources,
    short=r"Reflexes of \qu{to defecate} ",
)


def print_aligned_table(
    df, verb="new_verb", caption="", fuzzy=False, only_tab=False, do_sources=True
):
    fields = ["Language_ID", "Form", ""]
    if do_sources:
        sources = extract_sources(df, keep=True)
        raw_sources = extract_sources(df, latexify=False)
    else:
        raw_sources = extract_sources(df, latexify=False, keep=True)
    df["Segments"] = df.apply(lambda x: segmentify(x["Form"]), axis=1)
    df["Cognateset_ID"] = df["Cognateset_ID"].map(str2numcog)
    df = calculate_alignment(df, fuzzy=fuzzy)
    df = df[fields]
    sort_lg(df)
    for i, col in enumerate(df.columns):
        if col == "":
            # df.columns.values[i] = "Alignment"
            break
    df["Form"] = df["Form"].str.replace("+", "", regex=True)
    export_csv(
        df.replace({"Language_ID": name_dic}).rename(columns={"Language_ID": "Language"}),
        verb,
        repl_latex(caption),
        sources = raw_sources
    )
    add_obj_markdown(df)
    repl_lg_id(df)
    df.set_index("Language", drop=True, inplace=True)
    tabular = print_latex(df, keep_index=True)
    if only_tab:
        if do_sources:
            return tabular, sources
        else:
            return tabular
    else:
        if do_sources:
            save_float(
                tabular,
                verb,
                caption + " " + sources,
                short=caption,
            )
        else:
            save_float(
                tabular,
                verb,
                caption,
            )


print_aligned_table(
    v_df[v_df["Parameter_ID"] == "come"],
    verb="come",
    caption=r"Reflexes of \rc{(ət-)jəpɨ} \qu{to come}",
    fuzzy=True,
)
print_aligned_table(
    v_df[v_df["Parameter_ID"] == "go"],
    verb="go",
    caption=r"Reflexes of \rc{ɨtə[mə]} \qu{to go}",
)
print_aligned_table(
    v_df[v_df["Parameter_ID"] == "say"],
    verb="say",
    caption=r"Reflexes of \rc{ka[ti]} \qu{to say}",
)

# comparison of intransitive and transitive 'to bathe'
df_b = pd.read_csv("../data/bathe_data.csv")
df_b["Parameter_ID"] = df_b["Transitivity"].apply(lambda x: "bathe" + "_" + x.lower())
df_b.drop(columns=["Transitivity"], inplace=True)
df_b.index = df_b.index + 1
sources = extract_sources(df_b, keep=True)
tr = df_b[df_b["Parameter_ID"] == "bathe_tr"]
intr = df_b[df_b["Parameter_ID"] == "bathe_intr"]
intr_1 = intr[intr["Cognateset_ID"] == "DETRZ1+bathe_2"]
intr_2 = intr[intr["Cognateset_ID"] == "DETRZ+bathe_2"]
intr.drop(intr_1.index, inplace=True)
intr.drop(intr_2.index, inplace=True)
tr_1 = tr[tr["Cognateset_ID"] == "bathe_2"]
tr.drop(tr_1.index, inplace=True)

bathe_tables = [
    (intr, r"Reflexes of \rc{e-pɨ} \qu{to bathe (\gl{intr})}", "bathe_intr_1", True),
    (
        intr_1,
        r"Reflexes of \rc{e-kupi} \qu{to bathe (\gl{intr})}",
        "bathe_intr_2",
        True,
    ),
    (
        intr_2,
        r"Reflexes of \rc{ə-kupi} \qu{to bathe (\gl{intr})}",
        "bathe_intr_3",
        True,
    ),
    (tr, r"Reflexes of \rc{(ɨ)pɨ} \qu{to bathe (\gl{tr})}", "bathe_tr_1", False),
    (tr_1, r"Reflexes of \rc{kupi} \qu{to bathe (\gl{tr})}", "bathe_tr_2", False),
]

bathe_out = (
    r"""\begin{table}
\caption[Comparison of intransitive and transitive \qu{to bathe}]{Comparison of intransitive and transitive \qu{to bathe} %s}
\label{tab:bathe}
\small
\centering
"""
    % sources
)

for table in bathe_tables:
    tabular = print_aligned_table(
        table[0],
        verb=table[2],
        caption=table[1],
        only_tab=True,
        fuzzy=table[-1],
        do_sources=False,
    )
    if table[2] == "bathe_intr_1":
        bathe_out += r"""\begin{subtable}[t]{.49\linewidth}
\centering
"""
    if table[2] == "bathe_tr_1":
        bathe_out += r"""\end{subtable}
\begin{subtable}[t]{.49\linewidth}
\centering"""
    bathe_out += r"""\caption{%s}
\label{tab:%s}
%s""" % (
        table[1],
        table[2],
        tabular,
    )
bathe_out += r"\end{subtable}\end{table}"
f = open(f"../documents/floats/bathe.tex", "w")
f.write(bathe_out)
f.close()

# overview of what extensions affected what verbs
i_df = i_df[i_df["Inflection"] == "1"]
verb_list = ["say", "go", "be_1", "be_2", "come", "go_down", "bathe_intr"]

# determine whether verb was affected by extensions based on cognacy of prefixes
def identify_affected(cogset, row):
    value = row["Prefix_Cognateset_ID"]
    verb = row["Verb_Cognateset_ID"]
    lg = row["Language_ID"]
    # 'go down' used to be an Sp verb, the relative chronology of the class
    # change and the extensions, and whether the class occurred at all
    # are not known in some cases
    if verb == "go_down" and lg not in ["PPek", "ara", "ikp", "bak"]:
        # the extension of PTir *t- could have happened before or after the class change
        # the extension of car and yuk j- could have happened before or after the collapse
        # of the system. the verb might have changed class or not.
        if cogset in ["1t", "1p"] or lg in ["PWai", "wai", "hix"]:
            return "N/A"
        # we have to assume that when aku extended k-
        # it was already an Sa verb
        elif lg == "aku":
            return "n"
        # the verb didn't exist in PWai, and while it could have switched classes
        # *after* the extension of PPek *k-, why would it have acquired the old Sa
        # marker instead of the new one?
        else:
            raise ValueError("This combination should not occur")
    # we either don't know what form occurs or we think no potential form exists
    elif value in ["?", "–"]:
        return value
    # we think the verb does not occur at all in the language
    elif pd.isnull(value):
        return "–"
    else:
        # the new person marker occurs on the verb
        if cogset == value:
            return "y"
        # the new person marker occurs on the verb together
        # with another prefix (wai)
        elif cogset in value.split("+"):
            return "(y)"
        # the new marker does not occur on the verb
        else:
            return "n"


overview_legend = {
    "y": {"tex": "\checkmark", "legend": "affected"},
    "n": {"tex": "×", "legend": "not affected"},
    "?": {"tex": "?", "legend": "unknown first person prefix"},
    "–": {"tex": "–", "legend": "does not occur"},
    "(y)": {"tex": "(\\checkmark)", "legend": "affected with surviving old marker"},
    "N/A": {"tex": "\\textsc{n/a}", "legend": "not meaningfully answerable"},
}

# extensions that happened in proto-languages sometimes go further in daughter languages
daughters = {
    "PWai": ["wai", "hix"],
    "PTir": ["tri", "aku"],
    "PPek": ["ara", "ikp", "bak"],
}

overview = pd.DataFrame()
for i, row in e_df.iterrows():
    if row["Language_ID"] in daughters:
        lgs = [row["Language_ID"]] + daughters[row["Language_ID"]]
    else:
        lgs = [row["Language_ID"]]
    for lg in lgs:
        t_df = i_df[i_df["Language_ID"] == lg]
        t_df["Prefix_Form"] = row["Form"]
        t_df["Orig_Language"] = row["Language_ID"]
        t_df["Extension_ID"] = row["ID"]
        t_df["Affected"] = t_df.apply(
            lambda x: identify_affected(row["Cognateset_ID"], x),
            axis=1,
        )
        overview = overview.append(t_df)

overview.drop(
    columns=[
        "Source",
        "Prefix_Cognateset_ID",
        "Inflection",
        "Full_Form",
        "Comment",
    ],
    inplace=True,
)

affectedness = overview[overview["Language_ID"] == overview["Orig_Language"]]
affectedness = affectedness[affectedness["Affected"].isin(["y", "n"])]
affectedness = affectedness[affectedness["Concept"].isin(verb_list)]

affectedness.drop(
    columns=["Prefix_Form", "Orig_Language", "Language_ID"],
    inplace=True,
)

overview.drop(
    columns=["Form", "Extension_ID"],
    inplace=True,
)

pyd.x = ["Cognateset_ID"]
pyd.y = ["Orig_Language", "Prefix_Form", "Language_ID"]
pyd.content_string = "Affected"
pyd.x_sort = verb_list

repl_dic = {
    "DETRZ+come": "come",
    "DETRZ1+bathe_1": "bathe_intr",
    "DETRZ1": "bathe_intr",
}

overview["Cognateset_ID"] = overview["Verb_Cognateset_ID"].replace(repl_dic)
overview = overview[~(overview["Cognateset_ID"] == "DETRZ+sleep")]

result = pyd.compose_paradigm(overview)
result["Lg"] = pd.Categorical([lvl[2] for lvl in result.index.str.split(".")], lg_list)
result["Orig"] = pd.Categorical(
    [lvl[0] for lvl in result.index.str.split(".")], lg_list
)
result["Form"] = [lvl[1] for lvl in result.index.str.split(".")]
temp_list = ["Orig", "Form", "Lg"]
result.set_index(temp_list, inplace=True)
result.sort_index(inplace=True, level="Lg")
result.replace({"": "–"}, inplace=True)
result.index.names = ["", "", ""]
label = "overview"

def modify_index(idx, latex=True):
    o = get_obj_str(idx[2][0])
    if idx[0] != idx[2]:
        if latex:
            return "\\quad " + print_shorthand(idx[2])
        else:
            return "    " + name_dic[idx[2]]
    else:
        if latex:
            return print_shorthand(idx[0]) + " " + "\\%s{%s}" % (o, idx[1])
        else:
            return name_dic[idx[0]] + " " + repl_latex("\\%s{%s}" % (o, idx[1]))
    return idx

result_exp = result.copy()

result.index = result.index.map(modify_index)
result_exp.index = result_exp.index.map(lambda x: modify_index(x, latex=False))

# replace cogset ids with reconstructed forms and translationsm
result.columns = [
    result.columns.map(lambda x: f"\\rc{{{cog_form_dic[x]}}}"),
    result.columns.map(lambda x: f"\\qu{{{cog_trans_dic[x]}}}"),
]

# replace cogset ids with reconstructed forms and translationsm
result_exp.columns = [
    result_exp.columns.map(lambda x: f"\**{cog_form_dic[x]}*"),
    result_exp.columns.map(lambda x: f"'{cog_trans_dic[x]}'"),
]

export_csv(
    result_exp, label, "Overview of extensions and (un-)affected verbs", keep_index=True
)

# add nice-looking checkmarks and stuff
repl_dic = {x: y["tex"] for x, y in overview_legend.items()}
result.replace(
    repl_dic,
    inplace=True,
)

legend = "\\begin{legendlist}"
for v in overview_legend.values():
    legend += f"""\\item[{v["tex"]}] {v["legend"]}
"""
legend += "\\end{legendlist}"

save_float(
    print_latex(result, keep_index=True) + legend,
    label,
    "Overview of extensions and (un-)affected verbs",
)


def m_expl(row):
    if row["Affected"] == "y":
        return int("DETRZ" in row["Verb_Cognateset_ID"])
    else:
        return int(
            "DETRZ" not in row["Verb_Cognateset_ID"]
            or row["Form"].split("-")[1][0] == "i"
        )

cond_map = {
    "yuk_j": ["ə", "e", "a"],
    "aku_k": ["ə"],
    "car_j": ["e", "ə"],
    "ppek_k": ["ə", "e"],
    "pwai_k": ["o", "e"],
    "ptir_t": ["ə", "e"],
}


def p_expl(row):
    initial = row["Form"].split("-")[1][0]
    # if row["Extension_ID"] in ["aku_k", "car_j", "yuk_j"]:
    triggers = cond_map[row["Extension_ID"]]
    if row["Affected"] == "y":
        return int(initial in triggers)
    else:
        return int(initial not in triggers)


freq_map = {
    "be": 1,
    "go": 1,
    "come": 0,  # or 0.5?
    "say": 1,
    "bathe_intr": 0,
    "go_down": 0,
}


def f_expl(row):
    aff = freq_map[row["Meaning_ID"]]
    if aff == 0.5:
        return 1
    if row["Affected"] == "y":
        if aff == 0:
            return 1
        elif aff == 1:
            return 0
    else:
        return aff


affectedness["morphological"] = affectedness.apply(m_expl, axis=1)
affectedness["phonological"] = affectedness.apply(p_expl, axis=1)
affectedness["frequency"] = affectedness.apply(f_expl, axis=1)
affectedness.drop(columns=["Verb_Cognateset_ID", "Concept", "Meaning_ID"], inplace=True)


def format_exp(f):
    if float(f).is_integer():
        return str(int(f))
    else:
        return str(int(f)) + "-" + str(int(f) + 1)


def get_ratio(x, factor):
    return f"{format_exp(x[factor].sum())}/{str(len(x))}"


def get_perc(x, factor):
    return x[factor].sum() / len(x)


def get_print(x, factor):
    return get_ratio(x, factor) + " ({:.0%})".format(get_perc(x, factor))


affected_result = pd.DataFrame()

for factor in ["morphological", "phonological", "frequency"]:
    affected_result[factor] = affectedness.groupby("Extension_ID").apply(
        get_print, factor
    )

caption = "Proportion of (un-)affected verbs accurately predicted by potential factors"
label = "factors"

affected_result["Language_ID"] = affected_result.index.map(ext_lg_dic)
sort_lg(affected_result)
affected_result.drop(columns=["Language_ID"], inplace=True)

aff_export = affected_result.copy()
aff_export.index = aff_export.index.map(lambda x: extension_string(x, latex=False))
export_csv(aff_export, label, caption, keep_index=True)

affected_result.index = affected_result.index.map(extension_string)
affected_result.index.name=None

save_float(
    print_latex(affected_result, keep_index=True),
    label,
    caption,
)

# #forms illustrating Sa vs Sp verbs
dv_df = pd.read_csv("../data/split_s_data.csv")
dv_df["Language"] = dv_df["Language_ID"].map(print_shorthand)
dv_df["String"] = dv_df.apply(combine_form_meaning, axis=1)
pyd.content_string = "String"
pyd.x = ["Class"]
pyd.y = ["Language"]
pyd.z = []
pyd.x_sort = ["S_A_", "S_P_"]
pyd.y_sort = list(map(print_shorthand, lg_list))

# participles
pyd.filters = {"Construction": ["PTCP"]}
emp = ["o-", "w-"]
res = pyd.compose_paradigm(dv_df)
for em in emp:
    res["S_A_"] = res["S_A_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
res["S_A_"] = res["S_A_"].str.replace("\emp{o-}se", "o-se", regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(
    print_latex(res, keep_index=True),
    "participles",
    "Participles of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
    short="Participles of \gl{s_a_} and \gl{s_p_} verbs",
)

# nominalizations
pyd.filters = {"Construction": ["NMLZ"]}
emp = {"-u-": "-\\emp{u-}", "w-": "\\emp{w-}"}
res = pyd.compose_paradigm(dv_df)
for em, em1 in emp.items():
    res["S_A_"] = res["S_A_"].str.replace(em, em1, regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(
    print_latex(res, keep_index=True),
    "nominalizations",
    "Nominalizations of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
    short="Nominalizations of \gl{s_a_} and \gl{s_p_} verbs",
)

# imperatives
pyd.filters = {"Construction": ["IMP"]}
emp = ["oj-", "o-", "ə-", "əw-", "aj-"]
res = pyd.compose_paradigm(dv_df)
for em in emp:
    res["S_P_"] = res["S_P_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(
    print_latex(res, keep_index=True),
    "imperatives",
    "Imperatives of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
    short="Imperatives of \gl{s_a_} and \gl{s_p_} verbs",
)
pyd.content_string = "Form"

with open("data_output/metadata.json", "w") as outfile:
    json.dump(exported_tables, outfile, indent=4)
