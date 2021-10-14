import pyradigms as pyd
import pandas as pd
pd.options.mode.chained_assignment = None
import cariban_helpers as cah
import cldf_helpers as cldfh
import pynterlinear as pynt

lg_list = cah.lg_order().keys()
cognate_list = ["go", "say", "come", "be-1", "be-2", "go.down", "bathe"]
cs_df = pd.read_csv("../data/cognate_sets.csv")
v_df = pd.read_csv("../data/verb_stem_data.csv")

#functions for creating latex tables

def print_latex(df, ex=False, keep_index=False):
    if keep_index:
        df.columns.name = df.index.name
    df.index.name = None
    with pd.option_context("max_colwidth", 1000):
        lines = df.to_latex(escape=False).split("\n")
    lines[0] = lines[0].replace("tabular}{l", "tabular}[t]{@{}l").replace("l}", "l@{}}")
    if ex:
        del lines[1:4]
        del lines[-1]
        del lines[-2]
        return "\n".join(lines)
    else:
        return "\n".join(lines).replace(u"\toprule", u"\mytoprule")
        
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
            if i > 0: obj_string = "obj"
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

def print_shorthand(abbrev):
    return "\\" + cah.get_shorthand(abbrev)

#compile overview of individual cognate sets
def print_cognate_table(df, verb, print_class=False):
    #filter by verb
    df_v = df[df["Cognateset_ID"] == verb]
    #get bib references
    df_v["Source"] = df_v["Source"].fillna("")
    src = list(df_v["Source"])
    if "" in src:
        src.remove("")
    sources = cldfh.cite_a_bunch(src, parens=True)
    #sort by language
    df_v.Language_ID = df_v.Language_ID.astype("category")
    df_v.Language_ID.cat.set_categories(lg_list)
    df_v.sort_values(["Language_ID"], inplace=True)
    if print_class:
        #print verb with class
        fields = ["Language_ID", "Form", "Class"]
        print(df_v[fields].to_string(index=False))
        df_v["Class"] = df_v.apply(lambda x: pynt.get_expex_code(x["Class"]) if x["Class"] not in ["?", "–"] else x["Class"], axis=1)
        df_v["Form"] = df_v.apply(lambda x: objectify(x["Form"], "rc") if x["Language_ID"][0] == "P" else objectify(x["Form"]), axis=1)
        df_v["Form"] = df_v.apply(lambda x: "(" + x["Form"] + ")" if x["Cog_Cert"]<1 else x["Form"], axis=1)
    else:
        #print only forms, concatenate different reflexes of the same cognate set
        fields = ["Language_ID", "Form"]
        print(df_v[fields].to_string(index=False))
        df_v["Form"] = df_v.apply(lambda x: objectify(x["Form"], "rc") if x["Language_ID"][0] == "P" else objectify(x["Form"]), axis=1)
        df_v["Form"] = df_v.apply(lambda x: "(" + x["Form"] + ")" if x["Cog_Cert"]<1 else x["Form"], axis=1)
        df_v = df_v.groupby("Language_ID")["Form"].agg(", ".join).reset_index()
        df_v = df_v[~(pd.isnull(df_v["Form"]))]
    # object language representation with parentheses for uncertain or partial cognates
    # convert IDs to shorthand
    df_v["Language_ID"] = df_v["Language_ID"].apply(print_shorthand)
    df_v = df_v[fields]
    df_v.rename(columns={"Language_ID": "Language"}, inplace=True)
    df_v.set_index("Language", drop=True, inplace=True)
    return print_latex(df_v, keep_index=True), sources

# class-switching verbs
print("\nClass membership of 'to go down':")
tabular, sources = print_cognate_table(v_df, "go.down", print_class=True)
save_float(tabular, "godown", r"Reflexes of \rc{ɨpɨtə} \qu{to go down} " + sources, short=r"Reflexes of \rc{ɨpɨtə} \qu{to go down}")

print("\nClass membership of 'to defecate':")
tabular, sources = print_cognate_table(v_df, "defecate", print_class=True)
save_float(tabular, "defecate", r"\rc{weka} \qu{to defecate} as another class-switching \gl{s_p_} verb " + sources, short=r"\rc{weka} \qu{to defecate} as another class-switching \gl{s_p_} verb")

