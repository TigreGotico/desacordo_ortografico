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

    @pytest.mark.parametrize(
        "text,era,expected",
        [
            # the held-out precision of the label for its count of distinct evidence
            # tokens, lowest over the measured populations, as cal units correct/total
            ("A pharmacia fechou.", Era.ETYMOLOGICAL, 0.89),          # relabel 16/18
            ("pharmacia pharmacia", Era.ETYMOLOGICAL, 0.89),          # one distinct token
            ("Pharmacia PHARMACIA pharmacia", Era.ETYMOLOGICAL, 0.89),  # case is no new token
            ("A pharmacia do theatro tem um director.", Era.ETYMOLOGICAL, 0.99),
            ("a direcção mudou", Era.PT_1973, 0.79),                  # silver_corpus 392/497
            ("Chegou em Janeiro.", Era.PT_1973, 0.79),                # capital month only
            ("a direcção do actor", Era.PT_1973, 0.92),               # silver_full 2934/3180
            ("Eles lêem e crêem.", Era.PT_1973, 0.92),                # -êem only
            ("a idéia", Era.BR_1971, 0.95),                           # silver_full 1444/1520
            ("a idéia do vôo", Era.BR_1971, 0.99),
            ("Ele falava freqüentemente.", Era.BR_1971, 0.95),        # trema only
            ("a ação", Era.AO1990, 0.96),                             # silver_corpus 741/772
            ("ótima coleção objetiva", Era.AO1990, 0.95),             # silver_corpus 216/227
            ("o António come", Era.AO1990, 0.86),                     # silver_full 4942/5755
            ("a casa azul", Era.AO1990, 0.34),                        # no evidence at all
            # provisional: the etymological row, no held-out 1911 print (pg31347:71.4, 672.0)
            ("Vi-o chorar, àquele vélho de quási sessenta anos.", Era.REFORMA_1911, 0.89),
            ("Calmo, magníficamente fecundo, corria êle, o nobre rio do Paraíso, por entre "
             "as ilhas, quási afundadas sob o pêso rijo do rijo arvoredo todas fragrantes, e "
             "atroadas pelo clamor das cacatuas.", Era.REFORMA_1911, 0.99),
        ],
    )
    def test_confidence_is_measured_precision(self, text, era, expected):
        r = _orth(text)
        assert r.era == era
        assert r.confidence == expected





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


class TestNamesAreNoEvidence:
    """A listed archaic form that spells a name gives no pre-1911 evidence. Base XXI of
    the Acordo Ortográfico of 1990 (Portal da Língua Portuguesa text), "Das assinaturas e
    firmas": "Para ressalva de direitos, cada qual poderá manter a escrita que, por
    costume ou registo legal, adote na assinatura do seu nome. Com o mesmo fim, pode
    manter-se a grafia original de quaisquer firmas comerciais, nomes de sociedades,
    marcas e títulos que estejam inscritos em registo público."

    A word or a part of a word that starts with a capital inside a sentence is read as a
    name. The first word of a sentence and a text in capitals throughout give no case
    signal, so their listed forms still count.
    """

    @pytest.mark.parametrize(
        "text",
        [
            "Os anjos da Victoria desfilaram.",  # mmf-test-01366, Victoria's Secret
            "A Moraci Sant'Anna chegou.",  # mmf-271456
            "O preparador Sant'anna falou.",  # the word has the capital, the part anna not
            "A Hermínia d'Oliveira Paes saiu.",  # mmf-351075
            "Don't Be a Lemming Polka",  # mmf-010843
            "O retrato d'Anna Maria ficou na sala.",  # the part Anna has the capital
        ],
    )
    def test_names_inside_a_sentence_are_no_evidence(self, text):
        """Victoria, Anna, Paes and Polka are in the tugalex archaisms list. Here each one
        is a name or a title inside a sentence, and the sentence has no other marker, so
        it is AO1990."""
        r = _orth(text)
        assert r.era == Era.AO1990
        assert not [m for m in r.markers if m.startswith("etym")]

    @pytest.mark.parametrize(
        "text, archaism",
        [
            ("E d'ahi, que mal lhe faziam os padres e as irmãsinhas lá em casa?",
             "d'ahi"),  # mmf-294727
            ("O sol que morre tem clarões d'auroras, Águia que bate as azas pelos ceus!",
             "azas"),  # mmf-244985
            ("Entre os milhões d'astros o luar sem veo", "veo"),  # mmf-197966
            ("Quem vio tamanho enleio, Que houvesse ahi'sperança sem receio?",
             "ahi'sperança"),  # mmf-299798
        ],
    )
    def test_lowercase_archaisms_still_count(self, text, archaism):
        """Pre-1911 verse and prose: a lowercase listed form is no name."""
        r = _orth(text)
        assert r.era == Era.ETYMOLOGICAL
        assert f"etym-pattern:{archaism}" in r.markers

    @pytest.mark.parametrize("end", [". ", "! ", "? ", "… ", "\n"])
    def test_first_word_of_a_sentence_still_counts(self, end):
        """Commigo (comigo, base VII of 1911) opens the second sentence. Its capital comes
        from the sentence start, not from a name."""
        r = _orth(f"Ficou calado{end}Commigo ninguém falava.")
        assert r.era == Era.ETYMOLOGICAL
        assert "etym-pattern:commigo" in r.markers

    def test_first_word_of_the_text_still_counts(self):
        r = _orth("Commigo ninguém falava.")
        assert r.era == Era.ETYMOLOGICAL
        assert "etym-pattern:commigo" in r.markers

    def test_capital_after_a_comma_is_inside_the_sentence(self):
        r = _orth("Ficou calado, Commigo ninguém falava.")
        assert r.era == Era.AO1990

    @pytest.mark.parametrize(
        "text", ["OS ANJOS DA VICTORIA DESFILARAM.", "Os Anjos Da Victoria Desfilaram"])
    def test_text_with_no_lowercase_word_has_no_case_signal(self, text):
        """In capitals throughout or in title case, every word has the same case, so the
        capital of Victoria says nothing about a name."""
        r = _orth(text)
        assert r.era == Era.ETYMOLOGICAL
        assert "etym-pattern:victoria" in r.markers


