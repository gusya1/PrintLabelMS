import moy_sklad


def test_get_assortment_returns_materialized_list(monkeypatch):
    items = [object(), object()]
    monkeypatch.setattr("moy_sklad.Assortment.gen_list", lambda: iter(items))
    result = moy_sklad.get_assortment()
    assert isinstance(result, list)
    assert result == items
