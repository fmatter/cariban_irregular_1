import pyradigms as pyd
import pandas as pd
import cldf_helpers
import cariban_helpers

normalfonties = ["Ø", "?", "V", "G", "C"]
def objectify(string, obj_string="obj"):
    if string in ["", "?", " ", "  ", "–"]:
        return string
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
        # morph_list = [r"\%s{%s}" % (obj_string, morph) for morph in morph_list]
        output.append("/".join(out_list))
    for i, cell in enumerate(output):
        if r"\env" in cell:
            output[i] = cell.replace(r"\obj", "")
    output = ", ".join(output)
    for normalfonty in normalfonties:
        output = output.replace(normalfonty, r"{\normalfont %s}" % normalfonty)
    return output

def get_sources(df, parens=True):
    pyd.content_string = "Source"
    table = pyd.compose_paradigm(df)
    ref_list = [j for i in table.values.tolist() for j in i]
    source_string = cldf_helpers.cite_a_bunch(ref_list, parens=parens)
    pyd.content_string = "Form"
    return source_string

def print_latex(df, ex=False):
    lines = df.to_latex(escape=False, index=False).split("\n")
    lines[0] = lines[0].replace("tabular}{l", "tabular}[t]{@{}l").replace("l}", "l@{}}")
    if ex:
        del lines[1:4]
        del lines[-1]
        del lines[-2]
        return "\n".join(lines)
    else:
        return "\n".join(lines).replace(u"\toprule", u"\mytoprule")
        
df = pd.read_csv("irregular_verb_data.csv")

lg_list = ["PWai", "wai", "hix", "PPek", "PXin", "ara", "ikp", "bak", "PTir", "aku", "tri", "car", "yuk"]
for i in ["PWai", "PPek", "PXin", "PTir"]:
    lg_list.remove(i)
    
sh_dict = {x : "\\" + cariban_helpers.get_shorthand(x) for x in lg_list}
lg_list = [sh_dict[x] for x in lg_list]
df["Language"] = df["Language_ID"].map(sh_dict)
pyd.x = ["Cognateset_ID"]
pyd.y = ["Language"]
pyd.z = []
verb_list = ["come-1", "go", "say", "go.down", "be-1", "be-2"]
pyd.y_sort = lg_list
pyd.filters = {"Inflection": ["1"], "Cognateset_ID": verb_list, "Language": lg_list}
table = pyd.compose_paradigm(df)
print(table)
#
# for verb in verb_list:
#     pyd.filters = {"Inflection": ["1"], "Cognateset_ID": [verb], "Language": lg_list}
#
#     table = pyd.compose_paradigm(df)
#     table = table.applymap(objectify)
#     table.columns = ["First person form"]
#     table.reset_index(inplace=True)
#     # table.index.name = ""
#     src = get_sources(df, parens=True)
#     print(print_latex(table))
#     print(src)
#     print("")
#
