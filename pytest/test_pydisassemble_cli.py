import sys

from uncompyle6.bin import pydisassemble


def test_main_checks_each_input_file(tmp_path, monkeypatch, capsys):
    existing = tmp_path / "existing.pyc"
    missing = tmp_path / "missing.pyc"
    existing.write_bytes(b"")
    disassembled = []

    monkeypatch.setattr(
        pydisassemble,
        "disassemble_file",
        lambda filename, outstream: disassembled.append(filename),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["pydisassemble", str(existing), str(missing)],
    )

    pydisassemble.main()

    assert disassembled == [str(existing)]
    assert f"Can't read {missing} - skipping" in capsys.readouterr().err
