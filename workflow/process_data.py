import pyradigms as pyd
import warnings

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
v_df.rename(columns={"Meaning": "Parameter_ID"}, inplace=True)
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

# cs_df["Gloss"] = cs_df["Meaning"].replace(" ", ".")
cog_verb_df = cs_df[~(cs_df["Form"].str.contains("-"))]
cog_trans_dic = dict(zip(cog_verb_df["ID"], cog_verb_df["Meaning"]))
cog_form_dic = dict(zip(cog_verb_df["ID"], cog_verb_df["Form"]))
cog_form_dic["bathe_intr"] = "e-pɨ"
cog_form_dic["come"] = "(ət-)jəpɨ"
cog_trans_dic["bathe_intr"] = r"bathe"
cog_trans_dic["be_1"] = r"be-1"
cog_trans_dic["be_2"] = r"be-2"


def str2numcog(cogsets):
    return " ".join([cognum[x] for x in cogsets.split("+")])


def num2strcog(cogids):
    return "+".join([numcog[i] for i in cogids.split(" ")])


def segmentify(form):
    form = re.sub("[()\[\]]", "", form)
    form = form.replace("-", "+")
    form = form.strip("+")
    return t(form)


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
        return "\n".join(lines).replace(r"\toprule", "\mytoprule")


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
        return ref_list
    source_string = cldfh.cite_a_bunch(ref_list, parens=parens)
    return source_string


def sort_lg(df):
    df.Language_ID = df.Language_ID.astype("category")
    df.Language_ID.cat.set_categories(lg_list, ordered=True, inplace=True)
    df.sort_values(["Language_ID"], inplace=True)


def print_shorthand(abbrev):
    return "\\" + cah.get_shorthand(abbrev)


shorthand_dic = {x: print_shorthand(x) for x in lg_list}


def extract_sources(df, src_str="Source", keep=False):
    df[src_str] = df[src_str].fillna("")
    src = list(df[src_str])
    if "" in src:
        src.remove("")
    sources = cldfh.cite_a_bunch(src, parens=True)
    if not keep:
        df.drop(columns=[src_str], inplace=True)
    return sources


def get_obj_str(lg):
    if lg[0] == "P":
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


def reconstructed_form_table(lgs, proto, verbs, caption, name):
    print(f"Irregular {cah.get_name(proto)} verbs:")
    pyd.x = ["Language_ID"]
    pyd.y = ["Concept"]
    pyd.filters = {"Inflection": ["1"], "Language_ID": lgs, "Concept": verbs}
    pyd.x_sort = lgs
    pyd.y_sort = verbs
    tabular = pyd.compose_paradigm(i_df)
    sources = get_sources(i_df)
    tabular.index.name = None
    print(tabular)

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

lgs = ["PWai", "hix", "wai"]
verbs = ["say", "be_1", "be_2", "go"]
reconstructed_form_table(
    lgs,
    "PWai",
    verbs,
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PWai",
    "pwaiverbs",
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
akuverbs["Meaning"] = akuverbs["Meaning"].map(mean_dic)
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
    r"\akuriyo \gl{1}\gl{s_a_} markers in Gildea's fieldnotes " + sources,
    short=r"\akuriyo \gl{1}\gl{s_a_} markers in Gildea's fieldnotes",
)

# regular proto-waiwaian verbs
meanings = ["fall", "sleep"]
lgs = ["PWai", "hix", "wai"]
pyd.x = ["Meaning", "Language_ID"]
pyd.y = ["Inflection"]
pyd.filters = {"Language_ID": lgs, "Meaning": meanings}
pyd.sort_orders = {
    "Language_ID": lgs,
    "Meaning": meanings,
    "Inflection": ["1", "2", "1+2", "3"],
}
tabular = pyd.compose_paradigm(i_df, multi_index=True)
sources = get_sources(i_df)

print(tabular)

tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[1])))
tabular.rename(
    columns={"sleep": r"\qu{to sleep} (\gl{s_p_})", "fall": "\qu{to fall} (\gl{s_a_})"},
    level="Meaning",
    inplace=True,
)
tabular.rename(columns=shorthand_dic, level="Language_ID", inplace=True)
tabular.index = tabular.index.map(pynt.get_expex_code)
tabular.index.names = [None]
tabular.columns.names = [None, None]
save_float(
    print_latex(tabular, keep_index=True),
    "pwaireg",
    "Regular \PWai verbs " + sources,
    short="Regular \PWai verbs",
)

# regular proto-tiriyoan verbs
tir_reg = i_df[~(pd.isnull(i_df["Verb_Cognateset_ID"]))]
meanings = ["bathe_intr", "sleep"]
lgs = ["PTir", "tri", "aku"]
pyd.filters = {"Language_ID": lgs, "Meaning": meanings}
pyd.sort_orders = {
    "Language_ID": lgs,
    "Meaning": meanings,
    "Inflection": ["1", "2", "1+2", "3"],
}
tabular = pyd.compose_paradigm(tir_reg, multi_index=True)
sources = get_sources(tir_reg)

print(tabular)

tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[1])))

tabular.rename(columns=trans_dic, level="Meaning", inplace=True)
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


# regular pekodian verbs
tabular = pd.DataFrame()
sources = []
pyd.x = ["Language_ID", "Meaning"]
for lg, meaning in {"bak": "go_up", "ara": "dance", "ikp": "run"}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning": [meaning]}
    pyd.sort_orders = {"Inflection": ["1", "2", "1+2", "3"]}
    temp = pyd.compose_paradigm(i_df, multi_index=True)
    sources.extend(get_sources(i_df, latexify=False))
    tabular = pd.concat([tabular, temp], axis=1)

print(tabular)

sources = cldfh.cite_a_bunch(sources)
tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name[1])))

tabular.rename(columns=trans_dic, level="Meaning", inplace=True)
tabular.rename(columns=shorthand_dic, level="Language_ID", inplace=True)

tabular.index = tabular.index.map(pynt.get_expex_code)
tabular.index.names = [None]
tabular.columns.names = [None, None]
save_float(
    print_latex(tabular, keep_index=True),
    "pekreg",
    "Regular Pekodian \gl{s_a_} verbs " + sources,
    short="Regular Pekodian \gl{s_a_} verbs",
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
print(tabular)
sources = get_sources(forms)
tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name)))
tabular.columns = tabular.columns.map(print_shorthand)

tabular.index.name = "Meaning"
tabular.reset_index(inplace=True)
tabular["Meaning"] = tabular["Meaning"].map(mean_dic)
tabular["Meaning"] = tabular["Meaning"].map(lambda x: "\\qu{" + x + "}")

save_float(
    print_latex(tabular),
    "pxinw",
    r"Loss of \rc{w} in \ikpeng " + sources,
    short=r"Loss of \rc{w} in \ikpeng",
)
pyd.filters = {}

# prepare overviews of class-switching 'go down' and 'defecate'
print("\nClass membership of 'to go down':")
gd_df = v_df[v_df["Parameter_ID"] == "go_down"]
sources = extract_sources(gd_df)

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
print(gd_df)
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
    "godown",
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
        sources = extract_sources(df)
    df["Segments"] = df.apply(lambda x: segmentify(x["Form"]), axis=1)
    df["Cognateset_ID"] = df["Cognateset_ID"].map(str2numcog)
    df = calculate_alignment(df, fuzzy=fuzzy)
    df = df[fields]
    sort_lg(df)
    for i, col in enumerate(df.columns):
        if col == "":
            df.columns.values[i] = "Alignment"
            break
    df["Form"] = df["Form"].str.replace("+", "", regex=True)
    print(f"Comparative table for 'to {verb}'")
    print(df)
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
    caption=r"Reflexes of \qu{to come}",
    fuzzy=True,
)
print_aligned_table(
    v_df[v_df["Parameter_ID"] == "go"],
    verb="go",
    caption=r"Reflexes of \rc{ɨtə(mə)} \qu{to go}",
)
print_aligned_table(
    v_df[v_df["Parameter_ID"] == "say"],
    verb="say",
    caption=r"Reflexes of \rc{ka(ti)} \qu{to say}",
)

