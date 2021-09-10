import pandas as pd
from cariban_helpers import *
import seaborn as sns

def print_source(string):
    entries = string.split("; ")
    output = ""
    for entry in entries:
        bibkey = entry.split("[")[0]
        pages = entry.split("[")[1].replace("]","")
        if bibkey == "pc":
            return "\\perscomm{%s}" % pages
        else:
            output += "[%s]{%s}" % (pages, bibkey)
    return "\\textcites%s" % output

def shorthandify(lg_id):
    return "\\" + get_shorthand(lg_id)

def objectify(string, obj_string="obj"):
    if string in ["", "?", " ", "  "]:
        return string
    if string[0] == " ":
        return string
    out_list = []
    morph_list = string.split("; ")
    for i, morph in enumerate(morph_list):
        out_list.append(r"\%s{%s}" % (obj_string, morph))
        if i > 0: obj_string = "obj"
    return "/".join(out_list)
    
a = pd.read_csv("come_roots.csv")
# print(a)
 
a["Language_ID"] = pd.Categorical(a['Language_ID'], lg_order().keys())
a.sort_values("Language_ID", inplace=True)

a["Source"] = a["Source"].apply(print_source)
a["Form"] = a["Form"].apply(lambda x: "\obj{%s}" % x)
a["Language"] = a["Language_ID"].apply(shorthandify)

cogsets = {
    1: "jəpɨ",
    2: "əpɨ",
    3: "epɨ",
    4: "ətjəpɨ",
}

def get_palette(n):
    palette = sns.color_palette("pastel", n)
    for i, color in enumerate(palette):
        palette[i] = [str(x*255) for x in color]
    return dict(zip(range(1,len(palette)+1), palette))

colors = get_palette(len(cogsets))

cmd_out = ""
for i, j in colors.items():
    cmd_out += "\\definecolor{come%s}{RGB}{%s}\n" % (i, ",".join(j))
# print(cmd_out)

output = ""
df = a
for index, row in df.iterrows():
    row_colors = "\\colorbox{come%s}" % row["Cognateset_ID"]
    output += " & ".join([row['Language'], "%s{%s}" % (row_colors, row['Form']), row["Source"]]) + "\\\\\n"
templ = r"""\begin{table}
	\centering
	\caption{Reflexes of \qu{to come}}
    \label{tab:come}
	\begin{tabular}{@{}lll@{}}
	\mytoprule
	Language & Form & Source\\
	\mymidrule
%s\mybottomrule
	\end{tabular}
\end{table}""" % (output)
# print(templ)


from pandas_ods_reader import read_ods
path = "/Users/florianm/Dropbox/Uni/Research/LiMiTS/notes/go_comparative.ods"
bathe_df = read_ods(path, "bathe")

bathe_df["Source"] = bathe_df["src"].apply(print_source)
bathe_df["intr"] = bathe_df["intr"].apply(lambda x: objectify(x))
bathe_df["tr"] = bathe_df["tr"].apply(lambda x: objectify(x))
bathe_df["Language"] = bathe_df["lg"].apply(shorthandify)
bathe_df.drop(["lg", "src"], inplace=True, axis=1)

output = ""
for index, row in bathe_df.iterrows():
    output += " & ".join([row['Language'], row["intr"], row["tr"], row["Source"]]) + "\\\\\n"
templ = r"""\begin{table}
	\centering
	\caption{Intransitive and transitive \qu{to bathe}}
    \label{tab:bathe}
	\begin{tabular}{@{}llll@{}}
	\mytoprule
	Language & \gl{intr} & \gl{tr} & Source\\
	\mymidrule
%s\mybottomrule
	\end{tabular}
\end{table}""" % (output)
print(templ)

# print(templ)
#
# for cogset, form in cogsets.items():
#     df = a[a["Cognateset_ID"] == cogset]
#     output = ""
#     for index, row in df.iterrows():
#         output += " & ".join([row['Language'], row['Form'], row["Source"]]) + "\\\\\n"
#     templ = r"""\begin{table}
#     \centering
#     \caption{\rc{%s} \qu{to come}}
#     \label{tab:%s}
#     \begin{tabular}{@{}lll@{}}
#     \mytoprule
#     Language & Form & Source\\
#     \mymidrule
# %s\mybottomrule
#     \end{tabular}
# \end{table}""" % (form, form, output)
#     print(templ + "\n")

# import lingtypology
# df = pd.read_csv("/Users/florianm/Dropbox/Uni/Research/LiMiTS/musings/cariban_intr/come_roots.csv")
# df["Glottocode"] = df["Language_ID"].map(lambda x: get_glottocode(x))
# df.drop(["Language_ID", "Form", "Source"], axis=1, inplace=True)
#
# langfeatures = {}
#
# for row in df.itertuples():
#     if row.Glottocode not in langfeatures: langfeatures[row.Glottocode] = []
#     langfeatures[row.Glottocode].append(row.Cognateset_ID)
    
# aggr = pd.DataFrame()
# for glottocode in list(df["Glottocode"]):
#     out = {"Glottocode": glottocode}
#     for value in list(df[df["Glottocode"] == glottocode]["Cognateset_ID"].values):
#         out[value] = 1
#     aggr = aggr.append(out, ignore_index=True)
# aggr.fillna(0, inplace=True)

# print(aggr)
# languages = list(aggr.Glottocode)
# aggr.drop("Glottocode", axis=1, inplace=True)
# features_nan = aggr.values.tolist()
# features = []
# for l in features_nan:
#     l = [x for x in l if str(x) != "nan"]
#     print(l)
#     features.append(l)
# print(features)
#
# m = lingtypology.LingMap(langfeatures.keys(), glottocode=True)
# m.add_overlapping_features(list(langfeatures.values()))
# m.create_map()
# m.save('come_map.html')