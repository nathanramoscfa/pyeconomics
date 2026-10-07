# .semgrep/tests/dynamic-code.py
# Test cases for .semgrep/rules/dynamic-code.yaml (semgrep --test).
# Deliberately unsafe code: excluded from the bandit and semgrep hooks.
import ast
import builtins


def cases(expression, frame):
    # ruleid: dynamic-code
    eval(expression)
    # ruleid: dynamic-code
    exec(expression)
    # ruleid: dynamic-code
    eval(expression, {"__builtins__": {}})
    # ruleid: dynamic-code
    builtins.eval(expression)
    # ruleid: dynamic-code
    builtins.exec(expression)

    # ok: dynamic-code
    ast.literal_eval(expression)
    # ok: dynamic-code
    frame.eval("a + b")
    # ok: dynamic-code
    evaluate = len(expression)
    return evaluate
