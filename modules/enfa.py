"""
epsilon-NFA module.

Adds epsilon (\u03b5) transitions on top of an NFA: a state can move to another
state "for free", without consuming an input symbol. The key extra idea is
the epsilon closure of a state (or set of states): every state reachable
using only epsilon transitions.
"""

from modules.dfa import AutomatonInputError, _split_list

EPSILON = "\u03b5"


class EpsilonNFA:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        """
        transitions: dict[(state, symbol_or_EPSILON)] -> list[state]
        """
        self.states = states
        self.alphabet = alphabet  # does NOT include epsilon
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = set(final_states)
        self._validate()

    def _validate(self):
        if not self.states:
            raise AutomatonInputError("Define at least one state.")
        if self.start_state not in self.states:
            raise AutomatonInputError('Start state "{}" is not in the list of states.'.format(self.start_state))
        for f in self.final_states:
            if f not in self.states:
                raise AutomatonInputError('Final state "{}" is not in the list of states.'.format(f))
        if len(set(self.states)) != len(self.states):
            raise AutomatonInputError("Duplicate state names found.")

        for (state, symbol), targets in self.transitions.items():
            if state not in self.states:
                raise AutomatonInputError('Transition uses undefined state "{}".'.format(state))
            if symbol != EPSILON and symbol not in self.alphabet:
                raise AutomatonInputError('Transition uses undefined symbol "{}".'.format(symbol))
            for t in targets:
                if t not in self.states:
                    raise AutomatonInputError(
                        '\u03b4({}, {}) points to undefined state "{}".'.format(state, symbol, t)
                    )

    def epsilon_closure(self, state_set):
        """All states reachable from state_set using only epsilon moves."""
        stack = list(state_set)
        closure = set(state_set)
        while stack:
            s = stack.pop()
            for t in self.transitions.get((s, EPSILON), []):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return closure

    def transition_table(self):
        rows = []
        edges = []
        for s in self.states:
            cells = {}
            for sym in [EPSILON] + self.alphabet:
                targets = self.transitions.get((s, sym), [])
                cells[sym] = "{" + ", ".join(targets) + "}" if targets else "\u2205"
                for t in targets:
                    edges.append({"from": s, "to": t, "symbol": sym})
            rows.append({"state": s, "cells": cells})
        return {
            "states": self.states,
            "alphabet": [EPSILON] + self.alphabet,
            "start_state": self.start_state,
            "final_states": sorted(self.final_states),
            "rows": rows,
            "edges": edges,
        }

    def closures_for_all_states(self):
        return {s: sorted(self.epsilon_closure({s})) for s in self.states}

    def run(self, input_string):
        for ch in input_string:
            if ch not in self.alphabet:
                raise AutomatonInputError(
                    'Symbol "{}" in the input string is not part of the alphabet.'.format(ch)
                )

        active = self.epsilon_closure({self.start_state})
        log = [{"stage": "start + \u03b5-closure", "symbol": None, "active": sorted(active)}]
        snapshots = [sorted(active)]

        for ch in input_string:
            moved = set()
            for s in active:
                moved.update(self.transitions.get((s, ch), []))
            closed = self.epsilon_closure(moved)
            log.append({
                "stage": "consume",
                "symbol": ch,
                "moved_to": sorted(moved),
                "active": sorted(closed),
            })
            active = closed
            snapshots.append(sorted(active))
            if not active:
                break

        accepted = any(s in self.final_states for s in active)

        return {
            "input_string": input_string,
            "snapshots": snapshots,
            "log": log,
            "final_active_states": sorted(active),
            "accepted": accepted,
        }

    def to_nfa_transitions(self):
        """Subset-construction-lite: build an equivalent NFA (without epsilon)
        over the SAME state names, by folding epsilon moves into each direct
        transition. This keeps the conversion easy to read for students,
        at the cost of possibly adding a few redundant transitions.
        """
        new_transitions = {}
        new_finals = set(self.final_states)

        for s in self.states:
            closure_s = self.epsilon_closure({s})
            if closure_s & self.final_states:
                new_finals.add(s)
            for sym in self.alphabet:
                targets = set()
                for mid in closure_s:
                    for t in self.transitions.get((mid, sym), []):
                        targets.update(self.epsilon_closure({t}))
                if targets:
                    new_transitions[(s, sym)] = sorted(targets)

        return {
            "states": self.states,
            "alphabet": self.alphabet,
            "start_state": self.start_state,
            "final_states": sorted(new_finals),
            "transitions": {
                "{}|{}".format(k[0], k[1]): v for k, v in new_transitions.items()
            },
        }


def build_enfa_from_form(states_text, alphabet_text, transitions_list, start_state, final_states_text):
    """transitions_list: list of dicts {"from", "symbol" (may be 'eps'/'e'/EPSILON), "to"}"""
    states = _split_list(states_text)
    alphabet = _split_list(alphabet_text)
    final_states = _split_list(final_states_text)
    start_state = (start_state or "").strip()

    transitions = {}
    for t in transitions_list:
        frm = (t.get("from") or "").strip()
        sym = (t.get("symbol") or "").strip()
        if sym.lower() in ("eps", "e", "epsilon", EPSILON):
            sym = EPSILON
        to_targets = _split_list(t.get("to") or "")
        if frm == "" or sym == "" or not to_targets:
            continue
        transitions.setdefault((frm, sym), [])
        for tgt in to_targets:
            if tgt not in transitions[(frm, sym)]:
                transitions[(frm, sym)].append(tgt)

    return EpsilonNFA(states, alphabet, transitions, start_state, final_states)
