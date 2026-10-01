"""
Relation & Function module.

Covers two related but distinct ideas from DSCAT:
  - A relation on a set A: a collection of ordered pairs (a, b) with a, b in A.
  - A function: a special relation from a domain to a codomain where every
    domain element maps to exactly one codomain element.
"""

from modules.set_operations import parse_set, SetInputError  # reuse the same set parser


class RelationInputError(Exception):
    """Raised when relation/function text can't be parsed."""
    pass


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_pairs(raw_text):
    """Parse text like "(1,1),(1,2),(2,2),(3,3)" into a list of (a, b) tuples.

    Elements inside each pair follow the same int-or-string rule as sets.
    """
    if raw_text is None:
        raise RelationInputError("Relation/mapping input is missing.")

    text = raw_text.strip()
    if text == "":
        return []

    pairs = []
    depth = 0
    current = ""
    chunks = []
    # Split on commas that are NOT inside parentheses, e.g.
    # "(1,1),(1,2)" -> ["(1,1)", "(1,2)"]
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            chunks.append(current)
            current = ""
        else:
            current += ch
    if current.strip() != "":
        chunks.append(current)

    for chunk in chunks:
        item = chunk.strip()
        if not (item.startswith("(") and item.endswith(")")):
            raise RelationInputError(
                'Each pair must look like "(a, b)". Found: "{}".'.format(item)
            )
        inner = item[1:-1]
        parts = inner.split(",")
        if len(parts) != 2:
            raise RelationInputError(
                'Each pair needs exactly two elements, like "(1, 2)". Found: "{}".'.format(item)
            )
        a, b = parts[0].strip(), parts[1].strip()
        if a == "" or b == "":
            raise RelationInputError('Found an empty element in pair "{}".'.format(item))
        pairs.append((_coerce(a), _coerce(b)))

    return pairs


def _coerce(item):
    try:
        return int(item)
    except ValueError:
        return item


def format_pairs(pairs):
    if not pairs:
        return "\u2205"
    ordered = sorted(pairs, key=lambda p: [str(x) for x in p])
    return "{" + ", ".join("({}, {})".format(a, b) for a, b in ordered) + "}"


# ---------------------------------------------------------------------------
# Relation properties
# ---------------------------------------------------------------------------

def analyze_relation(set_a, pairs):
    """Check every standard property of a relation R on set A."""
    elements = sorted(set_a, key=str)
    pair_set = set(pairs)

    # Every pair must use elements that are actually in A.
    for a, b in pairs:
        if a not in set_a or b not in set_a:
            raise RelationInputError(
                'Pair ({}, {}) uses an element not in set A.'.format(a, b)
            )

    is_reflexive = all((a, a) in pair_set for a in elements)
    is_irreflexive = all((a, a) not in pair_set for a in elements)
    is_symmetric = all((b, a) in pair_set for (a, b) in pair_set)
    is_antisymmetric = all(
        (a == b) or (b, a) not in pair_set for (a, b) in pair_set
    )
    is_transitive = all(
        (a, c) in pair_set
        for (a, b) in pair_set
        for (b2, c) in pair_set
        if b == b2
    )
    is_equivalence = is_reflexive and is_symmetric and is_transitive
    is_partial_order = is_reflexive and is_antisymmetric and is_transitive

    matrix = [[1 if (a, b) in pair_set else 0 for b in elements] for a in elements]

    return {
        "elements": [str(e) for e in elements],
        "matrix": matrix,
        "pairs_formatted": format_pairs(pairs),
        "is_reflexive": is_reflexive,
        "is_irreflexive": is_irreflexive,
        "is_symmetric": is_symmetric,
        "is_antisymmetric": is_antisymmetric,
        "is_transitive": is_transitive,
        "is_equivalence": is_equivalence,
        "is_partial_order": is_partial_order,
        "graph_nodes": [str(e) for e in elements],
        "graph_edges": [[str(a), str(b)] for (a, b) in sorted(pair_set, key=lambda p: [str(x) for x in p])],
    }


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def analyze_function(domain, codomain, mapping_pairs):
    """Check that `mapping_pairs` defines a valid function domain -> codomain,
    then test injective / surjective / bijective / identity.
    """
    mapping = {}
    for a, b in mapping_pairs:
        if a not in domain:
            raise RelationInputError('"{}" is mapped but is not in the domain.'.format(a))
        if b not in codomain:
            raise RelationInputError('"{}" is not in the codomain.'.format(b))
        if a in mapping:
            raise RelationInputError(
                'Element "{}" is mapped more than once -- a function needs exactly one output per input.'.format(a)
            )
        mapping[a] = b

    missing = [a for a in domain if a not in mapping]
    if missing:
        raise RelationInputError(
            "Every element of the domain needs a mapping. Missing: " +
            ", ".join(str(m) for m in missing)
        )

    images = list(mapping.values())
    is_injective = len(images) == len(set(images))
    is_surjective = set(images) == set(codomain)
    is_bijective = is_injective and is_surjective
    is_identity = (domain == codomain) and all(mapping[a] == a for a in domain)

    inverse = None
    if is_bijective:
        inverse = {v: k for k, v in mapping.items()}

    return {
        "mapping": {str(k): str(v) for k, v in mapping.items()},
        "is_injective": is_injective,
        "is_surjective": is_surjective,
        "is_bijective": is_bijective,
        "is_identity": is_identity,
        "inverse": {str(k): str(v) for k, v in inverse.items()} if inverse else None,
    }


def compose_functions(mapping_f, mapping_g):
    """Compute g(f(x)) for every x in f's domain, given two plain dicts.

    mapping_f: domain -> intermediate values (function f)
    mapping_g: intermediate values -> final values (function g)
    Returns the composed mapping g∘f, or raises if some f(x) has no g mapping.
    """
    composed = {}
    for x, fx in mapping_f.items():
        if fx not in mapping_g:
            raise RelationInputError(
                'g is not defined for "{}", so g\u2218f("{}") is undefined.'.format(fx, x)
            )
        composed[x] = mapping_g[fx]
    return composed
