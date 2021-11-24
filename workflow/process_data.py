from helper_functions import *


# tables for the introduction, featuring "regular" and "irregular" verbs from Trio and Hixkaryana
person = ["1", "2", "1+2", "3"]
pyd.x = ["Meaning_ID"]
pyd.y = ["Inflection"]
pyd.y_sort = person
for lg, meanings in {
    "hix": ["fall", "be_afraid", "walk", "cut_self", "be"],
    "tri": ["sleep", "see_self", "bathe_intr", "yawn", "go"],
    # "mak": ["eat", "arrive", "go", "be"]
    # "yuk": ["wash_self", "sleep", "fall"],
}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning_ID": meanings, "Inflection": person}
    pyd.x_sort = meanings
    tabular = pyd.compose_paradigm(
        i_df[i_df["Verb_Cognateset_ID"] != "be_1"], multi_index=False
    )
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
sources_list = []
pyd.x = ["Language_ID", "Meaning_ID"]
# no reconstructable paradigms, so we use regular Sa verbs
for lg, meaning in {"bak": "go_up", "ara": "dance", "ikp": "run"}.items():
    pyd.filters = {"Language_ID": [lg], "Meaning_ID": [meaning]}
    pyd.sort_orders = {"Inflection": person}
    temp = pyd.compose_paradigm(i_df, multi_index=True)
    sources_list.extend(get_sources(i_df, latexify=False))
    tabular = pd.concat([tabular, temp], axis=1)

sources = cldfh.cite_a_bunch(sources_list, parens=True)
label = "pekreg"
tabular.index.names = [None]
export_csv(
    tabular.rename(columns=name_dic, level="Language_ID"),
    label,
    "Regular Pekodian Sa verbs",
    keep_index=True,
    sources=sources_list,
)

tabular = tabular.apply(lambda x: x.apply(objectify, obj_string=get_obj_str(x.name)))
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

# conservative pekodian verbs
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
label = "pwaireg"

export_csv(
    tabular.rename(columns=name_dic, level="Language_ID"),
    label,
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
    label,
    "Regular \qu{to fall} (\gl{s_a_}) and \qu{to sleep} (\gl{s_p_}) in \PWai "
    + get_sources(i_df),
    short="Regular \PWai verbs",
)

# conservative proto-waiwaian verbs
verbs = ["say", "be_1", "be_2", "go"]
reconstructed_form_table(
    lgs,
    "PWai",
    verbs,
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PWai",
    "pwaiverbs",
)


# regular proto-tiriyoan verbs
label = "ptirreg"
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
    label,
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
    label,
    "Regular \PTir \gl{s_a_} verbs " + sources,
    short="Regular \PTir \gl{s_a_} verbs",
)

# conservative proto-tiriyoan verbs
reconstructed_form_table(
    ["PTir", "tri", "aku"],
    "PTir",
    ["go", "say", "come", "be_1", "be_2"],
    r"Verbs preserving \gl{1}\gl{s_a_} \rc{w-} in \PTir",
    "ptirverbs",
)

# regular akuriyo Sa verbs
label = "aku1sa"
aku_verbs = i_df[
    (i_df["Language_ID"] == "aku") & (i_df["Prefix_Cognateset_ID"].isin(["k", "1t"]))
]
aku_verbs["Form"] = aku_verbs["Form"].apply(lambda x: x.split("-", 1)[1])
aku_verbs["Meaning"] = aku_verbs["Meaning_ID"].map(mean_dic)

aku_verbs["String"] = aku_verbs.apply(combine_form_meaning, axis=1)

k_list = aku_verbs[aku_verbs["Prefix_Cognateset_ID"] == "k"]["String"].reset_index(
    drop=True
)
t_list = aku_verbs[aku_verbs["Prefix_Cognateset_ID"] == "1t"]["String"].reset_index(
    drop=True
)

raw_sources = get_sources(aku_verbs, latexify=False)
sources = extract_sources(aku_verbs)
aku_verbs = pd.DataFrame.from_dict(
    {r"first person \obj{k-}": k_list, r"first person \obj{t͡ʃ-}": t_list}
)
aku_verbs.fillna("", inplace=True)

