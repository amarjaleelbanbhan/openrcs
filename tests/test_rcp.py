from pathlib import Path

from openrcs import rcp

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_valid_zip_project_parsed():
    result = rcp.inspect_project(str(FIXTURES / "synthetic_valid.rcp"))
    assert result["is_zip_container"] is True
    assert "project.xml" in result["members"]
    assert result["referenced_scan_like_paths"] == ["scan001.rcs"]
    assert result["xml_members_parsed"][0]["root_tag"] == "Project"


def test_non_zip_rejected():
    result = rcp.inspect_project(str(FIXTURES / "synthetic_not_a_zip.rcp"))
    assert result["is_zip_container"] is False


def test_doctype_rejected():
    # DOCTYPE declarations must be refused outright (XXE / entity-bomb
    # protection), not merely "not expanded".
    malicious = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        b"<foo>&xxe;</foo>"
    )
    result = rcp._summarize_xml("evil.xml", malicious)
    assert "parse_error" in result


if __name__ == "__main__":
    test_valid_zip_project_parsed()
    test_non_zip_rejected()
    test_doctype_rejected()
    print("ok")
