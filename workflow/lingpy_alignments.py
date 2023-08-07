import lingpy
from lingpy.compare.partial import Partial
import pandas as pd
import os
from difflib import SequenceMatcher

tempfile = "lingpy_temp.tsv"

cldf_lingpy = {
    "Language_ID": "DOCULECT",
    "Parameter_ID": "CONCEPT",
    "Form": "IPA",
    "Cognateset_ID": "COGIDS",
    "Segments": "TOKENS",
    "Source": "SOURCE",
    "Alignment": "ALIGNMENT",
    "Comment": "COMMENT",
    "ID": "CLDF_ID",
}


def rename_dict(df):
    for col in df.columns:
        if col not in cldf_lingpy:
            cldf_lingpy[col] = col.upper()
    lingpy_cldf = {y: x for x, y in cldf_lingpy.items()}
    return cldf_lingpy, lingpy_cldf


lingpy_cldf = {y: x for x, y in cldf_lingpy.items()}


def merge_sequences(seq1, seq2):
    sm = SequenceMatcher(a=seq1, b=seq2)
    res = []
    for op, start1, end1, start2, end2 in sm.get_opcodes():
        if op == "equal" or op == "delete":
            # This range appears in both sequences, or only in the first one.
            res += seq1[start1:end1]
        elif op == "insert":
            # This range appears in only the second sequence.
            res += seq2[start2:end2]
        elif op == "replace":
            # There are different ranges in each sequence - add both.
            res += seq1[start1:end1]
            res += seq2[start2:end2]
    return res


def get_order(lol):
    lol = sorted(lol, key=len, reverse=True)
    out = lol[0]
    for i in range(1, len(lol)):
        out = merge_sequences(out, lol[i])
    return out


def is_empty(slot):
    if list(set(slot.split())) == ["-"]:
        return True
    else:
        return False


def join_slots(slotlist, almsep):
    out = [slotlist[0]]
    for slot in slotlist[1::]:
        if is_empty(out[-1]) or is_empty(slot):
            out.append("-")
        else:
            out.append("+")
        out.append(slot)
    return " ".join(out)


def buffer_alignments(df, cogid="COGIDS", cogsep=" ", almid="ALIGNMENT", almsep=" + "):
    cogsets = list(set(df[cogid]))
    cogsets = [x.split(cogsep) for x in cogsets]
    entries = []
    for i, row in df.iterrows():
        pairs = dict(zip(row[cogid].split(cogsep), row[almid].split(almsep)))
        entries.append(pairs)

    c = pd.DataFrame.from_dict(entries)
    order = get_order(cogsets)
    c = c[order]

    buffers = {}
    for x in c.columns:
        values = [val.split(" ") for val in list(c[x]) if not pd.isnull(val)]
        buffers[x] = len(values[0])
        c[x].fillna(" ".join(["-" for i in range(0, buffers[x])]), inplace=True)
    c[almid] = c[[x for x in order]].values.tolist()
    # c[almid] = c[almid].apply(lambda x: almsep.join(x))
    c[almid] = c[almid].apply(join_slots, almsep=almsep)
    df[almid] = c[almid]
    # print(df)


def get_alm_df(df, almid="ALIGNMENT"):
    entries = []
    for i, row in df.iterrows():
        entries.append(row[almid].split(" "))
    c = pd.DataFrame.from_records(entries)
    c = c.replace({"-": ""})
    c = c.replace({"+": "-"})
    c.columns = [""] * len(c.columns)
    return c


def calculate_alignment(df, fuzzy=False):
    cldf_lingpy, lingpy_cldf = rename_dict(df)
    df.rename(columns=cldf_lingpy, inplace=True)
    # df.drop(columns=["Comment", "ID"], inplace=True)
    df.index.name = "ID"
    df.to_csv(tempfile, sep="\t", index=True)
    if fuzzy:
        lex = Partial(tempfile)
        alm = lingpy.Alignments(lex, ref="cogids", fuzzy=True)
    else:
        lex = lingpy.Wordlist(tempfile)
        alm = lingpy.Alignments(lex, ref="cogids")
    alm.align(model="sca", method="library")
    alm.output("tsv", filename="lingpy_temp", ignore="all", prettify=False)

    df = pd.read_csv(tempfile, sep="\t", dtype="str")
    if fuzzy:
        df.drop(
            columns=[
                "SONARS",
                "PROSTRINGS",
                "CLASSES",
                "LANGID",
                "NUMBERS",
                "WEIGHTS",
                "DUPLICATES",
            ],
            inplace=True,
        )
    os.remove(tempfile)

    if fuzzy:
        buffer_alignments(df)
    c = get_alm_df(df)
    df = pd.concat([df, c], axis=1)

    df.drop(
        columns=[
            "ID",
            # "CONCEPT",
            # "COGIDS",
            # "TOKENS",
            "ALIGNMENT",
        ],
        inplace=True,
    )
    df.rename(columns=lingpy_cldf, inplace=True)

    return df
