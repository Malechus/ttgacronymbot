import json
import pytest
from ttgacronymbot.acronyms import AcronymStore


@pytest.fixture
def store(tmp_path):
    data = {"DPS": "Damage Per Second", "HP": "Hit Points", "OP": "Overpowered"}
    p = tmp_path / "acronyms.jsonc"
    p.write_text(json.dumps(data), encoding="utf-8")
    return AcronymStore(str(p))


def test_store_loads_acronyms(store):
    assert len(store) == 3


def test_store_contains_known_acronym(store):
    assert "DPS" in store
    assert "dps" not in store  # case-sensitive


def test_store_does_not_contain_unknown_acronym(store):
    assert "XYZ" not in store


def test_get_returns_definition(store):
    assert store.get("DPS") == "Damage Per Second"
    assert store.get("dps") is None  # case-sensitive


def test_get_returns_none_for_unknown(store):
    assert store.get("UNKNOWN") is None


def test_find_in_text_detects_acronyms(store):
    found = store.find_in_text("The DPS is great and HP is low")
    assert found == {"DPS": "Damage Per Second", "HP": "Hit Points"}


def test_find_in_text_is_case_sensitive(store):
    assert store.find_in_text("the dps is low") == {}


def test_find_in_text_returns_empty_when_no_matches(store):
    assert store.find_in_text("Nothing relevant here") == {}


def test_find_in_text_ignores_partial_matches(store):
    # "ADPS" should NOT match DPS — requires whole-word boundary
    found = store.find_in_text("The ADPS stat")
    assert "DPS" not in found


def test_load_preserves_key_case(tmp_path):
    data = {"GComp": "Galaxy Compressor", "eHP": "Effective Health Points"}
    p = tmp_path / "acronyms.jsonc"
    p.write_text(json.dumps(data), encoding="utf-8")
    store = AcronymStore(str(p))
    assert "GComp" in store
    assert "GCOMP" not in store
    assert "eHP" in store
    assert store.find_in_text("Use GComp for coins and track eHP") == {
        "GComp": "Galaxy Compressor",
        "eHP": "Effective Health Points",
    }


def test_load_strips_line_comments(tmp_path):
    jsonc = '{\n  // line comment\n  "DPS": "Damage Per Second"\n}'
    p = tmp_path / "acronyms.jsonc"
    p.write_text(jsonc, encoding="utf-8")
    store = AcronymStore(str(p))
    assert "DPS" in store


def test_load_strips_block_comments(tmp_path):
    jsonc = '{ /* block comment */ "DPS": "Damage Per Second" }'
    p = tmp_path / "acronyms.jsonc"
    p.write_text(jsonc, encoding="utf-8")
    store = AcronymStore(str(p))
    assert "DPS" in store
