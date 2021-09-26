import pyradigms as pyd
import pandas as pd
        
df = pd.read_csv("../data/irregular_verb_data.csv")

lg_list = ["PWai", "wai", "hix", "PPek", "PXin", "ara", "ikp", "bak", "PTir", "aku", "tri", "car", "yuk"]
for i in ["PWai", "PPek", "PXin", "PTir"]:
    lg_list.remove(i)
    
pyd.x = ["Cognateset_ID"]
pyd.y = ["Language_ID"]
pyd.z = []
verb_list = ["come-1", "go", "say", "go.down", "be-1", "be-2"]
pyd.y_sort = lg_list
pyd.filters = {"Inflection": ["1"], "Cognateset_ID": verb_list, "Language_ID": lg_list}
# pyd.content_string = "Prefix_Cognateset_ID"
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
