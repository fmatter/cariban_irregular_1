# this script gathers and counts the Sa verbs in
# Courtz' (2008) Kari'ña dictionary, in order to
# get an approximation of how many "normal" Sa
# verbs one may expect in a Cariban language.

import re

text = open("kalina_dictionary.txt").read()
sa_verbs = re.findall(r"[()\wàèìòùỳ]+ /vm/", text)

glodic = {
    "à": "aʔ",
    "è": "eʔ",
    "ì": "iʔ",
    "ò": "oʔ",
    "ù": "uʔ",
    "ỳ": "ɨʔ",
    "y": "ɨ",
}


def kal2pc(form):
    for a, b in glodic.items():
        form = form.replace(a, b)
    form = form.replace(" /vm/", "")
    form = form.replace("(w)o", "o")
    form = form.replace("(w)a", "a")
    form = form.replace("(w)e", "e")
    return form


sa_verbs = list(map(kal2pc, sa_verbs))
print("\n".join(sa_verbs))
print(len(sa_verbs))
