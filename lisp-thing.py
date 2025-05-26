#!/usr/bin/env python3

import os, sys
import re, json

def main():
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("file", nargs="?")
    group.add_argument("-c", "--command", help=
        "the literal code of the program, not read from a file.")
    args = parser.parse_args()

    if args.file != None:
        with open(args.file) as f:
            contents = f.read()
    elif args.command != None:
        contents = args.command
    else: assert False

    tree = parse(contents)
    #print(repr(tree))

    print(eval_tuple(tree))

token_re = re.compile(r''
    r'\s+|' # Whitespace.
    r'\(|'
    r'\)|'
    r'"(?:[^"\n\\]|\\.)+"|' # Literally json strings.
    r'[^()\s]+' # Integers, identifiers, and anything else unrecognized.
    # We do NOT set re.DOTALL, because we don't want string literals to go past newline boundaries.
)
def parse(contents):
    stack = [[]]
    for match in token_re.finditer(contents):
        token_str = match.group()
        if token_str == "(":
            stack.append([])
        elif token_str == ")":
            if len(stack) < 2: raise ParseError("unmatched ')'")
            stack[-2].append(stack.pop())
        elif token_str.strip() == "":
            continue
        else:
            # Primative value
            stack[-1].append(parse_value(token_str))

    # Final syntax checks.
    if len(stack) > 1: raise ParseError("unmatched '('")
    top_level_expressions = stack.pop()
    if len(top_level_expressions) == 0: raise ParseError("unexpected end of input")
    if len(top_level_expressions) > 1: raise ParseError("too many top-level expressions")

    return top_level_expressions.pop()

def parse_value(token_str):
    try: return Integer(int(token_str))
    except ValueError: pass

    if token_str[0] == '"':
        try:
            return String(json.loads(token_str))
        except json.JSONDecodeError as e:
            raise ParseError(e) from None
    # Identifier
    return Identifier(token_str)

class ParseError(Exception): pass
class RuntimeError(Exception): pass

class Expr: pass
class Identifier(Expr):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "id:" + self.name
class Integer(Expr):
    def __init__(self, n):
        self.n = n
    def __repr__(self):
        return repr(self.n)
class String(Expr):
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return json.dumps(self.s)

def eval_tuple(tree):
    assert type(tree) == list
    if len(tree) == 0: raise RuntimeError("empty list")

    function_id = tree[0]
    if type(function_id) != Identifier: raise RuntimeError("cannot invoke a " + str(type(function_id)))

    fn = builtin_functions[function_id.name]

    args = [eval_expr(arg_tree) for arg_tree in tree[1:]]
    return fn(*args)

def eval_expr(expr):
    if type(expr) == list:
        return eval_tuple(expr)
    elif type(expr) == Identifier: raise RuntimeError("cannot eval an identifier: " + expr.name)
    elif type(expr) == Integer:
        return expr.n
    elif type(expr) == String:
        return expr.s
    else: assert False

builtin_functions = {
    "+": (lambda *args: sum(args)),
    "list": (lambda *args: list(args)),
    "first": (lambda l: l[0]),
}

if __name__ == "__main__":
    main()
