"""
Context-Free Grammar module.

Productions are written like:

    S -> aSb | eps

Membership and derivation are both found the same way a student would do
it by hand: starting from the start symbol, repeatedly expand the
LEFTMOST nonterminal using every production, in a breadth-first search
over sentential forms, until either the target string is produced or a
safety limit is hit. This works well for the small, typical textbook
grammars this simulator targets (it is not a general polynomial-time CFG
parser, which is intentionally out of scope for a teaching tool).
"""

from collections import deque

EPSILON_SYMBOLS = {"\u03b5", "epsilon", "eps", "@", "\u03bb"}

MAX_STRING_LEN = 40      # sentential forms longer than the target are pruned
MAX_STEPS = 20000        # safety limit on search size


class CFGInputError(Exception):
    pass


def parse_grammar(raw_text):
    """Parse lines like:
        S -> aSb | eps
        A -> aA | a
    into a dict: {"S": [("a","S","b"), ()], "A": [("a","A"), ("a",)]}

    Nonterminals are any single uppercase letter found as a production head.
    Everything else in a body is treated as a terminal character, except
    another uppercase letter, which is a nonterminal reference.
    """
    if not raw_text or not raw_text.strip():
        raise CFGInputError("Enter at least one production.")

    grammar = {}
    start_symbol = None

    for line_no, raw_line in enumerate(raw_text.strip().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "->" not in line and "\u2192" not in line:
            raise CFGInputError(
                'Line {} is missing "->". Expected something like "S -> aSb".'.format(line_no)
            )
        arrow = "->" if "->" in line else "\u2192"
        head, _, body_text = line.partition(arrow)
        head = head.strip()

        if len(head) != 1 or not head.isupper():
            raise CFGInputError(
                'Line {}: production head "{}" must be a single uppercase nonterminal.'.format(line_no, head)
            )

        if start_symbol is None:
            start_symbol = head

        grammar.setdefault(head, [])

        for alt in body_text.split("|"):
            alt = alt.strip()
            if alt in EPSILON_SYMBOLS or alt == "":
                grammar[head].append(())
                continue
            body = tuple(alt)
            grammar[head].append(body)

    if not grammar:
        raise CFGInputError("No valid productions were found.")

    return grammar, start_symbol


def _is_nonterminal(symbol, grammar):
    return symbol.isupper() and symbol in grammar


def _leftmost_nonterminal_index(form, grammar):
    for i, sym in enumerate(form):
        if _is_nonterminal(sym, grammar):
            return i
    return -1


def derive(grammar, start_symbol, target):
    """Breadth-first search for a leftmost derivation of `target`.

    Returns a dict: {"found": bool, "steps": [...], "parse_tree": {...}|None}
    `steps` is a list of {"form": "aSb", "expanded": "S", "production": "aSb"}
    describing each leftmost-expansion, suitable for direct display.
    """
    start_form = (start_symbol,)

    initial_tree = {"symbol": start_symbol, "children": None}
    queue = deque()
    queue.append((start_form, [], initial_tree))
    visited = {start_form}
    steps_examined = 0

    while queue:
        steps_examined += 1
        if steps_examined > MAX_STEPS:
            break

        form, steps_so_far, tree_root = queue.popleft()

        idx = _leftmost_nonterminal_index(form, grammar)

        if idx == -1:
            if "".join(form) == target:
                final_text = "".join(form) if form else "\u03b5"
                return {
                    "found": True,
                    "steps": steps_so_far,
                    "final_form": final_text,
                    "parse_tree": tree_root,
                }
            continue

        nonterminal = form[idx]
        for body in grammar.get(nonterminal, []):
            new_form = form[:idx] + body + form[idx + 1:]
            if len(new_form) > MAX_STRING_LEN:
                continue
            if new_form in visited:
                continue
            visited.add(new_form)

            new_form_text = "".join(new_form) if new_form else "\u03b5"
            body_text = "".join(body) if body else "\u03b5"
            step = {
                "form": new_form_text,
                "expanded": nonterminal,
                "production": "{} \u2192 {}".format(nonterminal, body_text),
            }

            new_tree_root = _copy_tree(tree_root)
            target_node = _find_nth_open_nonterminal(new_tree_root, idx)
            children = [{"symbol": sym, "children": None} for sym in body] if body else \
                       [{"symbol": "\u03b5", "children": []}]
            target_node["children"] = children

            queue.append((new_form, steps_so_far + [step], new_tree_root))

    return {"found": False, "steps": [], "final_form": None, "parse_tree": None}


def _copy_tree(node):
    if node["children"] is None:
        return {"symbol": node["symbol"], "children": None}
    return {
        "symbol": node["symbol"],
        "children": [_copy_tree(c) for c in node["children"]],
    }


def _find_nth_open_nonterminal(root, n):
    """Find the n-th (0-indexed, left-to-right) leaf whose 'children' is
    still None -- this corresponds to the leftmost-nonterminal position in
    the current sentential form.
    """
    open_leaves = []

    def collect(node):
        if node["children"] is None:
            open_leaves.append(node)
        else:
            for c in node["children"]:
                collect(c)

    collect(root)
    return open_leaves[n]


def _rightmost_nonterminal_index(form, grammar):
    for i in range(len(form) - 1, -1, -1):
        if _is_nonterminal(form[i], grammar):
            return i
    return -1


def derive_rightmost(grammar, start_symbol, target):
    """Same idea as derive(), but always expands the RIGHTMOST nonterminal.
    Used only to show the rightmost-derivation sequence; the parse tree
    shown to the user comes from the leftmost search since, for the small
    unambiguous textbook grammars this tool targets, both derivations
    correspond to the same tree.
    """
    start_form = (start_symbol,)
    queue = deque()
    queue.append((start_form, []))
    visited = {start_form}
    steps_examined = 0

    while queue:
        steps_examined += 1
        if steps_examined > MAX_STEPS:
            break

        form, steps_so_far = queue.popleft()
        idx = _rightmost_nonterminal_index(form, grammar)

        if idx == -1:
            if "".join(form) == target:
                return {"found": True, "steps": steps_so_far}
            continue

        nonterminal = form[idx]
        for body in grammar.get(nonterminal, []):
            new_form = form[:idx] + body + form[idx + 1:]
            if len(new_form) > MAX_STRING_LEN:
                continue
            if new_form in visited:
                continue
            visited.add(new_form)

            new_form_text = "".join(new_form) if new_form else "\u03b5"
            body_text = "".join(body) if body else "\u03b5"
            step = {
                "form": new_form_text,
                "expanded": nonterminal,
                "production": "{} \u2192 {}".format(nonterminal, body_text),
            }
            queue.append((new_form, steps_so_far + [step]))

    return {"found": False, "steps": []}


def test_membership(raw_text, target_string):
    grammar, start_symbol = parse_grammar(raw_text)
    result = derive(grammar, start_symbol, target_string)
    rightmost = derive_rightmost(grammar, start_symbol, target_string)
    result["rightmost_steps"] = rightmost["steps"]
    result["grammar"] = {k: ["".join(b) if b else "\u03b5" for b in v] for k, v in grammar.items()}
    result["start_symbol"] = start_symbol
    return result


CFG_EXAMPLES = [
    {"label": "Balanced a's and b's: S -> aSb | eps", "grammar": "S -> aSb | eps", "sample_input": "aaabbb"},
    {"label": "a's then b's, at least one each: S -> aSb | ab", "grammar": "S -> aSb | ab", "sample_input": "aabb"},
    {"label": "Palindromes over 0/1: S -> 0S0 | 1S1 | 0 | 1 | eps", "grammar": "S -> 0S0 | 1S1 | 0 | 1 | eps", "sample_input": "0110"},
]
