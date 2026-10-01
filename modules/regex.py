"""
Regular Expression module.

Supports the classic textbook regex operators over a single-character
alphabet:
    |        alternation      (a|b)
    *        Kleene star       a*
    +        one or more       a+
    ?        optional          a?
    (  )     grouping
    concatenation is implicit, e.g. "ab" means a followed by b

The regex is parsed into a small syntax tree, then compiled into an
epsilon-NFA using Thompson's Construction -- the standard textbook
algorithm for regex -> automaton. Accept/reject is then decided by
literally simulating that automaton, not by calling Python's `re` module,
so this matches how the theory course teaches it.
"""

from modules.dfa import AutomatonInputError
from modules.enfa import EpsilonNFA, EPSILON


class RegexSyntaxError(AutomatonInputError):
    pass


# ---------------------------------------------------------------------------
# Step 1: tokenizer + recursive-descent parser -> syntax tree
# Grammar (lowest to highest precedence):
#   expr    := term ('|' term)*
#   term    := factor+                (concatenation)
#   factor  := atom ('*' | '+' | '?')?
#   atom    := symbol | '(' expr ')'
# ---------------------------------------------------------------------------

class _Parser:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def advance(self):
        ch = self.peek()
        self.pos += 1
        return ch

    def parse(self):
        if self.text == "":
            raise RegexSyntaxError("The regular expression is empty.")
        node = self.parse_expr()
        if self.pos != len(self.text):
            raise RegexSyntaxError('Unexpected character "{}" at position {}.'.format(self.peek(), self.pos))
        return node

    def parse_expr(self):
        node = self.parse_term()
        while self.peek() == "|":
            self.advance()
            right = self.parse_term()
            node = ("union", node, right)
        return node

    def parse_term(self):
        factors = []
        while self.peek() is not None and self.peek() not in ("|", ")"):
            factors.append(self.parse_factor())
        if not factors:
            raise RegexSyntaxError("Expected a symbol or group here.")
        node = factors[0]
        for f in factors[1:]:
            node = ("concat", node, f)
        return node

    def parse_factor(self):
        node = self.parse_atom()
        while self.peek() in ("*", "+", "?"):
            op = self.advance()
            node = (op, node)
        return node

    def parse_atom(self):
        ch = self.peek()
        if ch is None:
            raise RegexSyntaxError("Unexpected end of expression.")
        if ch == "(":
            self.advance()
            node = self.parse_expr()
            if self.peek() != ")":
                raise RegexSyntaxError("Missing closing parenthesis.")
            self.advance()
            return node
        if ch in ("*", "+", "?", "|", ")"):
            raise RegexSyntaxError('Unexpected "{}" at position {}.'.format(ch, self.pos))
        self.advance()
        return ("symbol", ch)


def parse_regex(text):
    return _Parser(text.replace(" ", "")).parse()


# ---------------------------------------------------------------------------
# Step 2: Thompson's Construction -- turn the syntax tree into an epsilon-NFA
# ---------------------------------------------------------------------------

class _FragmentBuilder:
    """Builds up (states, transitions) while compiling the syntax tree."""

    def __init__(self):
        self.counter = 0
        self.transitions = {}
        self.states = []

    def new_state(self):
        name = "s{}".format(self.counter)
        self.counter += 1
        self.states.append(name)
        return name

    def add_edge(self, frm, symbol, to):
        self.transitions.setdefault((frm, symbol), [])
        self.transitions[(frm, symbol)].append(to)

    def build(self, node):
        """Returns (start, end) states for this subtree's fragment."""
        kind = node[0]

        if kind == "symbol":
            s, e = self.new_state(), self.new_state()
            self.add_edge(s, node[1], e)
            return s, e

        if kind == "concat":
            s1, e1 = self.build(node[1])
            s2, e2 = self.build(node[2])
            self.add_edge(e1, EPSILON, s2)
            return s1, e2

        if kind == "union":
            s, e = self.new_state(), self.new_state()
            s1, e1 = self.build(node[1])
            s2, e2 = self.build(node[2])
            self.add_edge(s, EPSILON, s1)
            self.add_edge(s, EPSILON, s2)
            self.add_edge(e1, EPSILON, e)
            self.add_edge(e2, EPSILON, e)
            return s, e

        if kind == "*":
            s, e = self.new_state(), self.new_state()
            s1, e1 = self.build(node[1])
            self.add_edge(s, EPSILON, s1)
            self.add_edge(s, EPSILON, e)
            self.add_edge(e1, EPSILON, s1)
            self.add_edge(e1, EPSILON, e)
            return s, e

        if kind == "+":
            s1, e1 = self.build(node[1])
            e = self.new_state()
            self.add_edge(e1, EPSILON, s1)
            self.add_edge(e1, EPSILON, e)
            return s1, e

        if kind == "?":
            s, e = self.new_state(), self.new_state()
            s1, e1 = self.build(node[1])
            self.add_edge(s, EPSILON, s1)
            self.add_edge(s, EPSILON, e)
            self.add_edge(e1, EPSILON, e)
            return s, e

        raise RegexSyntaxError("Internal error: unknown node type.")


def regex_to_enfa(pattern):
    """Compile a regex string into an EpsilonNFA."""
    tree = parse_regex(pattern)
    builder = _FragmentBuilder()
    start, end = builder.build(tree)

    alphabet = sorted({sym for (s, sym) in builder.transitions if sym != EPSILON})

    return EpsilonNFA(
        states=builder.states,
        alphabet=alphabet,
        transitions=builder.transitions,
        start_state=start,
        final_states=[end],
    ), tree


def test_string(pattern, input_string):
    enfa, _tree = regex_to_enfa(pattern)
    try:
        result = enfa.run(input_string)
    except AutomatonInputError:
        # A symbol outside the pattern's own alphabet can never be matched,
        # so this is simply a rejection, not an error to surface.
        result = {
            "input_string": input_string,
            "snapshots": [],
            "log": [],
            "final_active_states": [],
            "accepted": False,
        }
    return enfa, result


REGEX_EXAMPLES = [
    {"label": "(a|b)*abb", "pattern": "(a|b)*abb", "sample_input": "aabb"},
    {"label": "a(b|c)*", "pattern": "a(b|c)*", "sample_input": "abcbc"},
    {"label": "(0|1)*1", "pattern": "(0|1)*1", "sample_input": "1011"},
]
