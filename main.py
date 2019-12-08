import os
import argparse
from os import path as osp
import time
from copy import deepcopy
import numpy as np
from tabulate import tabulate

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
    start_symbol = grammar[0][0]
    grammar = [rule.rstrip().split(sep=' -> ', maxsplit=1) for rule in grammar]
    transitions = {rule[0]: rule[1].split(sep=' | ') for rule in grammar}
    nonterminals = set(transitions.keys())
    terminals = set()
    for transition in transitions.values():
        for child in transition:
            terminals.update(child.split())
    terminals = terminals.difference(nonterminals)

    return transitions, list(nonterminals), list(terminals), start_symbol


def generate_firsts_dict(terminals, nonterminals):
    firsts = dict()
    for terminal in terminals:
        firsts[terminal] = set()
        firsts[terminal].add(terminal)
    for nonterminal in nonterminals:
        firsts[nonterminal] = set()
    return firsts


def find_firsts(transitions, nonterminals, terminals, n_iter=5):
    firsts = generate_firsts_dict(terminals, nonterminals)
    for _ in range(n_iter):
        for nonterminal in nonterminals:
            for transition in transitions[nonterminal]:
                firsts[nonterminal].update(find_first(transition, firsts, nonterminals))
    return firsts


def find_follows(transitions, nonterminals, firsts, start_symbol, n_iter=5):
    follows = {nonterminal: set() for nonterminal in nonterminals}
    follows[start_symbol].add('$')
    for _ in range(n_iter):
        for nonterminal in nonterminals:
            for key, productions in transitions.items():
                for production in productions:
                    production = production.split()
                    if nonterminal in production:
                        if nonterminal == production[-1]:
                            follows[nonterminal].update(follows[key])
                        else:  # TODO: implement follow(B) for case aBc where c contains several nonterminals with eps
                            next_symbol = production[production.index(nonterminal) + 1]
                            tmp = deepcopy(firsts[next_symbol])
                            tmp.discard('ep')
                            follows[nonterminal].update(tmp)
                            if 'ep' in firsts[next_symbol]:
                                follows[nonterminal].update(follows[key])
    return follows


def print_dict(dict):
    for key, value in dict.items():
        print('\t{}: {}'.format(key, value))


def find_first(transition, firsts, nonterminals):
    first = set()
    if isinstance(transition, str):
        transition = transition.split()
    for symbol in transition:
        tmp = deepcopy(firsts[symbol])
        tmp.discard('ep') if symbol in nonterminals else None  # We add epsilon only if it is in all Y1...Yk
        first.update(tmp)
        if 'ep' not in firsts[symbol]:
            break
        elif symbol != transition[-1]:
            continue
        else:
            first.add('ep')
    return first


def build_table(grammar):
    transitions, nonterminals, terminals, start_symbol = process_grammar(grammar)
    firsts = find_firsts(transitions, nonterminals, terminals)
    follows = find_follows(transitions, nonterminals, firsts, start_symbol)

    table = np.empty((len(nonterminals), len(terminals) + 1), dtype=object)
    for row, items in enumerate(transitions.items()):
        nonterminal, productions = items
        for transition in productions:
            first = find_first(transition, firsts, terminals)
            for symbol in first:
                if symbol in terminals and symbol != 'ep':
                    table[row, terminals.index(symbol)] = transition
            if 'ep' in first:
                for symbol in follows[nonterminal]:
                    if symbol in terminals:
                        table[row, terminals.index(symbol)] = transition
                if '$' in follows[nonterminal]:
                    table[row, -1] = transition
    for key in terminals:
        firsts.pop(key)
    table = np.insert(table, 0, list(transitions.keys()), axis=1)
    terminals.append('$')
    terminals.insert(0, None)
    table = np.insert(table, 0, terminals, axis=0)
    return firsts, follows, table, terminals,


def main():
    args = parse_args()
    grammar = read_grammar(args.grammar)
    firsts, follows, table, terminals = build_table(grammar)
    terminals.insert(0, None)
    terminals.append('$')
    print('Firsts: ')
    print_dict(firsts)
    print('Follows:')
    print_dict(follows)
    print('Table:')
    print(tabulate(table, tablefmt='fancy_grid'))
    table = table[1:, 1:]



if __name__ == '__main__':
    start = time.time()
    main()
    print('Took {:.3f} to execute!'.format(time.time() - start))
