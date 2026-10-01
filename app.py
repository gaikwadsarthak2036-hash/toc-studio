"""
Theory of Computation Simulator (TOC Studio)
----------------------------------------------
Main Flask application file.

This file only wires together routes and templates. The actual
simulation logic for each module lives inside the `modules/` package
so that this file stays small and easy to read.

All 9 modules are implemented:
    1. Set Operations         5. epsilon-NFA
    2. Relation & Function    6. Regular Expression
    3. DFA                    7. CFG
    4. NFA                    8. PDA
                               9. Turing Machine

Every page route renders a template with a form + "load example" buttons.
Every module also exposes a small JSON API endpoint (POST /api/<module>/...)
that the page's own JavaScript calls to run the actual computation. Errors
from bad input are always caught and turned into a friendly JSON message --
never a raw Python traceback.
"""

from flask import Flask, render_template, request, jsonify

from modules.set_operations import parse_set, compute_all, SetInputError
from modules.relation import (
    parse_pairs, analyze_relation, analyze_function, compose_functions,
    RelationInputError,
)
from modules.dfa import build_dfa_from_form, AutomatonInputError
from modules.nfa import build_nfa_from_form
from modules.enfa import build_enfa_from_form
from modules.regex import test_string, RegexSyntaxError, REGEX_EXAMPLES
from modules.cfg import test_membership, CFGInputError, CFG_EXAMPLES
from modules.pda import build_pda_from_form, PDA_EXAMPLES
from modules.turing_machine import build_tm_from_form, TM_EXAMPLES

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Static data describing every module shown on the dashboard.
# ---------------------------------------------------------------------------
MODULES = [
    {
        "id": "set", "name": "Set Operations", "icon": "set",
        "description": "Union, intersection, difference, power set and more, with clean set-notation output.",
        "route": "/set", "available": True,
    },
    {
        "id": "relation", "name": "Relation & Function", "icon": "relation",
        "description": "Test reflexivity, symmetry and transitivity, and explore functions as mappings.",
        "route": "/relation", "available": True,
    },
    {
        "id": "dfa", "name": "DFA", "icon": "dfa",
        "description": "Build a Deterministic Finite Automaton and watch it accept or reject strings.",
        "route": "/dfa", "available": True,
    },
    {
        "id": "nfa", "name": "NFA", "icon": "nfa",
        "description": "Explore non-determinism by tracking every active state at once.",
        "route": "/nfa", "available": True,
    },
    {
        "id": "enfa", "name": "\u03b5-NFA", "icon": "enfa",
        "description": "Work with epsilon transitions and compute epsilon closures step by step.",
        "route": "/enfa", "available": True,
    },
    {
        "id": "regex", "name": "Regular Expression", "icon": "regex",
        "description": "Test strings against a pattern and see it converted into an automaton.",
        "route": "/regex", "available": True,
    },
    {
        "id": "cfg", "name": "CFG", "icon": "cfg",
        "description": "Derive strings from a grammar and visualize the resulting parse tree.",
        "route": "/cfg", "available": True,
    },
    {
        "id": "pda", "name": "PDA", "icon": "pda",
        "description": "Simulate a Pushdown Automaton with a live, visual stack.",
        "route": "/pda", "available": True,
    },
    {
        "id": "tm", "name": "Turing Machine", "icon": "tm",
        "description": "Define transition rules and watch the tape and head move in real time.",
        "route": "/tm", "available": True,
    },
]


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html", modules=MODULES)


def _friendly_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


# =============================================================================
# 1. Set Operations
# =============================================================================
SET_EXAMPLES = [
    {"label": "Basic overlap", "set_a": "1, 2, 3", "set_b": "2, 3, 4"},
    {"label": "Disjoint sets", "set_a": "1, 2, 3", "set_b": "4, 5, 6"},
    {"label": "Letters, A is a subset of B", "set_a": "a, b", "set_b": "a, b, c, d"},
]


@app.route("/set")
def set_operations():
    return render_template("set.html", examples=SET_EXAMPLES)


@app.route("/api/set/compute", methods=["POST"])
def api_set_compute():
    data = request.get_json(silent=True) or {}
    try:
        set_a = parse_set(data.get("set_a", ""))
        set_b = parse_set(data.get("set_b", ""))
        return jsonify({"ok": True, "results": compute_all(set_a, set_b)})
    except SetInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong while reading that input. Please check the format.")


# =============================================================================
# 2. Relation & Function
# =============================================================================
@app.route("/relation")
def relation_page():
    return render_template("relation.html")


@app.route("/api/relation/analyze", methods=["POST"])
def api_relation_analyze():
    data = request.get_json(silent=True) or {}
    try:
        set_a = parse_set(data.get("set_a", ""))
        pairs = parse_pairs(data.get("pairs", ""))
        return jsonify({"ok": True, "results": analyze_relation(set_a, pairs)})
    except (SetInputError, RelationInputError) as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong reading that relation. Please check the format.")


@app.route("/api/relation/function", methods=["POST"])
def api_relation_function():
    data = request.get_json(silent=True) or {}
    try:
        domain = parse_set(data.get("domain", ""))
        codomain = parse_set(data.get("codomain", ""))
        mapping_pairs = parse_pairs(data.get("mapping", ""))
        results = analyze_function(domain, codomain, mapping_pairs)

        compose_result = None
        g_text = (data.get("mapping_g") or "").strip()
        if g_text:
            codomain_c = parse_set(data.get("codomain_c", ""))
            g_pairs = parse_pairs(g_text)
            g_analysis = analyze_function(codomain, codomain_c, g_pairs)
            f_map = {str(a): str(b) for (a, b) in mapping_pairs}
            g_map = {str(a): str(b) for (a, b) in g_pairs}
            composed = compose_functions(f_map, g_map)
            compose_result = {
                "composed": {str(k): str(v) for k, v in composed.items()},
                "g_analysis": g_analysis,
            }

        return jsonify({"ok": True, "results": results, "compose": compose_result})
    except (SetInputError, RelationInputError) as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong reading that function. Please check the format.")


