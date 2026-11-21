from riskminer.extract.validate import check_quote, normalize, quote_in

NOWOGARD = ("W trakcie realizacji prac ziemnych ujawniono niekorzystne warunki gruntowe oraz miejscowy wysoki "
            "poziom wód<br/>gruntowych. W celu prawidłowego wykonania zamówienia konieczne było wydłużenie terminu.")


def test_normalize_both_sides():
    assert normalize("„Ala”\xa0ma – kota") == normalize('"ala" ma - KOTA')
    assert normalize("prze-\nsyłu") == "przesyłu"


def test_quote_with_ellipsis_and_br():
    assert quote_in("niekorzystne warunki gruntowe … wysoki poziom wód gruntowych", NOWOGARD)
    assert not quote_in("wysoki poziom wód gruntowych … niekorzystne warunki gruntowe", NOWOGARD)
    assert not quote_in("kolizja z siecią gazową", NOWOGARD)
    assert check_quote("służebności przesyłu", None, "Konieczność ustanowienia służebności przesyłu na działce nr 3/39")
