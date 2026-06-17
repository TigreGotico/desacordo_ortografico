import pytest

from desacordo_ortografico import rules


class TestReform1911Digraphs:
    @pytest.mark.parametrize(
        "old,new",
        [
            ("theatro", "teatro"),
            ("orthographia", "ortografia"),
            ("rhetorica", "retorica"),
            ("lyrio", "lirio"),
            ("estylo", "estilo"),
            ("phosphoro", "fosforo"),
        ],
    )
    def test_digraphs(self, old, new):
        assert rules.reform_1911_digraphs(old) == new


class TestNasalVowel:
    @pytest.mark.parametrize(
        "pt,br",
        [
            ("antónio", "antônio"),
            ("fenómeno", "fenômeno"),
            ("género", "gênero"),
            ("económico", "econômico"),
            ("tónico", "tônico"),
        ],
    )
    def test_pt_to_br(self, pt, br):
        assert rules.nasal_vowel_to_br(pt) == br

    @pytest.mark.parametrize(
        "pt,br",
        [
            ("antónio", "antônio"),
            ("fenómeno", "fenômeno"),
            ("género", "gênero"),
        ],
    )
    def test_br_to_pt(self, pt, br):
        assert rules.nasal_vowel_to_pt(br) == pt

    @pytest.mark.parametrize("word", ["também", "parabéns", "armazém", "ninguém", "porém"])
    def test_oxytone_em_untouched(self, word):
        # oxytones in -ém/-éns are identical in both norms; the rule must not touch them
        assert rules.nasal_vowel_to_br(word) == word


class TestAO1990Accents:
    @pytest.mark.parametrize(
        "old,new",
        [
            ("idéia", "ideia"),
            ("assembléia", "assembleia"),
            ("heróico", "heroico"),
            ("jibóia", "jiboia"),
            ("vôo", "voo"),
            ("enjôo", "enjoo"),
            ("lêem", "leem"),
            ("vêem", "veem"),
            ("crêem", "creem"),
        ],
    )
    def test_drop(self, old, new):
        assert rules.ao1990_drop_accents(old) == new

    @pytest.mark.parametrize("word", ["herói", "anéis", "papéis", "faróis", "céu", "constrói"])
    def test_oxytone_diphthong_kept(self, word):
        # word-final stressed diphthongs keep their accent under AO1990
        assert rules.ao1990_drop_accents(word) == word


class TestTrema:
    @pytest.mark.parametrize(
        "old,new",
        [("freqüência", "frequência"), ("lingüiça", "linguiça"), ("qüinqüênio", "quinquênio")],
    )
    def test_trema(self, old, new):
        assert rules.ao1990_drop_trema(old) == new


class TestSubtonicGrave:
    @pytest.mark.parametrize(
        "old,new",
        [("sòmente", "somente"), ("cafèzinho", "cafezinho"), ("sòzinho", "sozinho")],
    )
    def test_strip(self, old, new):
        assert rules.strip_subtonic_grave(old) == new

    def test_crasis_a_preserved(self):
        assert rules.strip_subtonic_grave("à") == "à"
        assert rules.strip_subtonic_grave("àquela") == "àquela"


class TestHyphenRS:
    @pytest.mark.parametrize(
        "old,new",
        [
            ("anti-religioso", "antirreligioso"),
            ("auto-retrato", "autorretrato"),
            ("contra-senha", "contrassenha"),
            ("micro-sistema", "microssistema"),
            ("ultra-romântico", "ultrarromântico"),
        ],
    )
    def test_double(self, old, new):
        assert rules.ao1990_hyphen_rs(old) == new

    def test_noun_compound_untouched(self):
        # 'guarda-sol' is a noun+noun compound, not prefix+base; must keep its hyphen
        assert rules.ao1990_hyphen_rs("guarda-sol") == "guarda-sol"


class TestMonths:
    @pytest.mark.parametrize("m", ["Janeiro", "Dezembro", "Verão"])
    def test_lowercase(self, m):
        assert rules.ao1990_lowercase_month(m) == m.lower()

    def test_restore_capital(self):
        assert rules.restore_capital_month("janeiro") == "Janeiro"

    def test_non_month_untouched(self):
        assert rules.ao1990_lowercase_month("Lisboa") == "Lisboa"


class TestApplyToWords:
    def test_preserves_case_title(self):
        out = rules.apply_to_words("Pharmacia", rules.reform_1911_digraphs)
        assert out == "Farmacia"

    def test_preserves_case_upper(self):
        out = rules.apply_to_words("THEATRO", rules.reform_1911_digraphs)
        assert out == "TEATRO"

    def test_preserves_punctuation(self):
        out = rules.apply_to_words("theatro, pharmacia!", rules.reform_1911_digraphs)
        assert out == "teatro, farmacia!"

    def test_hyphenated_word_is_single_token(self):
        assert rules.words("anti-religioso e gato") == ["anti-religioso", "e", "gato"]
