"""Monty execution helpers for agent logic."""

from typing import Any

import pydantic_monty

# Cache compiled Monty instances to avoid re-parsing on each invocation
_monty_cache: dict[str, pydantic_monty.Monty] = {}


def run_monty(
    code: str,
    *,
    inputs: dict[str, Any],
    external_functions: dict[str, Any] | None = None,
    type_check: bool = False,
    type_check_stubs: str | None = None,
    timeout_ms: int | None = None,
) -> Any:
    """Execute Monty code with the given inputs and external functions.

    Args:
        code: Python code to execute via Monty runtime.
        inputs: Dictionary of input values accessible to the code.
        external_functions: Optional dict of external Python functions callable from Monty code.
        type_check: Whether to enable type checking (slow).
        type_check_stubs: Optional type stubs for type checking.
        timeout_ms: Optional execution timeout in milliseconds (0 = no timeout).

    Returns:
        Result value returned by the Monty code.
    """
    external_functions = external_functions or {}

    # Create a cache key from code and type-checking config
    cache_key = (code, type_check, type_check_stubs)

    # Return cached Monty instance if available
    if cache_key in _monty_cache:
        monty = _monty_cache[cache_key]
    else:
        kwargs: dict[str, Any] = {
            "inputs": list(inputs.keys()),
            "external_functions": list(external_functions.keys()),
            "type_check": type_check,
        }
        if type_check_stubs is not None:
            kwargs["type_check_stubs"] = type_check_stubs

        monty = pydantic_monty.Monty(code, **kwargs)
        _monty_cache[cache_key] = monty

    # Run with optional timeout
    run_kwargs: dict[str, Any] = {
        "inputs": inputs,
        "external_functions": external_functions,
    }
    if timeout_ms is not None and timeout_ms > 0:
        run_kwargs["timeout"] = timeout_ms

    return monty.run(**run_kwargs)