print("\n(Partial) cognates of 'to come':")
# 'to come'
tabular, sources = print_cognate_table(v_df, "come")
save_float(tabular, "come", r"Reflexes of \qu{to come} " + sources, short=r"Reflexes of \qu{to come}")

# comparison of intransitive and transitive 'to bathe'
df_b = pd.read_csv("../data/bathe_data.csv")
sources = cldfh.cite_a_bunch(list(df_b["Source"]), parens=True)
df_b.drop(columns=["Source", "Cognateset_ID"], inplace=True)
df_b["Form"] = df_b["Form"].apply(objectify)
pyd.x = ["Transitivity"]
pyd.y = ["Language_ID"]
pyd.y_sort = lg_list
pyd.x_sort = ["TR", "INTR"]
table = pyd.compose_paradigm(df_b)
table.index = table.index.map(print_shorthand)
table.index.name = "Language"
table.columns = table.columns.map(pynt.get_expex_code)
save_float(print_latex(table, keep_index=True), "bathe", "Transitive and intransitive \qu{to bathe} " + sources, short="Transitive and intransitive \qu{to bathe}")


#overview of what extensions affected what verbs
e_df = pd.read_csv("../data/extensions.csv")
i_df = pd.read_csv("../data/inflection_data.csv")
i_df = i_df[i_df["Inflection"] == "1"]
verb_list = ["say", "go", "be-1", "be-2", "come", "go down", "bathe"]


#determine whether verb was affected by extensions based on cognacy of prefixes
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

#extensions that happened in proto-languages sometimes go further in daughter languages
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

#format for latex
# rename index
def modify_index(idx):
    if idx[2][0] == "P":
        o = "rc"
    else:
        o = "obj"
    if idx[0] != idx[2]:
        return "\\quad " + print_shorthand(idx[2])
    else:
        return print_shorthand(idx[0]) + " " + "\\%s{%s}" % (o, idx[1])
    return idx


result.index = result.index.map(modify_index)

# replace cogset ids with reconstructed forms and translations
t_d = dict(zip(cs_df["ID"], cs_df["Gloss"]))
f_d = dict(zip(cs_df["ID"], cs_df["Form"]))
result.columns = [
    result.columns.map(lambda x: f"\\rc{{{f_d[x]}}}"),
    result.columns.map(lambda x: f"\\qu{{{t_d[x]}}}"),
]

# add nice-looking checkmarks and stuff
result.replace({"n": "×", "y": "\checkmark", "(y)": "(\\checkmark)"}, inplace=True)

save_float(print_latex(result), "overview", "Overview of extensions and (un-)affected verbs")

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

#participles
pyd.filters={"Construction": ["PTCP"]}
emp = ["o-", "w-"]
res = pyd.compose_paradigm(dv_df)
for em in emp:
    res["S_A_"] = res["S_A_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
res["S_A_"] = res["S_A_"].str.replace("\emp{o-}se", "o-se", regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(print_latex(res, keep_index=True), "participles", "Participles of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Participles of \gl{s_a_} and \gl{s_p_} verbs")

#nominalizations
pyd.filters={"Construction": ["NMLZ"]}
emp = {"-u-": "-\\emp{u-}", "w-": "\\emp{w-}"}
res = pyd.compose_paradigm(dv_df)
for em, em1 in emp.items():
    res["S_A_"] = res["S_A_"].str.replace(em, em1, regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(print_latex(res, keep_index=True), "nominalizations", "Nominalizations of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Nominalizations of \gl{s_a_} and \gl{s_p_} verbs")

#imperatives
pyd.filters={"Construction": ["IMP"]}
emp = ["oj-", "o-", "ə-", "əw-", "aj-"]
res = pyd.compose_paradigm(dv_df)
for em in emp:
    res["S_P_"] = res["S_P_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
res.columns = res.columns.map(pynt.get_expex_code)
save_float(print_latex(res, keep_index=True), "imperatives", "Imperatives of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df), short="Imperatives of \gl{s_a_} and \gl{s_p_} verbs")