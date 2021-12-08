import pandas as pd
import itertools
import re

i_df = pd.read_csv("../data/inflection_data.csv")
s_df = pd.read_csv("../data/verb_stem_data.csv")
b_df = pd.read_csv("../data/bathe_data.csv")

def extract_abbrevs(full_string):
    def iterate(string):
        for repl in [r"\1", ""]:
            variant = re.sub(r"\[(.*?)\]", repl, string, 1)
            if ("[" in variant):
                for i in iterate(variant):
                    yield i
            else:
                yield variant.replace("]", "")

    
    all_abbrevs = list(itertools.chain(*[iterate(s) for s in full_string.split(", ")]))
    # Deduplicate while keeping the order:
    seen = set()
    return [x for x in all_abbrevs if not (x in seen or seen.add(x))]

s_df = s_df.append(b_df)
# s_df["Short"] = s_df["Form"].replace({"\[.*?\]": ""}, regex=True)
# s_df["Form"] = s_df["Form"].replace({"\[": "", "\]": ""}, regex=True)
s_df["Forms"] = s_df["Form"].map(extract_abbrevs)


stems = {}
for lg, df in s_df.groupby("Language_ID"):
    stems[lg] = {}
    for i, row in df.iterrows():
        cogid = row["Cognateset_ID"]
        if cogid not in stems[lg]:
            stems[lg][cogid] = row["Forms"]
        else:
            stems[lg][cogid].extend(row["Forms"])

for i, row in i_df.iterrows():
    verb = row["Verb_Cognateset_ID"]
    if pd.isnull(verb): continue
    form = row["Form"]
    if "-" not in form: continue
    lg = row["Language_ID"]
    if lg not in stems:
        raise ValueError(f"No data for language {lg}!")
    if verb not in stems[lg]:
        print(f"No data for {lg} {form} '{verb}'!")
        continue
    if row["Inflection"] not in ["IMP"]:
        i = 1
    else:
        i = 0
    stem = form.split("-")[i]
    while (stem not in stems[lg][verb] and i+1 < len(form.split("-"))):
        i += 1
        stem = form.split("-")[i]
    if stem not in stems[lg][verb]:
        print(f"{lg} {form} does not match stem {stems[lg][verb]}")
