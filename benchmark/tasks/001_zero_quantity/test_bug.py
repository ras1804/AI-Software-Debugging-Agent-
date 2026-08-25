from orders import orders
def test_zero_quantity():
    result=orders(0)
    assert result["total"] == 0
