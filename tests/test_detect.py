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



class TestForeignTokens:
    """Modern rows of the meio milhão de frases corpus and pre-1911 sentences of Project
    Gutenberg books (source in each comment)."""

    @pytest.mark.parametrize(
        "text",
        [
            # mmf-454536: Taylor gives tailor under the 1911 rules, no Portuguese word
            "Chama-se He's a Bully, Charlie Brown e foi originalmente idealizado por Charles "
            "Schulz e contava, entre os dubladores, com o ator Taylor Lautner, então criança.",
            # mmf-019520: city and within give citi and witin
            "“It’s a concept, a city within a city”, diz-nos o José Correal durante uma tour "
            "pelo centro da cidade.",
            # mmf-033066: University gives universiti
            "Formação Graduado em comércio pela Queen's University em Kingston, Canadá.",
            # mmf-013512: photo gives foto, but mickey gives mickei
            "Mac Tonight também faz aparição em Five nights with Mac Tonight (mais conhecido "
            "por FNWMT) criado por Photo-Negative-Mickey, um fan-game de FNAF (Five Nights at "
            "Freddy's) criado por Scott Cawthon.",
        ],
    )
    def test_foreign_tokens_are_no_etymological_evidence(self, text):
        assert _orth(text).era == Era.AO1990

    @pytest.mark.parametrize(
        "text",
        [
            "Livre-me d'ella, se póde!",  # mmf-314974: the part ella gives ela
            "Rapazes a entrarem na vida são lá capazes d'um cynismo d'esses!",  # mmf-193977
            "Hum natural desejo tinha acceso D'algum ditoso e doce pensamento, "
            "Que m'illustrasse a insana mocidade.",  # mmf-test-03169
            # Eça de Queirós, A Cidade e as Serras (Gutenberg 18220): a name mid-sentence
            "E Jacintho, aturdido e deslumbrado, reconheceu o snr.",
            "Amarrotára com colera a carta começada--eu escapei, respirando, para a "
            "Bibliotheca.",
            # Teófilo Braga, Viriatho (Gutenberg 26850): the first word of a second sentence
            "Nenhum dos cachôpos dava com o sentido da adivinha. Viriatho ao passar pelo "
            "rancho sorriu-se, dizendo para os Maioraes que o acompanhavam:",
        ],
    )
    def test_pre_1911_spellings_still_count(self, text):
        assert _orth(text).era == Era.ETYMOLOGICAL
