"""
Set Operations module.

All the "math" for the Set Operations Simulator lives here, kept separate
from app.py so the Flask file only has to worry about routing.

A user types a set as text, e.g.  1, 2, 3   or   {1, 2, 3}
We parse that text into a real Python set, then run whichever operations
were requested and format the results back into set notation such as
"{1, 2, 3}" for display.
"""


MAX_SET_SIZE = 50


class SetInputError(Exception):
    """Raised when the user's set text can't be parsed.

    We use a custom exception (instead of letting a random Python error
    bubble up) so app.py can catch exactly this and show a friendly
    message instead of a raw traceback.
    """
    pass


def parse_set(raw_text):
    """Convert user text like "{1, 2, 2, 3}" or "1,2,3" into a Python set.

    Rules:
      - Curly braces are optional and stripped if present.
      - Elements are separated by commas.
      - Empty input (after stripping braces/spaces) means the empty set.
      - Each element is tried as an integer first (so "2" and "2.0" don't
        silently become different elements); anything that isn't a valid
        integer is kept as a plain string, so sets of letters/words work
        too (e.g. "a, b, c").
      - Duplicate elements are automatically collapsed, matching real set
        semantics.
    """
    if raw_text is None:
        raise SetInputError("Set input is missing.")

    text = raw_text.strip()

    # Allow the user to type "{1,2,3}" or just "1,2,3".
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()

    if text == "":
        return set()

    elements = set()
    for piece in text.split(","):
        item = piece.strip()
        if item == "":
            raise SetInputError(
                "Found an empty element between commas. "
                "Check for a stray comma, e.g. \"1,,2\"."
            )
        elements.add(_coerce_element(item))

    if len(elements) > MAX_SET_SIZE:
        raise SetInputError(
            f"A set can contain at most {MAX_SET_SIZE} unique elements. "
            f"This input contains {len(elements)}."
        )

    return elements


def _coerce_element(item):
    """Turn a single element's text into an int when possible, else keep it
    as a string. This lets {1,2,3} and {a,b,c} both work naturally.
    """
    try:
        return int(item)
    except ValueError:
        return item


def format_set(py_set):
    """Format a Python set back into set notation for display.

    Elements are sorted when that's possible (all numbers, or all strings)
    so the output is stable and easy to read; if the set mixes types we
    fall back to sorting by their text representation.
    """
    if len(py_set) == 0:
        return "\u2205"  # the empty set symbol

    try:
        ordered = sorted(py_set)
    except TypeError:
        ordered = sorted(py_set, key=str)

    return "{" + ", ".join(str(el) for el in ordered) + "}"


def format_pairs(pairs):
    """Format a collection of (a, b) tuples as set notation, e.g.
    {(1, 2), (1, 3)}.
    """
    if len(pairs) == 0:
        return "\u2205"

    ordered = sorted(pairs, key=lambda p: [str(x) for x in p])
    body = ", ".join("({}, {})".format(a, b) for a, b in ordered)
    return "{" + body + "}"


def power_set(py_set):
    """Return the power set of py_set as a list of frozensets.

    Built with simple bit-counting: a set with n elements has 2^n subsets,
    and the bits of a number from 0 to 2^n - 1 tell us which elements to
    include in that subset.
    """
    items = list(py_set)
    n = len(items)
    subsets = []
    for mask in range(2 ** n):
        subset = frozenset(items[i] for i in range(n) if mask & (1 << i))
        subsets.append(subset)
    return subsets


def format_power_set(subsets):
    """Format a list of subsets (frozensets) as set notation, with the
    subsets ordered by size then contents so the output reads naturally.
    """
    def sort_key(s):
        try:
            return (len(s), sorted(s))
        except TypeError:
            return (len(s), sorted(s, key=str))

    ordered = sorted(subsets, key=sort_key)
    body = ", ".join(format_set(s) for s in ordered)
    return "{" + body + "}"


def compute_all(set_a, set_b):
    """Run every Set Operations Simulator calculation and return a plain
    dictionary that's easy to turn into JSON for the frontend.
    """
    union = set_a | set_b
    intersection = set_a & set_b
    difference_ab = set_a - set_b
    difference_ba = set_b - set_a
    symmetric_difference = set_a ^ set_b
    cartesian_product = {(a, b) for a in set_a for b in set_b}

    def sorted_elements(values):
        try:
            return sorted(values)
        except TypeError:
            return sorted(values, key=str)

    ordered_a = sorted_elements(set_a)
    ordered_b = sorted_elements(set_b)

    return {
        "elements_a": ordered_a,
        "elements_b": ordered_b,
        "union_elements": sorted_elements(union),
        "intersection_elements": sorted_elements(intersection),
        "difference_ab_elements": sorted_elements(difference_ab),
        "difference_ba_elements": sorted_elements(difference_ba),
        "symmetric_difference_elements": sorted_elements(symmetric_difference),
        "cartesian_pairs": sorted(cartesian_product, key=lambda p: (str(p[0]), str(p[1]))),
        "set_a": format_set(set_a),
        "set_b": format_set(set_b),
        "union": format_set(union),
        "intersection": format_set(intersection),
        "difference_ab": format_set(difference_ab),
        "difference_ba": format_set(difference_ba),
        "symmetric_difference": format_set(symmetric_difference),
        "cartesian_product": format_pairs(cartesian_product),
        "is_a_subset_of_b": set_a.issubset(set_b),
        "is_b_subset_of_a": set_b.issubset(set_a),
        "is_a_proper_subset_of_b": set_a < set_b,
        "is_b_proper_subset_of_a": set_b < set_a,
        "is_a_superset_of_b": set_a.issuperset(set_b),
        "is_b_superset_of_a": set_b.issuperset(set_a),
        # Enumerating P(A) grows as 2^n. Keep the simulator safe for the
        # 50-element input limit by displaying the full power set only for
        # small sets; for larger sets we still report its exact size.
        "power_set_a": format_power_set(power_set(set_a)) if len(set_a) <= 12
            else f"P(A) has {2 ** len(set_a):,} subsets; full visualization is disabled for large sets.",
        "power_set_a_size": 2 ** len(set_a),
        "power_set_b": format_power_set(power_set(set_b)) if len(set_b) <= 12
            else f"P(B) has {2 ** len(set_b):,} subsets; full visualization is disabled for large sets.",
        "power_set_b_size": 2 ** len(set_b),
    }
