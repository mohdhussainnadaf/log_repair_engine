from target_app.main import calculate_discount

def test_calculate_discount_valid():
    assert calculate_discount(100, 20) == 99.8

def test_calculate_discount_zero_price():
    assert calculate_discount(0, 10) == 0.0
