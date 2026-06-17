import pytest

from desacordo_ortografico.cli import main


class TestDetectCommand:
    def test_detect_etymological(self, capsys):
        rc = main(["detect", "pharmacia", "e", "theatro"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "etymological" in out

    def test_detect_sister_language(self, capsys):
        rc = main(["detect", "umha", "cançom"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "not-portuguese" in out
        assert "Galician" in out


class TestConvertCommand:
    def test_convert_basic(self, capsys):
        rc = main(["convert", "--from", "pt_1973", "--to", "ao1990-pt", "acção"])
        out = capsys.readouterr().out.strip()
        assert rc == 0
        assert out == "ação"

    def test_convert_variant_divergence(self, capsys):
        rc = main(["convert", "--from", "ao1990-pt", "--to", "ao1990-br", "facto"])
        out = capsys.readouterr().out.strip()
        assert rc == 0
        assert out == "fato"

    def test_convert_verbose_warns_on_lossy(self, capsys):
        rc = main(["convert", "--from", "ao1990-pt", "--to", "etymological", "-v", "farmácia"])
        err = capsys.readouterr().err
        assert rc == 0
        assert "warning" in err


class TestNormsCommand:
    def test_lists_norms(self, capsys):
        rc = main(["norms"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ao1990-pt" in out
        assert "etymological" in out
