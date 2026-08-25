from validators import positive_age
import pytest
def test_zero_invalid():
    with pytest.raises(ValueError):
        positive_age(0)
