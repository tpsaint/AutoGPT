import json

import pytest

from .parsing import extract_dict_from_json, extract_list_from_json, json_loads

_JSON_FIXABLE: list[tuple[str, str]] = [
    # Missing comma
    ('{"name": "John Doe"   "age": 30,}', '{"name": "John Doe", "age": 30}'),
    ("[1, 2 3]", "[1, 2, 3]"),
    # Trailing comma
    ('{"name": "John Doe", "age": 30,}', '{"name": "John Doe", "age": 30}'),
    ("[1, 2, 3,]", "[1, 2, 3]"),
    # Extra comma in object
    ('{"name": "John Doe",, "age": 30}', '{"name": "John Doe", "age": 30}'),
    # Extra newlines
    ('{"name": "John Doe",\n"age": 30}', '{"name": "John Doe", "age": 30}'),
    ("[1, 2,\n3]", "[1, 2, 3]"),
    # Missing closing brace or bracket
    ('{"name": "John Doe", "age": 30', '{"name": "John Doe", "age": 30}'),
    ("[1, 2, 3", "[1, 2, 3]"),
    # Different numerals
    ("[+1, ---2, .5, +-4.5, 123.]", "[1, -2, 0.5, -4.5, 123]"),
    ('{"bin": 0b1001, "hex": 0x1A, "oct": 0o17}', '{"bin": 9, "hex": 26, "oct": 15}'),
    # Broken array
    (
        '[1, 2 3, "yes" true, false null, 25, {"obj": "var"}',
        '[1, 2, 3, "yes", true, false, null, 25, {"obj": "var"}]',
    ),
    # Codeblock
    (
        '```json\n{"name": "John Doe", "age": 30}\n```',
        '{"name": "John Doe", "age": 30}',
    ),
    # Multiple problems
    (
        '{"name":"John Doe" "age": 30\n "empty": "","address": '
        "// random comment\n"
        '{"city": "New York", "state": "NY"},'
        '"skills": ["Python" "C++", "Java",""],',
        '{"name": "John Doe", "age": 30, "empty": "", "address": '
        '{"city": "New York", "state": "NY"}, '
        '"skills": ["Python", "C++", "Java", ""]}',
    ),
    # All good
    (
        '{"name": "John Doe", "age": 30, "address": '
        '{"city": "New York", "state": "NY"}, '
        '"skills": ["Python", "C++", "Java"]}',
        '{"name": "John Doe", "age": 30, "address": '
        '{"city": "New York", "state": "NY"}, '
        '"skills": ["Python", "C++", "Java"]}',
    ),
    ("true", "true"),
    ("false", "false"),
    ("null", "null"),
    ("123.5", "123.5"),
    ('"Hello, World!"', '"Hello, World!"'),
    ("{}", "{}"),
    ("[]", "[]"),
]

_JSON_UNFIXABLE: list[tuple[str, str]] = [
    # Broken booleans and null
    ("[TRUE, False, NULL]", "[true, false, null]"),
    # Missing values in array
    ("[1, , 3]", "[1, 3]"),
    # Leading zeros (are treated as octal)
    ("[0023, 015]", "[23, 15]"),
    # Missing quotes
    ('{"name": John Doe}', '{"name": "John Doe"}'),
    # Missing opening braces or bracket
    ('"name": "John Doe"}', '{"name": "John Doe"}'),
    ("1, 2, 3]", "[1, 2, 3]"),
]


@pytest.fixture(params=_JSON_FIXABLE)
def fixable_json(request: pytest.FixtureRequest) -> tuple[str, str]:
    return request.param


@pytest.fixture(params=_JSON_UNFIXABLE)
def unfixable_json(request: pytest.FixtureRequest) -> tuple[str, str]:
    return request.param


def test_json_loads_fixable(fixable_json: tuple[str, str]):
    assert json_loads(fixable_json[0]) == json.loads(fixable_json[1])


def test_json_loads_unfixable(unfixable_json: tuple[str, str]):
    assert json_loads(unfixable_json[0]) != json.loads(unfixable_json[1])


