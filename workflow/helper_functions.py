from read_data import *
import re
import pyradigms as pyd
import cldf_helpers as cldfh
import warnings
import json
import numpy as np
from lingpy_alignments import calculate_alignment

warnings.filterwarnings("ignore")

def print_shorthand(abbrev):
    return "\\" + cah.get_shorthand(abbrev)

shorthand_dic = {x: print_shorthand(x) for x in lg_list}

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
def print_latex(df, ex=False, keep_index=False, formatters=None, multicolumn=False, float_format=None):
    if keep_index:
        df.columns.name = df.index.name
        df.index.name = None

    with pd.option_context("max_colwidth", 1000):
        lines = df.to_latex(
            escape=False, index=keep_index, formatters=formatters, multicolumn=multicolumn,float_format=float_format
        ).split("\n")
    lines[0] = lines[0].replace("tabular}{l", "tabular}[t]{@{}l").replace("l}", "l@{}}")
    if ex:
        del lines[1:4]
        del lines[-1]
        del lines[-2]
        return "\n".join(lines)
    else:
        return "\n".join(lines).replace(r"\toprule", "\mytoprule").replace(r"\midrule", "\mymidrule").replace(r"\bottomrule", "\mybottomrule").replace("%", "\\%")


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
    unit_count = 0
    for entry in entry_list:
        out_list = []
        morph_list = entry.split("; ")
        for i, morph in enumerate(morph_list):
            unit_count += 1
            out_list.append(r"\%s{%s}" % (obj_string, morph))
            if unit_count > 0:
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
    out = form + " " + meaning.replace("_", " ")
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

web_checkmarks = {
    1: "✓",
    0: "×",
    True: "✓",
    False: "×",
    "\\checkmark": "✓",
    "×": "×"
}

def repl_latex(string):
    string = re.sub(r"\\rc\{(.*?)\}", r"\**\1*", string)
    string = re.sub(r"\\gl\{(.*?)\}", upper_repl, string)
    string = re.sub(r"\\obj\{(.*?)\}", r"*\1*", string)
    string = re.sub(r"\\qu\{(.*?)\}", r"'\1'", string)
    string = re.sub(r"\\envr\{\}\{(.*?)\}", r"/ _\1", string)
    return string
    
def delatexify(string):
    string = re.sub(r"\\rc\{(.*?)\}", r"\1", string)
    string = re.sub(r"\\gl\{(.*?)\}", upper_repl, string)
    string = re.sub(r"\\obj\{(.*?)\}", r"\1", string)
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


def get_verb_citation(v_id, l_id, latex=True, as_tuple=False):
    res = v_df[(v_df["Cognateset_ID"] == v_id) & (v_df["Language_ID"] == l_id)]
    if len(res) == 0:
        res = {"Form": "əturu", "Parameter_ID": "talk"}
        # raise ValueError(f"No verb entry for {l_id} {v_id}")
    else:
        res = res.iloc[0]
    form = res["Form"].replace("+", "")
    if latex:
        obj, gloss = f"""\\{get_obj_str(l_id)}{{{form}}}""", f"""\\qu{{{mean_dic[res["Parameter_ID"]].replace("to ", "")}}}"""
    else:
        obj, gloss = f"""{form}""",  f"""'{mean_dic[res["Parameter_ID"]]}'"""
    if as_tuple:
        return (obj, gloss)
    else:
        return obj + " " + gloss

def extension_string(id, latex=True):
    form = objectify(ext_form_dic[id], obj_string=get_obj_str(ext_lg_dic[id]))
    if latex:
        return print_shorthand(ext_lg_dic[id]) + " " + form
    else:
        return name_dic[ext_lg_dic[id]] + " " + repl_latex(form)

def reconstructed_form_table(lgs, proto, verbs, caption, name):
    pyd.x = ["Language_ID"]
    pyd.y = ["Concept"]
    pyd.filters = {"Inflection": ["1"], "Language_ID": lgs, "Concept": verbs}
    pyd.x_sort = lgs
    pyd.y_sort = ["be_1", "be_2", "say", "go", "come", "go_down", "bathe_intr"]
    tabular = pyd.compose_paradigm(i_df.replace({"go_down+?": "go_down"}))
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
        df.replace({"Language_ID": name_dic}).rename(
            columns={"Language_ID": "Language"}
        ),
        verb,
        repl_latex(caption),
        sources=raw_sources,
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

exported_tables = {}

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



def export_csv(
    tabular,
    label,
    caption=None,
    keep_index=False,
    sources=None,
    print_i_name=False,
    print_c_name=False,
    float_format=None
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
    tabular.to_csv(f"data_output/{label}.csv", index=keep_index, float_format=float_format)
    exported_tables[label] = {"caption": caption}
    if sources:
        src = cldfh.combine_refs(sources)
        # print("(" + ", ".join(src) + ")")
        exported_tables[label]["sources"] = src