# =============================================================================
# 3. DFA
# =============================================================================
@app.route("/dfa")
def dfa_page():
    return render_template("dfa.html")


@app.route("/api/dfa/run", methods=["POST"])
def api_dfa_run():
    data = request.get_json(silent=True) or {}
    try:
        machine = build_dfa_from_form(
            data.get("states", ""), data.get("alphabet", ""),
            data.get("transitions", []), data.get("start_state", ""),
            data.get("final_states", ""),
        )
        result = machine.run(data.get("input_string", ""))
        return jsonify({"ok": True, "table": machine.transition_table(), "result": result})
    except AutomatonInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong building that DFA. Please check the definition.")


# =============================================================================
# 4. NFA
# =============================================================================
@app.route("/nfa")
def nfa_page():
    return render_template("nfa.html")


@app.route("/api/nfa/run", methods=["POST"])
def api_nfa_run():
    data = request.get_json(silent=True) or {}
    try:
        machine = build_nfa_from_form(
            data.get("states", ""), data.get("alphabet", ""),
            data.get("transitions", []), data.get("start_state", ""),
            data.get("final_states", ""),
        )
        result = machine.run(data.get("input_string", ""))
        return jsonify({"ok": True, "table": machine.transition_table(), "result": result})
    except AutomatonInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong building that NFA. Please check the definition.")


# =============================================================================
# 5. epsilon-NFA
# =============================================================================
@app.route("/enfa")
def enfa_page():
    return render_template("enfa.html")


@app.route("/api/enfa/run", methods=["POST"])
def api_enfa_run():
    data = request.get_json(silent=True) or {}
    try:
        machine = build_enfa_from_form(
            data.get("states", ""), data.get("alphabet", ""),
            data.get("transitions", []), data.get("start_state", ""),
            data.get("final_states", ""),
        )
        result = machine.run(data.get("input_string", ""))
        return jsonify({
            "ok": True,
            "table": machine.transition_table(),
            "closures": machine.closures_for_all_states(),
            "nfa_conversion": machine.to_nfa_transitions(),
            "result": result,
        })
    except AutomatonInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong building that \u03b5-NFA. Please check the definition.")


# =============================================================================
# 6. Regular Expression
# =============================================================================
@app.route("/regex")
def regex_page():
    return render_template("regex.html", examples=REGEX_EXAMPLES)


@app.route("/api/regex/test", methods=["POST"])
def api_regex_test():
    data = request.get_json(silent=True) or {}
    pattern = data.get("pattern", "")
    input_string = data.get("input_string", "")
    try:
        enfa, result = test_string(pattern, input_string)
        return jsonify({
            "ok": True,
            "table": enfa.transition_table(),
            "start_state": enfa.start_state,
            "final_states": sorted(enfa.final_states),
            "result": result,
        })
    except RegexSyntaxError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong reading that regular expression.")


# =============================================================================
# 7. CFG
# =============================================================================
@app.route("/cfg")
def cfg_page():
    return render_template("cfg.html", examples=CFG_EXAMPLES)


@app.route("/api/cfg/derive", methods=["POST"])
def api_cfg_derive():
    data = request.get_json(silent=True) or {}
    grammar_text = data.get("grammar", "")
    target = data.get("input_string", "")
    try:
        result = test_membership(grammar_text, target)
        return jsonify({"ok": True, "result": result})
    except CFGInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong reading that grammar. Please check the format.")


# =============================================================================
# 8. PDA
# =============================================================================
@app.route("/pda")
def pda_page():
    return render_template("pda.html", examples=PDA_EXAMPLES)


@app.route("/api/pda/run", methods=["POST"])
def api_pda_run():
    data = request.get_json(silent=True) or {}
    try:
        machine = build_pda_from_form(
            data.get("states", ""), data.get("input_alphabet", ""),
            data.get("stack_alphabet", ""), data.get("transitions", []),
            data.get("start_state", ""), data.get("initial_stack_symbol", ""),
            data.get("final_states", ""),
        )
        result = machine.run(data.get("input_string", ""))
        return jsonify({"ok": True, "rows": machine.transition_list(), "result": result})
    except AutomatonInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong building that PDA. Please check the definition.")


# =============================================================================
# 9. Turing Machine
# =============================================================================
@app.route("/tm")
def tm_page():
    return render_template("tm.html", examples=TM_EXAMPLES)


@app.route("/api/tm/run", methods=["POST"])
def api_tm_run():
    data = request.get_json(silent=True) or {}
    try:
        machine = build_tm_from_form(
            data.get("states", ""), data.get("tape_alphabet", ""),
            data.get("input_alphabet", ""), data.get("blank_symbol", ""),
            data.get("transitions", []), data.get("start_state", ""),
            data.get("final_states", ""),
        )
        result = machine.run(data.get("input_string", ""))
        return jsonify({"ok": True, "rows": machine.transition_list(), "result": result})
    except AutomatonInputError as e:
        return _friendly_error(str(e))
    except Exception:
        return _friendly_error("Something went wrong building that Turing Machine. Please check the definition.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
