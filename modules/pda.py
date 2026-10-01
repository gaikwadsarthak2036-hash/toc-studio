"""
Pushdown Automaton module.

A PDA is an NFA plus a stack. Each transition looks at the current state,
the next input symbol (or epsilon), and the symbol on top of the stack,
then moves to a new state and replaces the top stack symbol with zero or
more symbols.

Because PDAs are non-deterministic, we search (breadth-first) over all
possible configurations for one that accepts the whole input by final
state, and return that one accepting run's step-by-step trace for display.
"""

from collections import deque
from modules.dfa import AutomatonInputError, _split_list

EPSILON = "\u03b5"
MAX_CONFIGS = 20000  # safety limit so a bad/looping PDA can't hang the server


class PDA:
    def __init__(self, states, input_alphabet, stack_alphabet, transitions,
                 start_state, initial_stack_symbol, final_states):
        """
        transitions: dict[(state, input_symbol_or_EPSILON, stack_top)] ->
                     list[(next_state, push_string)]
                     push_string is a string of stack symbols to push, read
                     left-to-right, so the LAST character ends up on top.
                     "" means pop with nothing pushed back (a plain pop).
        """
        self.states = states
        self.input_alphabet = input_alphabet
        self.stack_alphabet = stack_alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.initial_stack_symbol = initial_stack_symbol
        self.final_states = set(final_states)
        self._validate()

    def _validate(self):
        if not self.states:
            raise AutomatonInputError("Define at least one state.")
        if self.start_state not in self.states:
            raise AutomatonInputError('Start state "{}" is not in the list of states.'.format(self.start_state))
        if self.initial_stack_symbol not in self.stack_alphabet:
            raise AutomatonInputError('Initial stack symbol "{}" must be part of the stack alphabet.'.format(self.initial_stack_symbol))
        for f in self.final_states:
            if f not in self.states:
                raise AutomatonInputError('Final state "{}" is not in the list of states.'.format(f))

        for (state, sym, top), moves in self.transitions.items():
            if state not in self.states:
                raise AutomatonInputError('Transition uses undefined state "{}".'.format(state))
            if sym != EPSILON and sym not in self.input_alphabet:
                raise AutomatonInputError('Transition uses undefined input symbol "{}".'.format(sym))
            if top not in self.stack_alphabet:
                raise AutomatonInputError('Transition uses undefined stack symbol "{}".'.format(top))
            for (nxt, push) in moves:
                if nxt not in self.states:
                    raise AutomatonInputError('Transition moves to undefined state "{}".'.format(nxt))
                for ch in push:
                    if ch not in self.stack_alphabet:
                        raise AutomatonInputError('Transition pushes undefined stack symbol "{}".'.format(ch))

    def run(self, input_string):
        for ch in input_string:
            if ch not in self.input_alphabet:
                raise AutomatonInputError(
                    'Symbol "{}" in the input string is not part of the input alphabet.'.format(ch)
                )

        # A configuration is (state, remaining_input_index, stack_tuple, path_so_far)
        # stack_tuple[-1] is the TOP of the stack.
        start_config = (self.start_state, 0, (self.initial_stack_symbol,))
        queue = deque()
        queue.append((start_config, []))
        seen = set()
        examined = 0

        while queue:
            examined += 1
            if examined > MAX_CONFIGS:
                break

            (state, pos, stack), trace = queue.popleft()
            config_key = (state, pos, stack)
            if config_key in seen:
                continue
            seen.add(config_key)

            input_done = pos == len(input_string)
            if input_done and state in self.final_states:
                return {
                    "input_string": input_string,
                    "accepted": True,
                    "trace": trace,
                    "final_state": state,
                    "final_stack": list(stack),
                }

            if not stack:
                continue  # nowhere to go without a stack top -- dead end
            top = stack[-1]

            # Try epsilon moves first, then moves that consume a symbol.
            candidates = []
            for (s, sym, t), moves in self.transitions.items():
                if s != state or t != top:
                    continue
                if sym == EPSILON:
                    candidates.append((sym, moves, pos))
                elif not input_done and sym == input_string[pos]:
                    candidates.append((sym, moves, pos + 1))

            for sym, moves, new_pos in candidates:
                for (next_state, push) in moves:
                    new_stack = stack[:-1] + tuple(push)
                    if len(new_stack) > 60:
                        continue  # guard against runaway stack growth
                    step = {
                        "from_state": state,
                        "symbol": sym if sym != EPSILON else EPSILON,
                        "popped": top,
                        "pushed": push if push else EPSILON,
                        "to_state": next_state,
                        "remaining_input": input_string[new_pos:],
                        "stack_after": list(new_stack),
                    }
                    queue.append(((next_state, new_pos, new_stack), trace + [step]))

        return {
            "input_string": input_string,
            "accepted": False,
            "trace": [],
            "final_state": None,
            "final_stack": None,
        }

    def transition_list(self):
        rows = []
        for (state, sym, top), moves in sorted(self.transitions.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
            for (nxt, push) in moves:
                rows.append({
                    "from": state,
                    "symbol": sym,
                    "pop": top,
                    "to": nxt,
                    "push": push if push else EPSILON,
                })
        return rows


def build_pda_from_form(states_text, input_alphabet_text, stack_alphabet_text,
                         transitions_list, start_state, initial_stack_symbol, final_states_text):
    """transitions_list: list of dicts:
       {"from", "symbol" (or 'eps'), "pop", "to", "push" (or 'eps'/'')}
    """
    states = _split_list(states_text)
    input_alphabet = _split_list(input_alphabet_text)
    stack_alphabet = _split_list(stack_alphabet_text)
    final_states = _split_list(final_states_text)
    start_state = (start_state or "").strip()
    initial_stack_symbol = (initial_stack_symbol or "").strip()

    transitions = {}
    for t in transitions_list:
        frm = (t.get("from") or "").strip()
        sym = (t.get("symbol") or "").strip()
        pop = (t.get("pop") or "").strip()
        to = (t.get("to") or "").strip()
        push = (t.get("push") or "").strip()

        if sym.lower() in ("eps", "e", "epsilon", EPSILON):
            sym = EPSILON
        if push.lower() in ("eps", "e", "epsilon", EPSILON):
            push = ""

        if frm == "" or pop == "" or to == "":
            continue

        key = (frm, sym, pop)
        transitions.setdefault(key, [])
        transitions[key].append((to, push))

    return PDA(states, input_alphabet, stack_alphabet, transitions,
               start_state, initial_stack_symbol, final_states)


PDA_EXAMPLES = [
    {
        "label": "a^n b^n (equal a's then b's)",
        "states": "q0, q1, q2",
        "input_alphabet": "a, b",
        "stack_alphabet": "Z, A",
        "start_state": "q0",
        "initial_stack_symbol": "Z",
        "final_states": "q2",
        "transitions": [
            {"from": "q0", "symbol": "a", "pop": "Z", "to": "q0", "push": "ZA"},
            {"from": "q0", "symbol": "a", "pop": "A", "to": "q0", "push": "AA"},
            {"from": "q0", "symbol": "b", "pop": "A", "to": "q1", "push": ""},
            {"from": "q1", "symbol": "b", "pop": "A", "to": "q1", "push": ""},
            {"from": "q0", "symbol": "eps", "pop": "Z", "to": "q2", "push": "Z"},
            {"from": "q1", "symbol": "eps", "pop": "Z", "to": "q2", "push": "Z"},
        ],
        "sample_input": "aaabbb",
    },
    {
        "label": "Palindromes over 0/1 with center marker (ww^R)",
        "states": "q0, q1, q2",
        "input_alphabet": "0, 1",
        "stack_alphabet": "Z, X, Y",
        "start_state": "q0",
        "initial_stack_symbol": "Z",
        "final_states": "q2",
        "transitions": [
            {"from": "q0", "symbol": "0", "pop": "Z", "to": "q0", "push": "ZX"},
            {"from": "q0", "symbol": "1", "pop": "Z", "to": "q0", "push": "ZY"},
            {"from": "q0", "symbol": "0", "pop": "X", "to": "q0", "push": "XX"},
            {"from": "q0", "symbol": "1", "pop": "X", "to": "q0", "push": "XY"},
            {"from": "q0", "symbol": "0", "pop": "Y", "to": "q0", "push": "YX"},
            {"from": "q0", "symbol": "1", "pop": "Y", "to": "q0", "push": "YY"},
            {"from": "q0", "symbol": "eps", "pop": "Z", "to": "q1", "push": "Z"},
            {"from": "q0", "symbol": "eps", "pop": "X", "to": "q1", "push": "X"},
            {"from": "q0", "symbol": "eps", "pop": "Y", "to": "q1", "push": "Y"},
            {"from": "q1", "symbol": "0", "pop": "X", "to": "q1", "push": ""},
            {"from": "q1", "symbol": "1", "pop": "Y", "to": "q1", "push": ""},
            {"from": "q1", "symbol": "eps", "pop": "Z", "to": "q2", "push": "Z"},
        ],
        "sample_input": "0110",
    },
]
