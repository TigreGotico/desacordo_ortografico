import pytest

from desacordo_ortografico import detect
from desacordo_ortografico.detect import Orthography
from desacordo_ortografico.eras import Era, Variant


def _orth(text):
    r = detect(text)
    assert isinstance(r, Orthography), f"expected Portuguese, got {r}"
    return r


class TestEraDetection:
    @pytest.mark.parametrize(
        "text",
        ["pharmacia e theatro", "a orthographia do lyrio", "elle tinha pharmacia"],
    )
    def test_etymological(self, text):
        assert _orth(text).era == Era.ETYMOLOGICAL

    @pytest.mark.parametrize(
        "text",
        ["o facto é óptimo", "a direcção está correcta", "o pêlo do animal"],
    )
    def test_pre_ao90_pt(self, text):
        r = _orth(text)
        assert r.era == Era.PT_1973
        assert r.variant == Variant.PT

    @pytest.mark.parametrize("text", ["idéia e vôo", "a freqüência da lingüiça"])
    def test_pre_ao90_br(self, text):
        r = _orth(text)
        assert r.era == Era.BR_1971
        assert r.variant == Variant.BR

    @pytest.mark.parametrize("text", ["a ação direta", "ótima coleção objetiva"])
    def test_ao1990(self, text):
        assert _orth(text).era == Era.AO1990

    def test_nfd_input_is_normalised(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "óptimo acção recepção")
        assert _orth(nfd).era == Era.PT_1973

    @pytest.mark.parametrize(
        "text",
        [
            "a piscina tem água",        # 'sci' in piscina is modern, not etymological
            "a consciência pesa",        # 'sci' in consciência
            "comummente erramos",        # 'mm' survives in modern European PT
            "estamos connosco",          # 'nn' survives in modern European PT
        ],
    )
    def test_modern_geminate_sci_not_etymological(self, text):
        assert _orth(text).era != Era.ETYMOLOGICAL


class TestVariantDetection:
    def test_nasal_acute_is_pt(self):
        assert _orth("antónio é económico").variant == Variant.PT

    def test_nasal_circumflex_is_br(self):
        assert _orth("antônio é econômico").variant == Variant.BR

    def test_ambiguous_variant_is_none(self):
        # words identical in both AO1990 norms -> variant undetermined
        assert _orth("a ação direta").variant is None


class TestId:
    @pytest.mark.parametrize(
        "text,expected_id",
        [
            ("a pharmacia do theatro", "etymological"),
            ("o facto é óptimo", "pt_1973"),
            ("a idéia do vôo", "br_1971"),
            ("o Antônio é econômico", "ao1990-br"),
            ("o António é económico", "ao1990-pt"),
        ],
    )
    def test_id_matches_readme(self, text, expected_id):
        # .id is a canonical norm id (only AO1990 carries a variant suffix)
        assert _orth(text).id == expected_id

    def test_id_round_trips_into_convert(self):
        from desacordo_ortografico import convert
        r = _orth("o facto é óptimo")
        assert convert("óptimo", r.id, "ao1990-pt") == "ótimo"


class TestConfidence:
    def test_strong_markers_high_confidence(self):
        assert _orth("pharmacia e theatro").confidence >= 0.8

    def test_featureless_text_low_confidence(self):
        r = _orth("a casa azul")
        assert r.era == Era.AO1990
        assert r.confidence < 0.5

    def test_markers_are_reported(self):
        assert _orth("pharmacia").markers





class TestArchaicEvidence:
    """Pre-1911 evidence comes from listed archaic forms only: the 1911 word map of this
    package and the tugalex archaisms list (``TugaLexicon.archaic_words``). The expected
    labels follow the Formulário Ortográfico of 1911 (Portal da Língua Portuguesa, ILTEC).
    """

    @pytest.mark.parametrize(
        "text",
        [
            # meio milhão de frases rows mmf-021699, mmf-025898, pilot-201, mmf-454536
            "Por fim, Duncan Laurence, vencedor pela Holanda em 2019, cantou You'll Never "
            "Walk Alone, de Gerry and the Pacemakers, com a ajuda de várias outras vozes.",
            "Folha Você acha possível repetir o sucesso do hit «U Can't Touch This»?",
            "O Tom e a Mary disseram que ficariam em Boston?",
            "Chama-se He's a Bully, Charlie Brown e foi originalmente idealizado por Charles "
            "Schulz e contava, entre os dubladores, com o ator Taylor Lautner, então criança.",
        ],
    )
    def test_foreign_words_are_no_evidence(self, text):
        """Base I of 1911 proscribes k, w and y in "palavras portuguesas, ou
        aportuguesadas" only. The, This, Mary and Taylor are English words and names, no
        pre-1911 Portuguese form, and neither list holds them. With no other marker the
        sentence is AO1990."""
        assert _orth(text).era == Era.AO1990

    @pytest.mark.parametrize(
        "text, archaism",
        [
            # Eça de Queirós, A Cidade e as Serras (Project Gutenberg 18220), 1901
            ("Que magestoso armazem dos productos do Raciocinio e da Imaginação!", "productos"),
            ("Ao meio dia, um tam-tam argentino e melancholico ressoava, chamando ao almoço.",
             "melancholico"),
            ("Ouve lá, tu hoje jantas commigo e com uns amigos, Zé Fernandes?", "commigo"),
        ],
    )
    def test_listed_archaisms_are_evidence(self, text, archaism):
        """The tugalex list holds each word. Base VI of 1911 writes the ch of [k] as c
        (melancólico, as "técnica, cloro"), base VII doubles no consonant but rr, ss, mm
        and nn where pronounced (comigo), and base VIII drops a silent consonant that does
        not change the vowel before it ("autor, restrito, produto")."""
        r = _orth(text)
        assert r.era == Era.ETYMOLOGICAL
        assert f"etym-pattern:{archaism}" in r.markers

    @pytest.mark.parametrize(
        "text",
        [
            "A pharmacia do theatro vendia fósforos.",  # silver row s01
            "Livre-me d'ella, se póde!",  # mmf-314974
            "Tem uma collecção curiosa.",  # A Cidade e as Serras (Gutenberg 18220)
        ],
    )
    def test_common_archaisms_still_count(self, text):
        """Base VI of 1911 writes ph as f and drops the h of th ("O grupo ph será
        expresso por f", "teatro"): pharmacia, theatro. Base VII writes "ela" with one l:
        ella, collecção."""
        assert _orth(text).era == Era.ETYMOLOGICAL
