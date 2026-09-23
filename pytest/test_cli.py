from click.testing import CliRunner

from uncompyle6.bin import uncompile


def test_output_option_accepts_new_file(tmp_path, monkeypatch):
    input_path = tmp_path / "input.pyc"
    output_path = tmp_path / "new-output.py"
    input_path.write_bytes(b"")

    monkeypatch.setattr(uncompile, "main", lambda *args, **kwargs: (0, 0, 0, 0))
    result = CliRunner().invoke(
        uncompile.main_bin,
        ["--output", str(output_path), str(input_path)],
    )

    assert result.exit_code == 0