save_float(
    print_latex(aku_verbs),
    label,
    r"Regular \akuriyo \gl{1}\gl{s_a_} markers " + sources,
    short=r"Regular \akuriyo \gl{1}\gl{s_a_} markers",
)

aku_verbs = aku_verbs.applymap(delatexify)
aku_verbs.columns = map(repl_latex, aku_verbs.columns)

export_csv(
    aku_verbs,
    label,
    "Regular Akuriyo Sa verbs",
    sources=raw_sources,
)


# regular carijo and yukpa verbs
pyd.x = ["Meaning_ID"]
pyd.y = ["Inflection"]
pyd.y_sort = person
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

# prepare overviews of class-switching 'go down' (formerly also 'to defecate')
label = "godown"
pyd.filters = {}

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

# print("\nClass membership of 'to defecate':")
# s_df = v_df[v_df["Parameter_ID"] == "defecate"]
# sources = extract_sources(s_df)
# s_df.drop(
#     columns=["Parameter_ID", "Cog_Cert", "Comment", "Cognateset_ID"], inplace=True
# )
# s_df["Form"] = s_df["Form"].str.replace("+", "", regex=True)
# sort_lg(s_df)
# print(s_df)
# s_df["Class"] = s_df.apply(
#     lambda x: pynt.get_expex_code(x["Class"])
#     if x["Class"] not in ["?", "–"]
#     else x["Class"],
#     axis=1,
# )
# add_obj_markdown(s_df)
# repl_lg_id(s_df)
# s_df.set_index("Language", drop=True, inplace=True)
# tabular = print_latex(s_df, keep_index=True)
# save_float(
#     tabular,
#     "defecate",
#     r"Reflexes of \qu{to defecate} " + sources,
#     short=r"Reflexes of \qu{to defecate} ",
# )


# various cognate segment aligned tables of individual verbs
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
    elif table[2] == "bathe_tr_1":
        bathe_out += r"""\end{subtable}
\begin{subtable}[t]{.49\linewidth}
\centering"""
    # hacky fix for aligning ye'kwana ʔ with k rather than akawaio ʔ
    elif table[2] == "bathe_intr_2":
        tabular = tabular.replace("&    &    &  ʔ", "&  ʔ &    &   ")

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


