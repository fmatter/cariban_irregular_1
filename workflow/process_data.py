import pyradigms as pyd
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
segments = open("../data/segments.txt").read()
segment_list = [{"Grapheme": x, "mapping": x} for x in segments.split("\n")]
t = Tokenizer(Profile(*segment_list))
cognatesets = pd.read_csv("../data/cldf/cognatesets.csv")
cognatesets = cognatesets.append({"ID": "?", "Description": "Unknown material"}, ignore_index=True)

# lingpy does not like cogid 0
cognatesets.index = cognatesets.index + 1
cognum = dict(zip(cognatesets["ID"], cognatesets.index.astype(str)))
numcog = dict(zip(cognatesets.index.astype(str), cognatesets["ID"]))

print("Assigning cognates")


def str2numcog(cogsets):
    return " ".join([cognum[x] for x in cogsets.split("+")])


def num2strcog(cogids):
    return "+".join([numcog[i] for i in cogids.split(" ")])


def segmentify(form):
    form = re.sub("[()]", "", form)
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
        return "\n".join(lines).replace("\toprule", "\mytoprule")


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


def get_sources(df, parens=True):
    tmp = pyd.content_string
    pyd.content_string = "Source"
    table = pyd.compose_paradigm(df)
    ref_list = [j for i in table.values.tolist() for j in i]
    source_string = cldfh.cite_a_bunch(ref_list, parens=parens)
    pyd.content_string = tmp
    return source_string


def sort_lg(df):
    df.Language_ID = df.Language_ID.astype("category")
    df.Language_ID.cat.set_categories(lg_list, ordered=True, inplace=True)
    df.sort_values(["Language_ID"], inplace=True)


def print_shorthand(abbrev):
    return "\\" + cah.get_shorthand(abbrev)


def get_obj_str(lg):
    if lg[0] == "P":
        return "rc"
    else:
        return "obj"


# prepare overviews of class-switching 'go down' and 'defecate'
print("\nClass membership of 'to go down':")
gd_df = v_df[v_df["Parameter_ID"] == "go_down"]
gd_df["Source"] = gd_df["Source"].fillna("")
src = list(gd_df["Source"])
if "" in src:
    src.remove("")
sources = cldfh.cite_a_bunch(src, parens=True)
gd_df.drop(columns=["Source"], inplace=True)

