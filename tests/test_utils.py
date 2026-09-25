from pikpak_tool.utils import normalize_ext, normalize_remote


def test_normalize_ext():
    assert normalize_ext(".ASC") == "asc"
    assert normalize_ext(" Zip ") == "zip"


def test_normalize_remote():
    assert normalize_remote("pikpak:") == "pikpak"
    assert normalize_remote("pikpak") == "pikpak"
