from pathlib import Path

from openrcs import rcs

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_valid_signature_detected():
    result = rcs.inspect_scan(str(FIXTURES / "synthetic_valid.rcs"))
    assert result["signature"]["valid"] is True
    assert result["point_data_decoded"] is False


def test_header_fields_parsed():
    result = rcs.inspect_scan(str(FIXTURES / "synthetic_valid.rcs"))
    fields = result["header_fields"]
    assert fields is not None
    assert fields["format_version"] == "2.5"
    assert fields["num_points_claimed"] == 12345
    assert fields["translation"] == [1.0, 2.0, 3.0]
    assert fields["guid"] == "{AAAAAAAA_BBBB_CCCC_DDDD_EEEEEEEEEEEE}"
    assert fields["data_bounds"]["min"] == [-9.5, -9.5, -0.5]
    assert fields["data_bounds"]["max"] == [9.5, 9.5, 4.5]


def test_bad_signature_rejected():
    result = rcs.inspect_scan(str(FIXTURES / "synthetic_bad_signature.rcs"))
    assert result["signature"]["valid"] is False


def test_missing_file_raises():
    try:
        rcs.inspect_scan(str(FIXTURES / "does_not_exist.rcs"))
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


if __name__ == "__main__":
    test_valid_signature_detected()
    test_header_fields_parsed()
    test_bad_signature_rejected()
    test_missing_file_raises()
    print("ok")
