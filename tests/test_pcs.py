import pytest
from procyclingstats import Race

from src.utils import convert_name_to_slug, try_to_parse


@pytest.mark.parametrize(
    "test_input, expected",
    [("race/tour-de-france/2022", dict), ("race/does-not-exist/2023", type(None))],
)
def test_try_to_parse(test_input, expected):
    assert isinstance(try_to_parse(Race, f"{test_input}/overview"), expected)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("VAN AERT Wout", "wout-van-aert"),
        ("POGAČAR Tadej", "tadej-pogacar"),
        ("AYUSO Juan", "juan-ayuso-pesquera"),
    ],
)
def test_conversion_name_to_slug(test_input, expected):
    assert convert_name_to_slug(test_input) == expected