overview_legend = {
    "y": {"tex": "\checkmark", "legend": "affected"},
    "n": {"tex": "×", "legend": "not affected"},
    "?": {"tex": "?", "legend": "unknown first person prefix"},
    "–": {"tex": "–", "legend": "does not occur"},
    "(y)": {"tex": "(\\checkmark)", "legend": "old and new marker combined"},
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


# testing possible explanations using bybee's model
def predict_semantics(form):
    pass


def predict_morphology(form):
    if "DETRZ" in form["ID"] and form["Form"][0] != "i":
        return True
    else:
        return False


phon_preds = {
    "PWai": ["o", "e", "a"],
    "PTir": ["ə", "e"],
    "PPek": ["ə", "e"],
    "aku": ["ə"],
    "car": ["ə", "e"],
    "yuk": ["o", "a", "e", "i", "u"],
}


def predict_phonology(form):
    if form["Form"][0] in phon_preds[form["Language_ID"]]:
        return True
    else:
        return False
    return False


factors = {
    "Morphology": predict_morphology,
    "Phonology": predict_phonology,
    # "semantics": predict_semantics,
}

freq_df = pd.read_csv("../data/apalai_sa_verb_stats.csv")
freq_df["High_Freq"] = freq_df["% Sa"] > 0.1
frequencies = dict(zip(freq_df["ID"], freq_df["High_Freq"]))


def get_frequency_prediction(lexeme, frequencies):
    if lexeme in frequencies:
        return not frequencies[lexeme]
    else:
        return True


def test_explanations(word_form):
    explanations = {}
    for factor, factor_function in factors.items():
        actual = word_form["Affected"]
        fact_pred = factor_function(word_form)
        freq_pred = get_frequency_prediction(word_form["ID"], frequencies)
        explanations[factor] = fact_pred == actual
        explanations[factor + " + Frequency"] = (
            freq_pred == fact_pred == word_form["Affected"]
        ) or (fact_pred and not actual and not freq_pred)
    #         print(f"""Testing {word_form["Language_ID"]} {word_form["ID"]}. {factor} predicts {fact_pred}
    # frequency predicts {freq_pred}
    # reality is {actual}
    # {factor} scores {explanations[factor]}
    # {factor}+Frequency scores {explanations[factor+" + Frequency"]}""")
    return explanations


affectedness = overview[overview["Language_ID"] == overview["Orig_Language"]]
affectedness = affectedness[affectedness["Affected"].isin(["y", "n"])]
affectedness = affectedness[affectedness["Concept"].isin(verb_list)]
affectedness.to_csv("patterns.csv", index=False)
# affectedness.drop(
#     columns=["Prefix_Form", "Orig_Language", "Language_ID"],
#     inplace=True,
# )
affectedness["Form"] = affectedness["Form"].apply(lambda x: x.split("-")[1])

# # add fake Sa verbs
# for lg, conds in phon_preds.items():
#     for i in range(0, 100):
#         df = df.append({"Form": conds[0]+"turu", "Language_ID": lg, "Verb_Cognateset_ID": f"DETRZ+talk{i}", "Affected": "y", "Meaning_ID": "talk"}, ignore_index=True)

for lg in ["PWai", "PPek", "PTir", "aku", "car", "yuk"]:
    df_temp = affectedness[affectedness["Language_ID"] == lg]
    df_temp = df_temp[df_temp["Affected"].isin(["y", "n"])]
    df_temp["Affected"] = df_temp["Affected"].map({"n": False, "y": True})
    df_temp.rename(columns={"Verb_Cognateset_ID": "ID"}, inplace=True)
    explanations = {}
    for i, row in df_temp.iterrows():
        explanations[row["ID"]] = test_explanations(row.to_dict())
    r_df = pd.DataFrame(explanations)
    r_df = r_df.applymap(int)
    r_df["Score"] = r_df.apply(sum, axis=1) / len(r_df.columns)
    r_df.sort_values(by="Score", inplace=True, ascending=False)
    label = f"{lg.lower()}_predictions"
    export_csv(
        r_df,
        label,
        caption=f"Predictions and scores for {name_dic[lg]}",
        keep_index=True,
        print_i_name=True,
    )
    # r_df.to_csv(f"{lg}_results.csv")
    print(r_df)

print(get_frequency_prediction("go", frequencies))
#
#
# cond_map = {
#     "yuk_j": ["ə", "e", "a"],
#     "aku_k": ["ə"],
#     "car_j": ["e", "ə"],
#     "ppek_k": ["ə", "e"],
#     "pwai_k": ["o", "e"],
#     "ptir_t": ["ə", "e"],
# }
#
#
#
#
# # affectedness["morphological"] = affectedness.apply(m_expl, axis=1)
# # affectedness["phonological"] = affectedness.apply(p_expl, axis=1)
# # affectedness["frequency"] = affectedness.apply(f_expl, axis=1)
# # affectedness.drop(columns=["Verb_Cognateset_ID", "Concept", "Meaning_ID"], inplace=True)
#
#
# # def format_exp(f):
# #     if float(f).is_integer():
# #         return str(int(f))
# #     else:
# #         return str(int(f)) + "-" + str(int(f) + 1)
#
#
# # def get_ratio(x, factor):
# #     return f"{format_exp(x[factor].sum())}/{str(len(x))}"
#
#
# # def get_perc(x, factor):
# #     return x[factor].sum() / len(x)
#
#
# # def get_print(x, factor):
# #     return get_ratio(x, factor) + " ({:.0%})".format(get_perc(x, factor))
#
#
# # affected_result = pd.DataFrame()
#
# # for factor in ["morphological", "phonological", "frequency"]:
# #     affected_result[factor] = affectedness.groupby("Extension_ID").apply(
# #         get_print, factor
# #     )
#
# # caption = "Proportion of (un-)affected verbs accurately predicted by potential factors"
# # label = "factors"
#
# # affected_result["Language_ID"] = affected_result.index.map(ext_lg_dic)
# # sort_lg(affected_result)
# # affected_result.drop(columns=["Language_ID"], inplace=True)
#
# # aff_export = affected_result.copy()
# # aff_export.index = aff_export.index.map(lambda x: extension_string(x, latex=False))
# # export_csv(aff_export, label, caption, keep_index=True)
#
# # affected_result.index = affected_result.index.map(extension_string)
# # affected_result.index.name = None
#
# # save_float(
# #     print_latex(affected_result, keep_index=True),
# #     label,
# #     caption,
# # )
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
# # participles
# pyd.filters = {"Construction": ["PTCP"]}
# emp = ["o-", "w-"]
# res = pyd.compose_paradigm(dv_df)
# for em in emp:
#     res["S_A_"] = res["S_A_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
# res["S_A_"] = res["S_A_"].str.replace("\emp{o-}se", "o-se", regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(
#     print_latex(res, keep_index=True),
#     "participles",
#     "Participles of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
#     short="Participles of \gl{s_a_} and \gl{s_p_} verbs",
# )
#
# # nominalizations
# pyd.filters = {"Construction": ["NMLZ"]}
# emp = {"-u-": "-\\emp{u-}", "w-": "\\emp{w-}"}
# res = pyd.compose_paradigm(dv_df)
# for em, em1 in emp.items():
#     res["S_A_"] = res["S_A_"].str.replace(em, em1, regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(
#     print_latex(res, keep_index=True),
#     "nominalizations",
#     "Nominalizations of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
#     short="Nominalizations of \gl{s_a_} and \gl{s_p_} verbs",
# )
#
# # imperatives
# pyd.filters = {"Construction": ["IMP"]}
# emp = ["oj-", "o-", "ə-", "əw-", "aj-"]
# res = pyd.compose_paradigm(dv_df)
# for em in emp:
#     res["S_P_"] = res["S_P_"].str.replace(em, f"\\emp{{{em}}}", regex=False)
# res.columns = res.columns.map(pynt.get_expex_code)
# save_float(
#     print_latex(res, keep_index=True),
#     "imperatives",
#     "Imperatives of \gl{s_a_} and \gl{s_p_} verbs " + get_sources(dv_df),
#     short="Imperatives of \gl{s_a_} and \gl{s_p_} verbs",
# )
# pyd.content_string = "Form"
#
#
# # preliminary Sa verb frequency counts from apalai
# apalai_data = pd.read_csv("../data/apalai_sa_verb_stats.csv")
#
# label = "apalaicounts"
#
# export_csv(
#     apalai_data,
#     label,
#     "Frequency counts of Sa verbs in two Apalai texts",
#     keep_index=False,
#     sources="",
# )
#
# apalai_data["Verb"] = apalai_data.apply(combine_form_meaning, axis=1)
# apalai_data.drop(columns=["Form", "Meaning"], inplace=True)
#
# apalai_data.rename(
#     columns={"% Sa": "% \gl{s_a_} verb tokens", "% Words": "% word tokens"},
#     inplace=True,
# )
#
#
# save_float(
#     print_latex(
#         apalai_data[["Verb", "Count", "% \gl{s_a_} verb tokens", "% word tokens"]],
#         formatters={
#             "% \gl{s_a_} verb tokens": "{:,.2%}".format,
#             "% word tokens": "{:,.2%}".format,
#         },
#     ),
#     label,
#     r"Frequency counts of \gl{s_a_} verbs in three \apalai texts from \textcite{koehns1994textos} (163 \gl{s_a_} verbs, 1070 words)",
#     short=r"Frequency counts of \gl{s_a_} verbs in \apalai",
# )
#
for t in exported_tables.keys():
    print(f"\\input{{floats/{t}.tex}}")
with open("data_output/metadata.json", "w") as outfile:
    json.dump(exported_tables, outfile, indent=4)
