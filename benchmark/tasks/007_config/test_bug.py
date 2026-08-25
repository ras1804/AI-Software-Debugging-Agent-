from config import api_url
def test_default(monkeypatch):
    monkeypatch.delenv("API_URL", raising=False)
    assert api_url() == "http://localhost"
