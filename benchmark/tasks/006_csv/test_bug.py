from transform import first_name
def test_snake_case():
    assert first_name({"first_name":"Ada"}) == "Ada"
