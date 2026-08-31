from app import is_even

def test_even():
    assert is_even(4) is True
    assert is_even(3) is False
