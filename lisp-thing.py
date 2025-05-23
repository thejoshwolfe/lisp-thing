#!/usr/bin/env python3

import os, sys
import re, json

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    with open(args.file) as f:
        contents = f.read()
    print(repr(parse(contents)))

token_re = re.compile(r''
    r'\s+|'
    r'\(|'
    r'\)|'
    r'"(?:[^"\n\\]|\\.)+"|' # roughly json strings.
    r'[^()\s]+'
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

class Value: pass
class Identifier(Value):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "id:" + self.name
class Integer(Value):
    def __init__(self, n):
        self.n = n
    def __repr__(self):
        return repr(self.n)
class String(Value):
    def __init__(self, s):
        self.s = s
    def __repr__(self):
        return json.dumps(self.s)

if __name__ == "__main__":
    main()
