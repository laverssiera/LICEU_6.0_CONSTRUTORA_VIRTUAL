# Assert determinístico para contratos soberanos

def deterministic_assert(actual, expected):
    assert actual == expected, f"Deterministic contract violation: {actual} != {expected}"
