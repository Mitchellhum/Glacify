from contextlib import contextmanager
import pytest

from glacier.wrappers import _validate_inner_type, _validate_type, validator


class MockError:
    value = None


@contextmanager
def mock_raise():
    error = MockError()
    yield error


@pytest.mark.parametrize(
    "selection, raises, error_message",
    [
        ("string", pytest.raises(TypeError), "Error: type is a string"),
        (1, pytest.raises(TypeError), "Error: type is integer"),
        ({"dict": "test"}, pytest.raises(TypeError), "Error: type is dict"),
        ((1, 2), pytest.raises(TypeError), "Error: type is tuple"),
        ([], mock_raise(), None),
        ([1], mock_raise(), None),
        (["test"], mock_raise(), None),
        ([{}], mock_raise(), None),
    ],
)
def test_type_validator(selection, raises, error_message):
    with raises as raised_error:
        _validate_type(selection=selection, error=error_message)

        assert raised_error.value == error_message


@pytest.mark.parametrize(
    "selection, raises, error_message",
    [
        ([1, 2, 3, 4], pytest.raises(TypeError), "Error: no strings"),
        (["valid", 2, 3], pytest.raises(TypeError), "Error: one or more invalid"),
        (
            ["valid", "valid", "valid", "valid", 1],
            pytest.raises(TypeError),
            "Error: one or more invalid",
        ),
        (
            [{1, 2, 3}, {1, 2, 3}, "valid"],
            pytest.raises(TypeError),
            "Error: one or more invalid",
        ),
        ([], mock_raise(), None),
        (["valid"], mock_raise(), None),
        (["valid", "valid", "valid", "valid"], mock_raise(), None),
    ],
)
def test_inner_type_validator(selection, raises, error_message):
    with raises as raised_error:
        _validate_inner_type(selection=selection, error=error_message)

        assert raised_error.value == error_message


@pytest.mark.parametrize(
    "selection, outcome",
    [
        (None, ["*"]),
        ([], ["*"]),
        (
            ["valid_item_1", "valid_item_2", "valid_item_3"],
            ["valid_item_1", "valid_item_2", "valid_item_3"],
        ),
    ],
)
def test_wrapper_init(selection, outcome):
    @validator(selection=selection)
    def inner_function():
        pass

    assert getattr(inner_function, "_is_validator") == True
    assert getattr(inner_function, "_for_columns") == outcome


@pytest.mark.parametrize(
    "selection, raises, outcome",
    [
        (
            [1, 2, 3, 4],
            pytest.raises(TypeError),
            "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!",
        ),
        (
            ["valid", 2, 3],
            pytest.raises(TypeError),
            "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!",
        ),
        (
            ["valid", "valid", "valid", "valid", 1],
            pytest.raises(TypeError),
            "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!",
        ),
        (
            [{1, 2, 3}, {1, 2, 3}, "valid"],
            pytest.raises(TypeError),
            "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!",
        ),
        (None, mock_raise(), ["*"]),
        ([], mock_raise(), ["*"]),
        (["valid"], mock_raise(), ["valid"]),
        (
            ["valid", "valid", "valid", "valid"],
            mock_raise(),
            ["valid", "valid", "valid", "valid"],
        ),
    ],
)
def test_wrapper_integration(selection, raises, outcome):
    with raises as raised_error:
        @validator(selection=selection)
        def inner_function():
            pass

        if not raised_error.value:
            assert getattr(inner_function, "_is_validator") == True
            assert getattr(inner_function, "_for_columns") == outcome
        else:
            assert raised_error.value == outcome

