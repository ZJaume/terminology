#!/usr/bin/env python
import re
import sys
import json
import html
import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

try:
    from .utils import get_suffix
except ImportError:
    from utils import get_suffix

parser = ArgumentParser("Convert terminology file (json) to .dix lttoolbox format.", formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("input", type=FileType('r'), default=sys.stdin, nargs='?', help='Input json terminology file')
parser.add_argument("output", type=FileType('w'), default=sys.stdout, nargs='?', help='Output dix file.')
parser.add_argument("-s", "--src_lang", type=str, required=True, help='Source language')
parser.add_argument("-t", "--trg_lang", type=str, required=True, help='Target language')
parser.add_argument("--start-symbol", type=str, default='<t_start>', help='Start symbol for terminology boundaries')
parser.add_argument("--mid-symbol", type=str, default='<t_mid>', help='Middle symbol for terminology boundaries')
parser.add_argument("--end-symbol", type=str, default='<t_end>', help='End symbol for terminology boundaries')

ALPHABET = "ÃÀÁĀÂÄÇẼÈÉÊËÌÍĪÎĨÏÑÕÒŌÓÔÖÙÚŨÛÜãàáāâäçèéêẽëìíĩīîïñõòōóôöùúũûüABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DIX_HEADER = f'''<?xml version="1.0" encoding="UTF-8"?>
<dictionary>
  <alphabet>{ALPHABET}</alphabet>
'''
RE_SUFFIX = f'''<pardefs>
    <pardef n="suffix1">
        <e><re>[{ALPHABET}]?</re></e>
    </pardef>
    <pardef n="suffix2">
        <e><re>[{ALPHABET}]?</re></e>
        <e><re>[{ALPHABET}][{ALPHABET}]?</re></e>
    </pardef>
    <pardef n="suffix3">
        <e><re>[{ALPHABET}]?</re></e>
        <e><re>[{ALPHABET}][{ALPHABET}][{ALPHABET}]?</re></e>
    </pardef>
    <pardef n="suffix4">
        <e><re>[{ALPHABET}]?</re></e>
        <e><re>[{ALPHABET}][{ALPHABET}][{ALPHABET}]?</re></e>
        <e><re>[{ALPHABET}][{ALPHABET}][{ALPHABET}][{ALPHABET}]</re></e>
    </pardef>
</pardefs>
'''

def read_term(entries, args, read_entries):
    out = ''
    for entry in entries:
        # For each entry in the source language create a dictionary entry
        #TODO trecase in source or target??
        #TODO if entry already read, use the longest
        if entry["lang"] == args.src_lang \
                and entry["preferred"] \
                and entry["word"] not in read_entries:
            out += f'<e><p><l>{html.escape(entry["word"])}</l>'
            read_entries.add(entry["word"])
            for entry_trg in entries:
                # In the target we search for the prefered one that's it
                if entry_trg["lang"] == args.trg_lang and entry_trg['preferred']:
                    out += f'<r><s n="{args.start_symbol}"/>'
                    out += f'{html.escape(entry["word"])}'
                    out += f'<s n="{args.mid_symbol}"/>'
                    #TODO insert trg word lemmetized?
                    out += f'{html.escape(entry_trg["word"])}'
                    out += f'<s n="{args.end_symbol}"/>'
                    out += '</r></p>' + get_suffix(entry["word"]) + '</e>\n'
                    break
            else:
                raise Exception(f"Source word '{entry['word']}' " \
                        + " has no corresponding entry in the target language")
    return out


def main():
    args = parser.parse_args()
    args.start_symbol = args.start_symbol.strip('<>')
    args.mid_symbol = args.mid_symbol.strip('<>')
    args.end_symbol = args.end_symbol.strip('<>')
    read_entries = set()

    # Print dix header
    print(DIX_HEADER, file=args.output, end='')

    # Print special symbols
    print('<sdefs>', file=args.output)
    print(f'<sdef n="{args.start_symbol}"/>', file=args.output)
    print(f'<sdef n="{args.mid_symbol}"/>', file=args.output)
    print(f'<sdef n="{args.end_symbol}"/>', file=args.output)
    print('</sdefs>', file=args.output)

    # Suffix regex definition
    print(RE_SUFFIX, file=args.output)

    # Print entries section
    print('<section id="main" type="standard">', file=args.output)
    # Read terminology, one json per line
    # eachline is a term entry
    for line in args.input:
        term = json.loads(line.strip())
        args.output.write(read_term(term["term"], args, read_entries))

    print('</section>', file=args.output)
    print('</dictionary>', file=args.output)

if __name__ == "__main__":
    main()