grouped = gd_df.groupby(gd_df.Cog_Cert)
temp_df1 = grouped.get_group(1.0)
temp_df2 = grouped.get_group(0.5)
temp_df1["Segments"] = temp_df1.apply(lambda x: segmentify(x["Form"]), axis=1)
temp_df1["Cognateset_ID"] = temp_df1["Cognateset_ID"].map(str2numcog)
temp_df1 = calculate_alignment(temp_df1, fuzzy=True)
temp_df1["Cognateset_ID"] = temp_df1["Cognateset_ID"].map(num2strcog)
temp_df1.rename(columns={"Cognateset_ID1": "Cognateset_ID"}, inplace=True)
temp_df1["Class"] = temp_df1.apply(
    lambda x: "(" + x["Class"] + ")" if "DETRZ" in x["Cognateset_ID"] else x["Class"], axis=1
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
gd_df["Form"] = gd_df.apply(
    lambda x: objectify(x["Form"], get_obj_str(x["Language_ID"])), axis=1
)
gd_df["Language_ID"] = gd_df["Language_ID"].apply(print_shorthand)
gd_df.rename(columns={"Language_ID": "Language"}, inplace=True)
gd_df.set_index("Language", drop=True, inplace=True)
tabular = print_latex(gd_df, keep_index=True)
save_float(
    tabular,
    "godown",
    r"Reflexes of \rc{ɨpɨtə} \qu{to go down} " + sources,
    short=r"Reflexes of \rc{ɨpɨtə} \qu{to go down}",
)

# print("\nClass membership of 'to defecate':")

# come_aligned = pd.read_csv("../data/comp_tables/come.csv", keep_default_na=False)
# # columns = pd.DataFrame(come_aligned.columns.tolist())
# # columns.loc[columns[0].str.startswith('Unnamed:'), 0] = np.nan
# # come_aligned.columns = pd.MultiIndex.from_tuples(columns.to_records(index=False).tolist())

# print("\n(Partial) cognates of 'to come':")
# come_aligned["Language_ID"] = come_aligned["Language_ID"].astype("category")
# come_aligned["Language_ID"].cat.set_categories(lg_list, ordered=True, inplace=True)
# come_aligned.sort_values(["Language_ID"], inplace=True)
# come_aligned["Language_ID"] = come_aligned["Language_ID"].map(print_shorthand)
# come_aligned["Form"] = come_aligned["Form"].map(objectify)
# come_aligned.rename(columns={"Language_ID": "Language", "Form": "Form", "Unnamed: 3": "Alignment"}, inplace=True)
# come_aligned.rename(columns=lambda x: re.sub(r"Unnamed: [\d]","",x), inplace=True)


# sources = list(come_aligned["Source"])
# sources = cldfh.cite_a_bunch(sources, parens=True)
# come_aligned.drop(columns=["Source"], inplace=True)
# save_float(print_latex(come_aligned), "come", r"Reflexes of \qu{to come} " + sources, short=r"Reflexes of \qu{to come}")


# # comparison of intransitive and transitive 'to bathe'
# df_b = pd.read_csv("../data/bathe_data.csv")
# sources = cldfh.cite_a_bunch(list(df_b["Source"]), parens=True)
# df_b.drop(columns=["Source", "Cognateset_ID"], inplace=True)
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


# #overview of what extensions affected what verbs
# e_df = pd.read_csv("../data/extensions.csv")
# i_df = pd.read_csv("../data/inflection_data.csv")
# i_df = i_df[i_df["Inflection"] == "1"]
# verb_list = ["say", "go", "be-1", "be-2", "come", "go down", "bathe (INTR)"]

# #determine whether verb was affected by extensions based on cognacy of prefixes
# def identify_affected(cogset, value):
#     if value in ["?", "–"]:
#         return value
#     elif pd.isnull(value):
#         return "–"
#     else:
#         if cogset == value:
#             return "y"
#         elif cogset in value.split("+"):
#             return "(y)"
#         else:
#             return "n"

# #extensions that happened in proto-languages sometimes go further in daughter languages
# daughters = {
#     "PWai": ["wai", "hix"],
#     "PTir": ["tri", "aku"],
#     "PPek": ["ara", "ikp", "bak"],
# }

# overview = pd.DataFrame()
# for i, row in e_df.iterrows():
#     if row["Language_ID"] in daughters:
#         lgs = [row["Language_ID"]] + daughters[row["Language_ID"]]
#     else:
#         lgs = [row["Language_ID"]]
#     for lg in lgs:
#         t_df = i_df[i_df["Language_ID"] == lg]
#         t_df["Form"] = row["Form"]
#         t_df["Orig_Language"] = row["Language_ID"]
#         t_df["Affected"] = t_df.apply(
#             lambda x: identify_affected(
#                 row["Cognateset_ID"], x["Prefix_Cognateset_ID"]
#             ),
#             axis=1,
#         )
#         t_df.drop(
#             columns=[
#                 "Source",
#                 "Prefix_Cognateset_ID",
#                 "Inflection",
#                 "Full_Form",
#                 "Comment",
#             ],
#             inplace=True,
#         )
#         overview = overview.append(t_df)

# pyd.x = ["Cognateset_ID"]
# pyd.y = ["Orig_Language", "Form", "Language_ID"]
# pyd.content_string = "Affected"
# pyd.x_sort = verb_list
#
# repl_dic = {
#     "DETRZ+come": "come"
# }
#
# overview["Cognateset_ID"] = overview["Cognateset_ID"].replace(repl_dic)
#
# result = pyd.compose_paradigm(overview)
# result["Lg"] = pd.Categorical([lvl[2] for lvl in result.index.str.split(".")], lg_list)
# result["Orig"] = pd.Categorical(
#     [lvl[0] for lvl in result.index.str.split(".")], lg_list
# )
# result["Form"] = [lvl[1] for lvl in result.index.str.split(".")]
# temp_list = ["Orig", "Form", "Lg"]
# result.set_index(temp_list, inplace=True)
# result.sort_index(inplace=True, level="Lg")
# result.replace({"n/n": "n", "n/y": "(y)", "": "–"}, inplace=True)
# result.index.names = ["", "", ""]
# print("\nOverview of extensions and (un-)affected verbs:")
# print(result)
#
# #format for latex
# # rename index
# def modify_index(idx):
#     if idx[2][0] == "P":
#         o = "rc"
#     else:
#         o = "obj"
#     if idx[0] != idx[2]:
#         return "\\quad " + print_shorthand(idx[2])
#     else:
#         return print_shorthand(idx[0]) + " " + "\\%s{%s}" % (o, idx[1])
#     return idx
#
#
# result.index = result.index.map(modify_index)
#
# # replace cogset ids with reconstructed forms and translationsm
# cs_df["Gloss"] = cs_df["Meaning"].replace(" ", ".")
# t_d = dict(zip(cs_df["ID"], cs_df["Gloss"]))
# f_d = dict(zip(cs_df["ID"], cs_df["Form"]))
#
# result.columns = [
#     result.columns.map(lambda x: f"\\rc{{{f_d[x]}}}"),
#     result.columns.map(lambda x: f"\\qu{{to {t_d[x]}}}"),
# ]
#
# # add nice-looking checkmarks and stuff
# result.replace({"n": "×", "y": "\checkmark", "(y)": "(\\checkmark)"}, inplace=True)
#
# save_float(print_latex(result), "overview", "Overview of extensions and (un-)affected verbs")
#
# # #forms illustrating Sa vs Sp verbs
# dv_df = pd.read_csv("../data/split_s_data.csv")
# dv_df["Language"] = dv_df["Language_ID"].map(print_shorthand)
# dv_df["String"] = dv_df.apply(combine_form_meaning, axis=1)
# pyd.content_string = "String"
# pyd.x = ["Class"]
# pyd.y = ["Language"]
# pyd.z = []
# pyd.x_sort = ["S_A_", "S_P_"]
# pyd.y_sort = list(map(print_shorthand, lg_list))
#
# #participles
# pyd.filters={"Construction": ["PTCP"]}
# emp = ["o-", "w-"]
# res = pyd.compose_paradigm(dv_df)
# for em in emp:
#     res["S_A_"] = res["S_A_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
# res["S_A_"] = res["S_A_"].str.replace("\emp{o-}se", "o-se", regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(print_latex(res, keep_index=True), "participles", "Participles of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Participles of \gl{s_a_} and \gl{s_p_} verbs")
#
# #nominalizations
# pyd.filters={"Construction": ["NMLZ"]}
# emp = {"-u-": "-\\emp{u-}", "w-": "\\emp{w-}"}
# res = pyd.compose_paradigm(dv_df)
# for em, em1 in emp.items():
#     res["S_A_"] = res["S_A_"].str.replace(em, em1, regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(print_latex(res, keep_index=True), "nominalizations", "Nominalizations of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Nominalizations of \gl{s_a_} and \gl{s_p_} verbs")
#
# #imperatives
# pyd.filters={"Construction": ["IMP"]}
# emp = ["oj-", "o-", "ə-", "əw-", "aj-"]
# res = pyd.compose_paradigm(dv_df)
# for em in emp:
#     res["S_P_"] = res["S_P_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(print_latex(res, keep_index=True), "imperatives", "Imperatives of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Imperatives of \gl{s_a_} and \gl{s_p_} verbs")
