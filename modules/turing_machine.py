"""
Turing Machine module.

A Turing Machine reads/writes on an infinite tape (modeled here as a list
that grows in either direction as the head moves off the end) and moves its
head left or right after every step. It has no built-in notion of
"accept/reject" during a run -- the usual convention, used here, is: the
machine accepts if it halts (no transition defined for the current
state/symbol) in one of the designated final states.
"""

from modules.dfa import AutomatonInputError, _split_list

MAX_STEPS = 2000  # safety limit so a non-halting machine can't hang the server


class TuringMachine:
    def __init__(self, states, tape_alphabet, input_alphabet, blank_symbol,
                 start_state, final_states, transitions):
        """
        transitions: dict[(state, read_symbol)] -> (write_symbol, move, next_state)
        move is "L" or "R".
        """
        self.states = states
        self.tape_alphabet = tape_alphabet
        self.input_alphabet = input_alphabet
        self.blank_symbol = blank_symbol
        self.start_state = start_state
        self.final_states = set(final_states)
        self.transitions = transitions
        self._validate()

    def _validate(self):
        if not self.states:
            raise AutomatonInputError("Define at least one state.")
        if self.blank_symbol not in self.tape_alphabet:
            raise AutomatonInputError('The blank symbol "{}" must be part of the tape alphabet.'.format(self.blank_symbol))
        if self.start_state not in self.states:
            raise AutomatonInputError('Start state "{}" is not in the list of states.'.format(self.start_state))
        for f in self.final_states:
            if f not in self.states:
                raise AutomatonInputError('Final state "{}" is not in the list of states.'.format(f))
        for sym in self.input_alphabet:
            if sym not in self.tape_alphabet:
                raise AutomatonInputError('Input symbol "{}" must also be part of the tape alphabet.'.format(sym))

        for (state, read), (write, move, nxt) in self.transitions.items():
            if state not in self.states:
                raise AutomatonInputError('Transition uses undefined state "{}".'.format(state))
            if read not in self.tape_alphabet:
                raise AutomatonInputError('Transition reads undefined tape symbol "{}".'.format(read))
            if write not in self.tape_alphabet:
                raise AutomatonInputError('Transition writes undefined tape symbol "{}".'.format(write))
            if move not in ("L", "R"):
                raise AutomatonInputError('Move must be "L" or "R", got "{}".'.format(move))
            if nxt not in self.states:
                raise AutomatonInputError('Transition moves to undefined state "{}".'.format(nxt))

    def run(self, input_string):
        for ch in input_string:
            if ch not in self.input_alphabet:
                raise AutomatonInputError(
                    'Symbol "{}" in the input string is not part of the input alphabet.'.format(ch)
                )

        tape = list(input_string) if input_string else [self.blank_symbol]
        head = 0
        state = self.start_state
        history = []
        steps = 0
        halted_by_transition = False

        while steps < MAX_STEPS:
            if head < 0:
                tape.insert(0, self.blank_symbol)
                head = 0
            if head >= len(tape):
                tape.append(self.blank_symbol)

            symbol = tape[head]
            history.append({
                "step": steps,
                "tape": list(tape),
                "head": head,
                "state": state,
                "read": symbol,
            })

            key = (state, symbol)
            if key not in self.transitions:
                halted_by_transition = True
                break

            write, move, next_state = self.transitions[key]
            tape[head] = write
            head += 1 if move == "R" else -1
            state = next_state
            steps += 1

        accepted = halted_by_transition and state in self.final_states

        return {
            "input_string": input_string,
            "history": history,
            "final_state": state,
            "final_tape": tape,
            "final_head": head,
            "halted": halted_by_transition,
            "accepted": accepted,
            "step_count": steps,
        }

    def transition_list(self):
        rows = []
        for (state, read), (write, move, nxt) in sorted(self.transitions.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            rows.append({"state": state, "read": read, "write": write, "move": move, "next_state": nxt})
        return rows


def build_tm_from_form(states_text, tape_alphabet_text, input_alphabet_text, blank_symbol,
                        transitions_list, start_state, final_states_text):
    """transitions_list: list of dicts {"state","read","write","move","next_state"}"""
    states = _split_list(states_text)
    tape_alphabet = _split_list(tape_alphabet_text)
    input_alphabet = _split_list(input_alphabet_text)
    final_states = _split_list(final_states_text)
    start_state = (start_state or "").strip()
    blank_symbol = (blank_symbol or "").strip()

    transitions = {}
    for t in transitions_list:
        state = (t.get("state") or "").strip()
        read = (t.get("read") or "").strip()
        write = (t.get("write") or "").strip()
        move = (t.get("move") or "").strip().upper()
        next_state = (t.get("next_state") or "").strip()
        if state == "" or read == "" or write == "" or next_state == "":
            continue
        transitions[(state, read)] = (write, move, next_state)

    return TuringMachine(states, tape_alphabet, input_alphabet, blank_symbol,
                          start_state, final_states, transitions)


TM_EXAMPLES = [
    {
        "label": "Increment a binary number by 1",
        "states": "q0, q1, qf",
        "tape_alphabet": "0, 1, _",
        "input_alphabet": "0, 1",
        "blank_symbol": "_",
        "start_state": "q0",
        "final_states": "qf",
        "transitions": [
            {"state": "q0", "read": "0", "write": "0", "move": "R", "next_state": "q0"},
            {"state": "q0", "read": "1", "write": "1", "move": "R", "next_state": "q0"},
            {"state": "q0", "read": "_", "write": "_", "move": "L", "next_state": "q1"},
            {"state": "q1", "read": "1", "write": "0", "move": "L", "next_state": "q1"},
            {"state": "q1", "read": "0", "write": "1", "move": "R", "next_state": "qf"},
            {"state": "q1", "read": "_", "write": "1", "move": "R", "next_state": "qf"},
        ],
        "sample_input": "1011",
    },
    {
        "label": "Accept strings of the form 0^n 1^n",
        "states": "q0, q1, q2, q3, qf",
        "tape_alphabet": "0, 1, X, Y, _",
        "input_alphabet": "0, 1",
        "blank_symbol": "_",
        "start_state": "q0",
        "final_states": "qf",
        "transitions": [
            {"state": "q0", "read": "0", "write": "X", "move": "R", "next_state": "q1"},
            {"state": "q0", "read": "Y", "write": "Y", "move": "R", "next_state": "q3"},
            {"state": "q1", "read": "0", "write": "0", "move": "R", "next_state": "q1"},
            {"state": "q1", "read": "Y", "write": "Y", "move": "R", "next_state": "q1"},
            {"state": "q1", "read": "1", "write": "Y", "move": "L", "next_state": "q2"},
            {"state": "q2", "read": "0", "write": "0", "move": "L", "next_state": "q2"},
            {"state": "q2", "read": "Y", "write": "Y", "move": "L", "next_state": "q2"},
            {"state": "q2", "read": "X", "write": "X", "move": "R", "next_state": "q0"},
            {"state": "q3", "read": "Y", "write": "Y", "move": "R", "next_state": "q3"},
            {"state": "q3", "read": "_", "write": "_", "move": "R", "next_state": "qf"},
        ],
        "sample_input": "0011",
    },
    {
        "label": "Unary successor: append one more 1",
        "states": "q0, qf",
        "tape_alphabet": "1, _",
        "input_alphabet": "1",
        "blank_symbol": "_",
        "start_state": "q0",
        "final_states": "qf",
        "transitions": [
            {"state": "q0", "read": "1", "write": "1", "move": "R", "next_state": "q0"},
            {"state": "q0", "read": "_", "write": "1", "move": "R", "next_state": "qf"},
        ],
        "sample_input": "111",
    },
]
