from pricing import price
def test_discount_fraction():
    assert price(100, 20) == 80