# comparison of intransitive and transitive 'to bathe'
df_b = pd.read_csv("../data/bathe_data.csv")
df_b["Parameter_ID"] = df_b["Transitivity"].apply(lambda x: "bathe" + "_" + x.lower())
df_b.drop(columns=["Transitivity"], inplace=True)
df_b.index = df_b.index + 1
sources = extract_sources(df_b)
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
\caption{Comparison of intransitive and transitive \qu{to bathe} %s}
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
"""
    if table[2] == "bathe_tr_1":
        bathe_out += r"""\end{subtable}
\begin{subtable}[t]{.49\linewidth}"""
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

# alternative table with transitive and intransitive forms juxtaposed
# sources = extract_sources(df_b)
# df_b.drop(columns=["Cognateset_ID"], inplace=True)
# df_b["Form"] = df_b["Form"].str.replace("+", "")
# df_b["Form"] = df_b["Form"].apply(objectify)
# pyd.x = ["Transitivity"]
# pyd.y = ["Language_ID"]
# pyd.y_sort = lg_list
# pyd.x_sort = ["TR", "INTR"]
# table = pyd.compose_paradigm(df_b)
# table.index = table.index.map(print_shorthand)
# table.index.name = "Language"
# table.columns = table.columns.map(pynt.get_expex_code)
# save_float(print_latex(table, keep_index=True), "bathe", "Transitive and intransitive \qu{to bathe} " + sources, short="Transitive and intransitive \qu{to bathe}")

# overview of what extensions affected what verbs
i_df = i_df[i_df["Inflection"] == "1"]
verb_list = ["say", "go", "be_1", "be_2", "come", "go_down", "bathe_intr"]

# determine whether verb was affected by extensions based on cognacy of prefixes
def identify_affected(cogset, value):
    if value in ["?", "–"]:
        return value
    elif pd.isnull(value):
        return "–"
    else:
        if cogset == value:
            return "y"
        elif cogset in value.split("+"):
            return "(y)"
        else:
            return "n"


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
        t_df["Form"] = row["Form"]
        t_df["Orig_Language"] = row["Language_ID"]
        t_df["Affected"] = t_df.apply(
            lambda x: identify_affected(
                row["Cognateset_ID"], x["Prefix_Cognateset_ID"]
            ),
            axis=1,
        )
        t_df.drop(
            columns=[
                "Source",
                "Prefix_Cognateset_ID",
                "Inflection",
                "Full_Form",
                "Comment",
            ],
            inplace=True,
        )
        overview = overview.append(t_df)


pyd.x = ["Cognateset_ID"]
pyd.y = ["Orig_Language", "Form", "Language_ID"]
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
result.replace({"n/n": "n", "n/y": "(y)", "": "–"}, inplace=True)
result.index.names = ["", "", ""]
print("\nOverview of extensions and (un-)affected verbs:")
print(result)

# format for latex
# rename index
def modify_index(idx):
    o = get_obj_str(idx[2][0])
    if idx[0] != idx[2]:
        return "\\quad " + print_shorthand(idx[2])
    else:
        return print_shorthand(idx[0]) + " " + "\\%s{%s}" % (o, idx[1])
    return idx


result.index = result.index.map(modify_index)

# replace cogset ids with reconstructed forms and translationsm
result.columns = [
    result.columns.map(lambda x: f"\\rc{{{cog_form_dic[x]}}}"),
    result.columns.map(lambda x: f"\\qu{{to {cog_trans_dic[x]}}}"),
]
# add nice-looking checkmarks and stuff
result.replace({"n": "×", "y": "\checkmark", "(y)": "(\\checkmark)"}, inplace=True)
save_float(
    print_latex(result, keep_index=True),
    "overview",
    "Overview of extensions and (un-)affected verbs",
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
