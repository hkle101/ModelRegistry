from backend.api.license_check import SimpleLicenseCheckRequest


def test_simple_license_check_request_valid():
    m = SimpleLicenseCheckRequest(github_url="https://github.com/o/r")
    assert m.github_url.startswith("https://")