class TestExtractDictFromJson:
    """Test cases for extract_dict_from_json function."""

    def test_extract_dict_from_json_codeblock(self):
        """Test extracting dict from JSON in code block."""
        json_str = '```json\n{"name": "John", "age": 30}\n```'
        result = extract_dict_from_json(json_str)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_extract_dict_from_json_codeblock_uppercase(self):
        """Test extracting dict from JSON in uppercase code block."""
        json_str = '```JSON\n{"name": "John", "age": 30}\n```'
        result = extract_dict_from_json(json_str)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_extract_dict_from_json_embedded_in_text(self):
        """Test extracting dict from JSON embedded in text."""
        json_str = 'Here is some text {"name": "John", "age": 30} and more text'
        result = extract_dict_from_json(json_str)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_extract_dict_from_json_plain_dict(self):
        """Test extracting dict from plain JSON dict."""
        json_str = '{"name": "John", "age": 30}'
        result = extract_dict_from_json(json_str)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_extract_dict_from_json_nested_dict(self):
        """Test extracting nested dict from JSON."""
        json_str = '{"person": {"name": "John", "age": 30}, "city": "NYC"}'
        result = extract_dict_from_json(json_str)
        expected = {"person": {"name": "John", "age": 30}, "city": "NYC"}
        assert result == expected

    def test_extract_dict_from_json_with_fixable_issues(self):
        """Test extracting dict from JSON with fixable syntax issues."""
        json_str = '{"name": "John",, "age": 30,}'  # Extra comma
        result = extract_dict_from_json(json_str)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_extract_dict_from_json_non_dict_raises_error(self):
        """Test that non-dict JSON raises ValueError."""
        json_str = '[1, 2, 3]'
        with pytest.raises(ValueError, match="evaluated to non-dict value"):
            extract_dict_from_json(json_str)

    def test_extract_dict_from_json_string_raises_error(self):
        """Test that string JSON raises ValueError."""
        json_str = '"hello world"'
        with pytest.raises(ValueError, match="evaluated to non-dict value"):
            extract_dict_from_json(json_str)

    def test_extract_dict_from_json_number_raises_error(self):
        """Test that number JSON raises ValueError."""
        json_str = '42'
        with pytest.raises(ValueError, match="evaluated to non-dict value"):
            extract_dict_from_json(json_str)

    def test_extract_dict_from_json_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises ValueError."""
        json_str = 'not json at all'
        with pytest.raises(ValueError, match="Failed to parse JSON string"):
            extract_dict_from_json(json_str)


class TestExtractListFromJson:
    """Test cases for extract_list_from_json function."""

    def test_extract_list_from_json_codeblock(self):
        """Test extracting list from JSON in code block."""
        json_str = '```json\n[1, 2, 3]\n```'
        result = extract_list_from_json(json_str)
        expected = [1, 2, 3]
        assert result == expected

    def test_extract_list_from_json_codeblock_uppercase(self):
        """Test extracting list from JSON in uppercase code block."""
        json_str = '```JSON\n["a", "b", "c"]\n```'
        result = extract_list_from_json(json_str)
        expected = ["a", "b", "c"]
        assert result == expected

    def test_extract_list_from_json_embedded_in_text(self):
        """Test extracting list from JSON embedded in text."""
        json_str = 'Here is some text [1, 2, 3] and more text'
        result = extract_list_from_json(json_str)
        expected = [1, 2, 3]
        assert result == expected

    def test_extract_list_from_json_plain_list(self):
        """Test extracting list from plain JSON list."""
        json_str = '[1, 2, 3]'
        result = extract_list_from_json(json_str)
        expected = [1, 2, 3]
        assert result == expected

    def test_extract_list_from_json_nested_list(self):
        """Test extracting nested list from JSON."""
        json_str = '[[1, 2], [3, 4], [5, 6]]'
        result = extract_list_from_json(json_str)
        expected = [[1, 2], [3, 4], [5, 6]]
        assert result == expected

    def test_extract_list_from_json_mixed_types(self):
        """Test extracting list with mixed types from JSON."""
        json_str = '[1, "hello", true, null, {"key": "value"}]'
        result = extract_list_from_json(json_str)
        expected = [1, "hello", True, None, {"key": "value"}]
        assert result == expected

    def test_extract_list_from_json_with_fixable_issues(self):
        """Test extracting list from JSON with fixable syntax issues."""
        json_str = '[1, 2, 3,]'  # Trailing comma
        result = extract_list_from_json(json_str)
        expected = [1, 2, 3]
        assert result == expected

    def test_extract_list_from_json_non_list_raises_error(self):
        """Test that non-list JSON raises ValueError."""
        json_str = '{"key": "value"}'
        with pytest.raises(ValueError, match="evaluated to non-list value"):
            extract_list_from_json(json_str)

    def test_extract_list_from_json_string_raises_error(self):
        """Test that string JSON raises ValueError."""
        json_str = '"hello world"'
        with pytest.raises(ValueError, match="evaluated to non-list value"):
            extract_list_from_json(json_str)

    def test_extract_list_from_json_number_raises_error(self):
        """Test that number JSON raises ValueError."""
        json_str = '42'
        with pytest.raises(ValueError, match="evaluated to non-list value"):
            extract_list_from_json(json_str)

    def test_extract_list_from_json_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises ValueError."""
        json_str = 'not json at all'
        with pytest.raises(ValueError, match="Failed to parse JSON string"):
            extract_list_from_json(json_str)


class TestJsonLoadsErrorHandling:
    """Additional test cases for json_loads error handling."""

    def test_json_loads_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse JSON string"):
            json_loads("completely invalid json")

    def test_json_loads_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = json_loads("")
        assert result is None

    def test_json_loads_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = json_loads("   \n\t   ")
        assert result is None
