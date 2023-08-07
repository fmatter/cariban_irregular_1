import cariban_helpers as cah
import pandas as pd

pd.options.mode.chained_assignment = None
import pynterlinear as pynt
from segments import Tokenizer, Profile

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

name_dic = {x: cah.get_name(x) for x in lg_list}

ext_lg_dic = {x: y for x, y in dict(zip(e_df["ID"], e_df["Language_ID"])).items()}
ext_form_dic = {x: y for x, y in dict(zip(e_df["ID"], e_df["Form"])).items()}

trans_dic = {x: "\\qu{%s}" % y for x, y in mean_dic.items()}
plain_trans_dic = {x: "'%s'" % y for x, y in mean_dic.items()}

concept_dic = {
    "DETRZ1+bathe_1": "bathe_intr",
    "DETRZ+come": "come",
    "DETRZ1": "bathe_intr",
    "DETRZ": "come",
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
cog_form_dic["come"] = "(ət-)epɨ"
cog_trans_dic["bathe_intr"] = r"bathe"
cog_trans_dic["be_1"] = r"be-1"
cog_trans_dic["be_2"] = r"be-2"

cog_meaning_dic = dict(zip(cog_verb_df["ID"], cog_verb_df["ID"]))
cog_meaning_dic["DETRZ1+bathe_1"] = "bathe_intr"
cog_meaning_dic["DETRZ+come"] = "come"
