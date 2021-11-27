import pandas as pd
i_df = pd.read_csv("../data/inflection_data.csv")
s_df = pd.read_csv("../data/verb_stem_data.csv")
b_df = pd.read_csv("../data/bathe_data.csv")

s_df = s_df.append(b_df)
s_df["Form"] = s_df["Form"].replace({"\[": "", "\]": "", "\+": ""}, regex=True)

stems = {}
for lg, df in s_df.groupby("Language_ID"):
    stems[lg] = dict(zip(df["Cognateset_ID"], df["Form"]))

for i, row in i_df.iterrows():
    verb = row["Verb_Cognateset_ID"]
    lg = row["Language_ID"]
    form = row["Form"]
    if pd.isnull(verb): continue
    if lg not in stems:
        raise ValueError(f"No data for language {lg}!")
    if verb not in stems[lg]:
        print(f"No data for {lg} {form} '{verb}'!")