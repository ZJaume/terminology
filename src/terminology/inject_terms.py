#!/usr/bin/env python
import sys
import json
import logging
import regex
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

parser = ArgumentParser(
        description="Inject terminology in source and target sentence for forced translation training",
        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("input", type=FileType('r'),
                    default=sys.stdin, nargs='?',
                    help='Input txt file, one sentence per line')
parser.add_argument("output", type=FileType('w'),
                    default=sys.stdout, nargs='?',
                    help='Output txt file, one sentence per line')
parser.add_argument("-c", "--check",
                    default=False, action='store_true',
                    help='Perform terminology check instead of annotation')
parser.add_argument("-d", "--terminology",
                    type=FileType('r'), required=True,
                    help='Tab-separated terminology file')
parser.add_argument("-s", "--src_lang",
                    type=str, required=True, help='Source language')
parser.add_argument("-t", "--trg_lang",
                    type=str, required=True, help='Target language')
parser.add_argument("--start-symbol",
                    type=str, default='<misc0>',
                    help='Start symbol for terminology boundaries')
parser.add_argument("--mid-symbol",
                    type=str, default='<misc1>',
                    help='Middle symbol for terminology boundaries')
parser.add_argument("--end-symbol",
                    type=str, default='<misc2>',
                    help='End symbol for terminology boundaries')

def load_terms(args):
    ''' Load terminology json dictionaries into a dict '''
    terms = {}
    for line in args.terminology:
        entries = json.loads(line)["term"]
        for entry in entries:
            # Ignore entries for other langs and use only preferred
            if entry["lang"] != args.src_lang or not entry["preferred"]:
                continue

            # For each entry in the source language create a dictionary entry
            #TODO trecase in source or target??
            for entry_trg in entries:
                # In the target we search for the prefered one
                if entry_trg["lang"] == args.trg_lang and entry_trg['preferred']:
                    # If current term has already been read in a previous entry
                    # we keep it if the current target is longer than the previous
                    if entry["word"] in terms \
                            and len(terms[entry["word"]]) <= len(entry_trg["word"]):
                        break
                    terms[entry["word"].casefold()] = entry_trg["word"]
                    break
            else:
                raise Exception(f"Source word '{entry['word']}'" \
                        + " has no corresponding entry in the target language")
    return terms

def create_terms_regex(terms):
    ''' Read terminology dictionary
        Build a regex with all the keys
    '''
    r = r'\b('
    for i, term in enumerate(terms):
        if i != 0:
            r += r'|'
        r += regex.escape(term)
    # At most 4 chars of suffix
    # can't specify a suffix depending on the word because
    # will need to be inside the group
    # and we won't be able to place the tags with the suffix outside
    r += r')\w{0,4}\b'
    # Compile with ignorecase, casefold and match the longest possible (posix)
    r = regex.compile(r, flags=regex.I | regex.FULLCASE | regex.POSIX)

    return r

def create_terms_target_regex(args, terms):
    ''' Create a dictionary of terms
        where the values are regex to search the target term
    '''
    # Avoid word contained inside another with preceeding word boundary \b
    tbeg = '\\b(?<!' + regex.escape(args.start_symbol).replace('<','[<]') + ')'
    tend = r'(?!' + regex.escape(args.end_symbol) + ')'
    terms_trg_re = {}

    for term in terms:
        # We check that the target term is not already annotated
        trg_re = tbeg + regex.escape(terms[term]) + tend
        terms_trg_re[term] = regex.compile(trg_re, flags=regex.I | regex.FULLCASE)

    return terms_trg_re

def annotate_target(args, sentence, match):
    ''' Add special tokens annotation to the target '''

    start = match.span()[0]
    end = match.span()[1]
    fragments = [sentence[:start]]
    fragments.append(args.start_symbol)
    fragments.append(sentence[start:end])
    fragments.append(args.end_symbol)
    fragments.append(sentence[end:])

    return ''.join(fragments)

def annotate_source(args, terms, sentence, matches):
    ''' Add special tokens plus target terms to the source matches '''
    matches.sort(key=lambda x: x.span())
    fragments = []
    cur = 0

    for match in matches:
        # Acces through group 1 to remove suffix
        start = match.start(1)
        end = match.end(1)

        if start < cur:
            print(f"OVERLAP! {sentence}: {matches}")
            continue # avoid overlaps

        fragments.append(sentence[cur:start])
        fragments.append(args.start_symbol)
        fragments.append(sentence[start:end])
        fragments.append(args.mid_symbol)
        # Acces through group 1 to remove suffix
        fragments.append(terms[match.group(1).casefold()])
        fragments.append(args.end_symbol)

        cur = end

    fragments.append(sentence[cur:])
    return ''.join(fragments)

def main():
    args = parser.parse_args()
    terms = load_terms(args)
    terms_re = create_terms_regex(terms)
    terms_trg_re = create_terms_target_regex(args, terms)

    correct_terms = 0
    total_terms = 0
    for line in args.input:
        src, trg = line.strip().split('\t')

        src_to_annotate = []
        # find each term found term in the source, in the target
        for match in terms_re.finditer(src):
            total_terms += 1
            # Acces through group 1 to remove suffix
            trg_term = terms_trg_re[match.group(1).casefold()]
            found = trg_term.search(trg)
            if found:
                # annotate target sentence if term found
                # save current term to be annotated in source
                if not args.check:
                    trg = annotate_target(args, trg, found)
                    src_to_annotate.append(match)
                else:
                    correct_terms += 1

        if not args.check:
            # Print source and target sentences
            # adding to source the terms that have been found in target
            print(annotate_source(args, terms, src, src_to_annotate), trg, sep='\t')

    if args.check:
        print(f"Terminology check: {correct_terms} out of" \
              + f" {total_terms} ({correct_terms/total_terms*100:.2f}%)")
    else:
        print(f"Total terms found: {total_terms}", file=sys.stderr)

if __name__ == "__main__":
    main()
