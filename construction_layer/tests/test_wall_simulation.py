def test_wall_cost():
    from construction_layer.use_cases.simulate_wall import cost
    assert cost > 0
