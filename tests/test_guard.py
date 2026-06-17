import pytest

from desacordo_ortografico import detect, detect_sister
from desacordo_ortografico.detect import Orthography
from desacordo_ortografico.guard import NotPortuguese


class TestSisterLanguages:
    @pytest.mark.parametrize(
        "text,lang",
        [
            ("umha cançom", "gl"),
            ("nom hai nengumha relaçom", "gl"),
            ("l mirandés ye ua lhéngua", "mwl"),
            ("you falo la lhéngua mirandesa", "mwl"),
            ("oh irmõih ehtá na bê labá", "oki-barranquenho"),
            ("e'hcrebê un poema en barranquenhu", "oki-barranquenho"),
        ],
    )
    def test_flagged(self, text, lang):
        r = detect(text)
        assert isinstance(r, NotPortuguese)
        assert r.lang == lang
        assert r.convertible is False
        assert r.is_portuguese is False

    def test_status_is_reported(self):
        r = detect_sister("oh irmõih ehtá na bê labá")
        assert "Lei n. 97/2021" in r.status


class TestPortugueseNotFlagged:
    @pytest.mark.parametrize(
        "text",
        [
            "o gato preto subiu ao telhado",
            "a ação direta é ótima",
            "o facto é que está tudo bem",
            "pharmacia e theatro antigos",
            "uma menina com meia azul",  # 'meia' must not trip the Galician/accent markers
            "ninguém respondeu à pergunta",
            "ele deu-lhe a chave de casa",       # enclitic -lhe must not look like Mirandese lh-
            "a idéia do vôo deu-lhe alegria",    # enclitic -lhe inside pre-AO90 BR text
            "disse-lhes que partíamos cedo",
        ],
    )
    def test_not_sister(self, text):
        assert detect_sister(text) is None
        assert isinstance(detect(text), Orthography)
