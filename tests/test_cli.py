
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


class TestCliErrorHandling:
    def test_bad_norm_exits_cleanly_no_traceback(self, capsys):
        rc = main(["convert", "--from", "bogus", "--to", "ao1990-pt", "x"])
        captured = capsys.readouterr()
        assert rc == 2
        assert "error:" in captured.err
        assert "Traceback" not in captured.err  # must not dump a stack to the user

    def test_missing_text_no_stdin_errors(self, capsys, monkeypatch):
        # simulate an interactive TTY with no piped input and no positional text
        class _TTY:
            def isatty(self):
                return True

            def read(self):  # pragma: no cover - must not be reached
                raise AssertionError("should not block on stdin")

        monkeypatch.setattr("sys.stdin", _TTY())
        rc = main(["detect"])
        assert rc == 2
        assert "no text provided" in capsys.readouterr().err


class TestNormsCommand:
    def test_lists_norms(self, capsys):
        rc = main(["norms"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ao1990-pt" in out
        assert "etymological" in out
