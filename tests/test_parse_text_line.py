from murata_sensor import FailedCheckSum, parse_text_line


def test_parse_empty_line_non_strict_returns_unparsed_result():
    """strict=False では空行も未解析結果として返す"""
    result = parse_text_line("   ", strict=False)

    assert result["parsed"] is False
    assert result["reason"] == "empty_line"
    assert result["raw_data"] == b""
    assert isinstance(result["timestamp"], str)


def test_parse_checksum_error_non_strict_keeps_source_metadata():
    """送信元付きのチェックサムエラーでも未解析情報を保持する"""
    line = (
        "2024/09/20 16:26:11 192.168.1.100/55061:"
        "ERXDATA 8001 0000 1012 F000 2A 7A "
        "03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C"
        "FFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7199 "
        "8001 7FFF"
    )

    result = parse_text_line(line, strict=False)

    assert result["parsed"] is False
    assert result["reason"] == "checksum_error"
    assert isinstance(result["error"], FailedCheckSum)
    assert result["source_ip"] == "192.168.1.100"
    assert result["source_port"] == 55061
    assert result["addr"] == ("192.168.1.100", 55061)
    assert result["raw_data"].startswith(b"ERXDATA")