class TestReforma1911:
    """reforma_1911 evidence is a form that the Formulário Ortográfico of 1911 prints and
    Brazilian print of 1943 does not. The expected labels follow the source of each text:
    pg31347 is Eça de Queirós, Contos, 3rd edition, Chardron 1913, printed in the 1911
    spelling; the Formulário Ortográfico of 1943 (ABL page) is Brazilian 1943 print; the
    other books are printed before 1911.
    """

    @pytest.mark.parametrize(
        "text, marker",
        [
            # Base XIV: "receberão o acento circunflexo quando forem polissilabos com a
            # última sílaba predominante"
            ("Tambêm sei!", "tambêm"),  # pg31347:236.13
            ("Os filhos, duas rapariguitas e um rapaz, eram tambêm doentes, crescendo pouco "
             "e com dificuldade, cheios de tumores nas orelhas, chorões e tristonhos.",
             "tambêm"),  # pg31347:391.4
            ("Mas Jacinto ergueu os ombros, com seguro desdêm.", "desdêm"),  # pg31347:545.2
            ("Mas ninguêm se chegou à janela de peitoril, com caixilhos verdes.",
             "ninguêm"),  # pg31347:77.6
            # Base XXIV: "mas, quási, Vénus, órfã(s)"
            ("Vi-o chorar, àquele vélho de quási sessenta anos.", "quási"),  # pg31347:71.4
            # Base XLVI: "fre qùente, a gùentar, ar gùir"
            ("No entanto estava tranqùilo.", "tranqùilo"),  # pg31347:169.1
            # Base XXXV: "a acentuação com o agudo ... mantém-se ...: fácilmente"
            ("A raínha chorou magníficamente o rei.", "magníficamente"),  # pg31347:724.0
        ],
    )
    def test_1911_print_is_reforma_1911(self, text, marker):
        r = _orth(text)
        assert r.era == Era.REFORMA_1911
        assert r.variant is None
        assert r.id == "reforma_1911"
        assert f"reforma-1911:{marker}" in r.markers

    def test_as_many_1911_forms_as_pre_1911_forms_is_reforma_1911(self):
        """pg31347:948.0. The 1913 print keeps emquanto against 1911 Base XV ("conquanto,
        com n, e não com m"), beside one 1911 form."""
        text = ("Recusei e abalei--emquanto êle, indiferente à minha fuga, estendido na "
                "poltrona, acendia trémulamente um imenso charuto.")
        r = _orth(text)
        assert "etym-pattern:emquanto" in r.markers
        assert r.era == Era.REFORMA_1911

    @pytest.mark.parametrize(
        "text",
        [
            # Camilo Castelo Branco, Novelas do Minho (Gutenberg 21406), pg21406:402.0
            "--Não, minha senhora, veio sómente esta folha.",
            # Perdigão Malheiro, Indice chronologico (Gutenberg 22044), pg22044:404.12
            "Porêm alguns Deputados reunem-se aos Senadores que se achavão ainda no Senado, "
            "envião a S.",
        ],
    )
    def test_forms_printed_before_1911_are_no_1911_evidence(self, text):
        """Base XXV writes porêm and Base XXXV writes sómente, but books printed before
        1911 have both, so neither tells a 1911 print."""
        r = _orth(text)
        assert r.era != Era.REFORMA_1911
        assert not [m for m in r.markers if m.startswith("reforma-1911")]

    def test_id_is_a_norm_id(self):
        from desacordo_ortografico.eras import Norm
        norm = Norm.parse(_orth("Tambêm sei!").id)
        assert norm.era == Era.REFORMA_1911

    @pytest.mark.parametrize(
        "text",
        [
            # F1943:156.1 and F1943:205.0: the pronoun circumflex of 1943 rule 14.ª
            "Dentro dêsse princípio, deve-se empregar o hífen nos seguintes casos:",
            "OBSERVAÇÃO – Êsses nomes se escrevem com inicial minúscula quando são "
            "empregados em sentido geral ou indeterminado.",
        ],
    )
    def test_brazilian_1943_pronoun_circumflex_is_no_1911_evidence(self, text):
        """Formulário 1943, rule 14.ª, writes "êsse, êsses, êste, êstes", so the pronoun
        circumflex is also Brazilian 1943 to 1971 print."""
        r = _orth(text)
        assert r.era != Era.REFORMA_1911
        assert not [m for m in r.markers if m.startswith("reforma-1911")]

    def test_brazilian_evidence_blocks_reforma_1911(self):
        """Formulário 1943, rule 13.ª (F1943:135.0). It quotes terrívelmente, an acute
        before -mente, beside its own circumflex forms (cômodamente, cortêsmente), which
        lean Brazilian."""
        text = (
            "13.ª - Mantêm-se o acento circunflexo e o til do primeiro elemento nos "
            "advérbios em mente e nos derivados em que figuram sufixos precedidos do infixo "
            "z (zada, zal, zeiro, zinho, zista, zito, zona, zorro, zudo, etc.): cômodamente, "
            "cortêsmente, dendêzeiro, ôvozito, pêssegozinho, chãmente, cristãzinha, "
            "leõezinhos, mãozoada, romãzeira, etc.; o acento agudo do primeiro elemento "
            "passará a ser acento grave nos derivados dessa natureza: avòzinha, cafézeiro, "
            "faíscazinha, indelèvelmente, opùsculozinho, sòmente, sòzinho, terrívelmente, "
            "voluntàriozinho, volùvelmente, etc.")
        r = _orth(text)
        assert "reforma-1911:terrívelmente" in r.markers
        assert r.era != Era.REFORMA_1911

    @pytest.mark.parametrize(
        "text",
        [
            # Teófilo Braga, Viriatho (Gutenberg 26850): no 1911 form
            "podendo considerar tal o simples accordo da medicina e da pharmacia.",
            # Pinheiro Chagas, A Lenda da Meia-Noite (Gutenberg 23400), pg23400:425.1:
            # one acute before -mente, two listed pre-1911 forms (typo, elle)
            "Decidídamente Isaura não lhe perdoava a creação do typo de Julieta que elle "
            "julgava que tanto devia lisongeal-a.",
        ],
    )
    def test_pre_1911_print_stays_etymological(self, text):
        assert _orth(text).era == Era.ETYMOLOGICAL

    @pytest.mark.parametrize(
        "text",
        [
            # silver_corpus p08-004, gold ao1990-pt and ao1990-br
            "De facto, o diretor exato corrigiu o exercício para que ninguém errasse.",
            # relabel row mmf-010635, modern news
            "Mas também se bebe “d’além mar” (Cava, da Catalunha) e “d’além terra” "
            "(Tokai, Hungria).",
            # HF parallel d01115 and d10705, gold ao1990
            "A atividade do vulcão diminuiu, mas os geólogos mantêm a vigilância apertada.",
            "É facto que muitas peças do museu provêm de coleções desfeitas no decurso do "
            "século passado.",
        ],
    )
    def test_modern_text_is_ao1990(self, text):
        """The Acordo Ortográfico of 1990 writes também with the acute (Base VIII 1.º c:
        "porém, provém, provéns, também") and the third person plural of the compounds
        of ter and vir with the circumflex (Base IX: "mantêm [...] provêm"), so none of
        them is a 1911 form."""
        r = _orth(text)
        assert r.era == Era.AO1990
        assert not [m for m in r.markers if m.startswith("reforma-1911")]
