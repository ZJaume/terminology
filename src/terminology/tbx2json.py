"""
Transforms TBX files in simplified JSON objects

Usage:
  tbx2json.py [options] [INPUT [OUTPUT]]

Options:
  --enable_non_alphabetical    Do not ignore non-alphabetical terms.
  --enable_small               Do not ignore terms whose lenght <= 3.
  -h --help                    Shows this help.
"""
import docopt
import xmltojson
import sys
import json

from collections import OrderedDict

enable_small = False
enable_non_alphabetical = False


def get_preferred(elem, key):
    if key not in elem:
        return False
    term_note = elem[key]
    if type(term_note) == type([]):
        for i in term_note:
            if "#text" in i and i["#text"] == "preferred":
                return True
    return False


def is_complete(term):
    langs = [w["lang"] for w in term]
    if len(set(langs)) < 2:
        return False
    else:
        return True


def generate_json_simplified(bigjson, out):
    global enable_small, enable_non_alphabetical
    for elem in bigjson["martif"]["text"]["body"]["termEntry"]:
        term = []
        for accep in elem["langSet"]:
            if type(accep) != type({}) or "@xml:lang" not in accep:
                continue
            lang = accep['@xml:lang']
            if type(accep) != type({}) or "tig" not in accep:
                continue
            words = accep['tig']
            if type(words) == type([]):
                trues = 0
                falses = 0
                localterm = []
                for i in words:
                    w = OrderedDict()
                    pref = get_preferred(i, 'termNote')
                    w["word"] = i['term']['#text']
                    w["lang"] = lang[0:2]
                    w["preferred"] = pref
                    if not enable_small and len(w["word"]) <= 3:
                        continue
                    if not enable_non_alphabetical and not any(c.isalpha() for c in w["word"]):
                        continue
                    if pref:
                        trues += 1
                    else:
                        falses += 1
                    localterm.append(w)

                if trues == 0 and trues + falses > 0:
                    localterm[-1]["preferred"] = True
                elif trues >= 2:
                    for j in localterm:
                        if j["preferred"]:
                            j["preferred"] = False
                            trues -= 1
                        if trues == 1:
                            break

                term.extend(localterm)
            else:
                w = OrderedDict()
                w["word"] = words['term']['#text']
                w["lang"] = lang[0:2]
                w["preferred"] = True
                if not enable_small and len(w["word"]) <= 3:
                    continue
                if not enable_non_alphabetical and not any(c.isalpha() for c in w["word"]):
                    continue
                term.append(w)
        if is_complete(term):
            print(json.dumps({"term": term}), file=out)


def main():
    args = docopt.docopt(__doc__, version=f'tbx2json v 1.0')
    global enable_small, enable_non_alphabetical

    fin = sys.stdin
    fout = sys.stdout

    if args["INPUT"] is not None:
        fin = open(args["INPUT"], "r")
    if args["OUTPUT"] is not None:
        fout = open(args["OUTPUT"], "wt")

    enable_small = args["--enable_small"]
    enable_non_alphabetical = args["--enable_non_alphabetical"]

    bigjson = json.loads(xmltojson.parse(fin.read()))
    fin.close()
    
    if len(bigjson) > 0:
        generate_json_simplified(bigjson, fout)
    
    fout.close()

    
if __name__ == '__main__':
    main()

