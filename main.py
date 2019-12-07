import os
import argparse
from os import path as osp
import time
from itertools import chain


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grammar',
                        type=str,
                        default='grammar.txt',
                        help='Path to file containing grammar'
                        )
    parser.add_argument('--word',
                        type=str,
                        default='id+id*id$')

    return parser.parse_args()


def read_grammar(fpath):
    data = None
    assert osp.exists(fpath), fpath
    assert osp.isfile(fpath), fpath
    with open(fpath) as file:
        data = file.readlines()
    return data


def process_grammar(grammar):
    print('Initial grammar: ', grammar)
    grammar = [rule.rstrip().split(sep=' -> ', maxsplit=1) for rule in grammar]
    transitions = {rule[0]: rule[1].split(sep=' | ') for rule in grammar}
    print('Grammar after splitting: ', grammar)
    nonterminals = set(transitions.keys())
    terminals = set()
    for transition in transitions.values():
        for child in transition:
            terminals.update(child.split())
    terminals = terminals.difference(nonterminals)

    # print('Transitions: ', transitions)
    # print('Terminals: ', terminals)
    # print('Nonterminals: ', nonterminals)
    return transitions, nonterminals, terminals


def find_firsts(transitions, nonterminals, terminals):
    firsts = dict.fromkeys(nonterminals, set())
    print(firsts)


def main():
    args = parse_args()
    grammar = read_grammar(args.grammar)
    transitions, nonterminals, terminals = process_grammar(grammar)
    find_firsts(transitions, nonterminals, terminals)


if __name__ == '__main__':
    start = time.time()
    main()
    print('Took {:.3f} to execute!'.format(time.time() - start))
