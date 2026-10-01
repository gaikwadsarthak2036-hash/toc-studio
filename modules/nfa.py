"""
NFA (Non-deterministic Finite Automaton) module.

Unlike a DFA, a state/symbol pair can map to *several* next states (or none
at all). We simulate this by tracking the whole set of "active states" after
each symbol, which is the standard way to run an NFA without exploring every
path individually.
"""

from modules.dfa import AutomatonInputError, _split_list


class NFA:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        """
        transitions: dict[(state, symbol)] -> list[state]
        """
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = set(final_states)
        self._validate()

    def _validate(self):
        if not self.states:
            raise AutomatonInputError("Define at least one state.")
        if not self.alphabet:
            raise AutomatonInputError("Define at least one input symbol.")
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
            if symbol not in self.alphabet:
                raise AutomatonInputError('Transition uses undefined symbol "{}".'.format(symbol))
            for t in targets:
                if t not in self.states:
                    raise AutomatonInputError(
                        '\u03b4({}, {}) points to undefined state "{}".'.format(state, symbol, t)
                    )

    def transition_table(self):
        rows = []
        edges = []
        for s in self.states:
            cells = {}
            for sym in self.alphabet:
                targets = self.transitions.get((s, sym), [])
                cells[sym] = "{" + ", ".join(targets) + "}" if targets else "\u2205"
                for t in targets:
                    edges.append({"from": s, "to": t, "symbol": sym})
            rows.append({"state": s, "cells": cells})
        return {
            "states": self.states,
            "alphabet": self.alphabet,
            "start_state": self.start_state,
            "final_states": sorted(self.final_states),
            "rows": rows,
            "edges": edges,
        }

    def run(self, input_string):
        for ch in input_string:
            if ch not in self.alphabet:
                raise AutomatonInputError(
                    'Symbol "{}" in the input string is not part of the alphabet.'.format(ch)
                )

        active = {self.start_state}
        log = []
        snapshots = [sorted(active)]

        for ch in input_string:
            nxt = set()
            for s in active:
                nxt.update(self.transitions.get((s, ch), []))
            log.append({"from": sorted(active), "symbol": ch, "to": sorted(nxt)})
            active = nxt
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


def build_nfa_from_form(states_text, alphabet_text, transitions_list, start_state, final_states_text):
    """transitions_list: list of dicts {"from": .., "symbol": .., "to": "q1,q2"}"""
    states = _split_list(states_text)
    alphabet = _split_list(alphabet_text)
    final_states = _split_list(final_states_text)
    start_state = (start_state or "").strip()

    transitions = {}
    for t in transitions_list:
        frm = (t.get("from") or "").strip()
        sym = (t.get("symbol") or "").strip()
        to_targets = _split_list(t.get("to") or "")
        if frm == "" or sym == "" or not to_targets:
            continue
        transitions.setdefault((frm, sym), [])
        for tgt in to_targets:
            if tgt not in transitions[(frm, sym)]:
                transitions[(frm, sym)].append(tgt)

    return NFA(states, alphabet, transitions, start_state, final_states)
