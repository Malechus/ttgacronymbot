import json
import pytest
from ttgacronymbot.acronyms import AcronymStore


@pytest.fixture
def store(tmp_path):
    data = {"DPS": "Damage Per Second", "HP": "Hit Points", "OP": "Overpowered"}
    p = tmp_path / "acronyms.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return AcronymStore(str(p))


def test_store_loads_acronyms(store):
    assert len(store) == 3


def test_store_contains_known_acronym(store):
    assert "DPS" in store
    assert "dps" in store  # case-insensitive


def test_store_does_not_contain_unknown_acronym(store):
    assert "XYZ" not in store


def test_get_returns_definition(store):
    assert store.get("DPS") == "Damage Per Second"
    assert store.get("dps") == "Damage Per Second"


def test_get_returns_none_for_unknown(store):
    assert store.get("UNKNOWN") is None


def test_find_in_text_detects_acronyms(store):
    found = store.find_in_text("The DPS is great and HP is low")
    assert found == {"DPS": "Damage Per Second", "HP": "Hit Points"}


def test_find_in_text_returns_empty_when_no_matches(store):
    assert store.find_in_text("Nothing relevant here") == {}


def test_find_in_text_ignores_partial_matches(store):
    # "ADPS" should NOT match DPS — requires whole-word boundary
    found = store.find_in_text("The ADPS stat")
    assert "DPS" not in found


def test_load_normalises_keys_to_uppercase(tmp_path):
    data = {"dps": "Damage Per Second"}
    p = tmp_path / "acronyms.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    store = AcronymStore(str(p))
    assert "DPS" in store
