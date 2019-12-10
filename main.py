import os
import argparse
from os import path as osp
import time
from copy import deepcopy
import numpy as np
from tabulate import tabulate
from collections import deque

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grammar',
                        type=str,
                        default='grammar_1.txt',
                        help='Path to file containing grammar'
                        )
    parser.add_argument('--word',
                        type=str,
                        default='id + id * id $') # 'a c b g f h' for grammar_1

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
                        else:
                            first_of_remain = find_first(production[production.index(nonterminal) + 1:], firsts, nonterminals)
                            follows[nonterminal].update(first_of_remain.difference(['ep']))
                            if 'ep' in first_of_remain:
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
    tmp = deepcopy(terminals)
    tmp.insert(0, None)
    table = np.insert(table, 0, tmp, axis=0)
    return firsts, follows, table, terminals, transitions


def parse_word(word, table, start_symbol, terminals, nonterminals):
    print('Processing string {} with table'.format(word))
    stack = deque((start_symbol, '$'))
    input_stream = deque(word.split())
    stack_symbol = start_symbol
    while stack_symbol != '$':
        input_symbol = input_stream[0]
        if stack_symbol == input_symbol:
            stack.popleft()
            input_stream.popleft()
            stack_symbol = stack[0]
            continue
        elif stack_symbol in terminals:
            raise RuntimeError('Unable to process the string with the grammar')
        row = nonterminals.index(stack_symbol)
        col = terminals.index(input_symbol)
        if table[row, col] is None:
            raise RuntimeError('Unable to process the string with the grammar')
        else:
            print('\tProduction {} -> {}'.format(stack_symbol, table[row, col]))
            stack.popleft()
            if table[row, col] != 'ep':
                stack.extendleft(reversed(table[row, col].split()))
        stack_symbol = stack[0]



def main():
    args = parse_args()
    grammar = read_grammar(args.grammar)
    firsts, follows, table, terminals, transitions = build_table(grammar)
    print('Firsts: ')
    print_dict(firsts)
    print('Follows:')
    print_dict(follows)
    print('Table:')
    print(tabulate(table, tablefmt='fancy_grid'))
    table = table[1:, 1:]
    parse_word(args.word, table, grammar[0][0], terminals, list(transitions.keys()))



if __name__ == '__main__':
    start = time.time()
    main()
    print('Took {:.3f} to execute!'.format(time.time() - start))
