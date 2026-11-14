"""Tests for the Fortis patch helpers (no ZWCAD needed)."""

import json

from zwcad_mcp.backends.file_ipc import FileIPCBackend, encode_lisp_markers


class TestLispMarkers:
    def test_ascii_untouched(self):
        code = '(command "_.LINE" "0,0" "10,0" "")'
        assert encode_lisp_markers(code) == code

    def test_accents_and_symbols(self):
        code = '(strcat "Armação h≥10")'
        out = encode_lisp_markers(code)
        assert out == '(strcat "Arma{{U+00E7}}{{U+00E3}}o h{{U+2265}}10")'
        out.encode("ascii")  # must be pure ASCII

    def test_cjk(self):
        assert encode_lisp_markers("中望") == "{{U+4E2D}}{{U+671B}}"


class TestDwgBase:
    def test_variants_match(self):
        names = [
            "Floor-Plan-01.dwg",
            "C:\\Projects\\Floor-Plan-01.dwg",
            "C:/Projects/floor-plan-01.DWG",
            "Floor-Plan-01*",
            "Floor-Plan-01",
        ]
        assert {FileIPCBackend._dwg_base(n) for n in names} == {"floor-plan-01"}


class TestCommandPayload:
    def test_non_ascii_params_are_json_escaped(self):
        # Python sends \uXXXX escapes (ensure_ascii); the LISP side decodes them.
        payload = json.dumps({"params": {"text": "Armação"}})
        assert "\\u00e7" in payload
        payload.encode("ascii")
