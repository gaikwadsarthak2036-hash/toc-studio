"""
DFA (Deterministic Finite Automaton) module.

A DFA is defined by:
  - a set of states
  - an alphabet of input symbols
  - a transition function: exactly one next state for every (state, symbol)
  - one start state
  - a set of final (accepting) states
"""


class AutomatonInputError(Exception):
    """Raised when a DFA/NFA/etc. definition or input string is invalid."""
    pass


def _split_list(raw_text):
    """Turn "q0, q1, q2" into ["q0", "q1", "q2"], trimming blanks."""
    if raw_text is None:
        return []
    items = [x.strip() for x in raw_text.split(",")]
    return [x for x in items if x != ""]


class DFA:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        """
        states: list[str]
        alphabet: list[str] (single-character symbols)
        transitions: dict[(state, symbol)] -> state
        start_state: str
        final_states: list[str]
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

        for state in self.states:
            for symbol in self.alphabet:
                if (state, symbol) not in self.transitions:
                    raise AutomatonInputError(
                        'Missing transition for state "{}" on symbol "{}". '
                        "A DFA needs exactly one transition for every state/symbol pair."
                        .format(state, symbol)
                    )
                target = self.transitions[(state, symbol)]
                if target not in self.states:
                    raise AutomatonInputError(
                        'Transition \u03b4({}, {}) = "{}" points to an undefined state.'
                        .format(state, symbol, target)
                    )

    def transition_table(self):
        return {
            "states": self.states,
            "alphabet": self.alphabet,
            "start_state": self.start_state,
            "final_states": sorted(self.final_states),
            "rows": [
                {
                    "state": s,
                    "cells": {sym: self.transitions[(s, sym)] for sym in self.alphabet},
                }
                for s in self.states
            ],
        }

    def run(self, input_string):
        """Execute the DFA on input_string, returning a step-by-step trace."""
        for ch in input_string:
            if ch not in self.alphabet:
                raise AutomatonInputError(
                    'Symbol "{}" in the input string is not part of the alphabet.'.format(ch)
                )

        path = [self.start_state]
        log = []
        current = self.start_state

        for ch in input_string:
            nxt = self.transitions[(current, ch)]
            log.append({"from": current, "symbol": ch, "to": nxt})
            current = nxt
            path.append(current)

        accepted = current in self.final_states

        return {
            "input_string": input_string,
            "path": path,
            "log": log,
            "final_state": current,
            "accepted": accepted,
        }


def build_dfa_from_form(states_text, alphabet_text, transitions_list, start_state, final_states_text):
    """Build a DFA object from raw form fields.

    transitions_list: list of dicts like {"from": "q0", "symbol": "0", "to": "q1"}
    """
    states = _split_list(states_text)
    alphabet = _split_list(alphabet_text)
    final_states = _split_list(final_states_text)
    start_state = (start_state or "").strip()

    transitions = {}
    for t in transitions_list:
        frm = (t.get("from") or "").strip()
        sym = (t.get("symbol") or "").strip()
        to = (t.get("to") or "").strip()
        if frm == "" or sym == "" or to == "":
            continue
        transitions[(frm, sym)] = to

    return DFA(states, alphabet, transitions, start_state, final_states)
