from contextlib import nullcontext
import pytest

from glacier.wrappers import _validate_inner_type, _validate_outer_type, validator

type_error = "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!"


@pytest.mark.parametrize(
    "selection, raises, error_message",
    [
        (
            b"string",
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            1,
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            {"dict": "test"},
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            (1, 2),
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        ([], nullcontext(), None),
        ([1], nullcontext(), None),
        (["test"], nullcontext(), None),
        ([b"test"], nullcontext(), None),
        ([{}], nullcontext(), None),
    ],
)
def test_outer_type_validator(selection, raises, error_message):
    with raises:
        _validate_outer_type(selection=selection, error=error_message)


@pytest.mark.parametrize(
    "selection, raises, error_message",
    [
        (
            [1, 2, 3, 4],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            ["valid", 2, 3],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            [b"valid"],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            ["valid", "valid", "valid", "valid", 1],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            [{1, 2, 3}, {1, 2, 3}, "valid"],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        ([], nullcontext(), None),
        ([""], nullcontext(), None),
        (["valid"], nullcontext(), None),
        (["valid", "valid", "valid", "valid"], nullcontext(), None),
    ],
)
def test_inner_type_validator(selection, raises, error_message):
    with raises:
        _validate_inner_type(selection=selection, error=error_message)


@pytest.mark.parametrize(
    "selection, outcome",
    [
        (None, ["*"]),
        ([], ["*"]),
        ([""], [""]),
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
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            ["valid", 2, 3],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            [b"invalid"],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            ["valid", "valid", "valid", "valid", 1],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (
            [{1, 2, 3}, {1, 2, 3}, "valid"],
            pytest.raises(TypeError, match=type_error),
            type_error,
        ),
        (None, nullcontext(), ["*"]),
        ([], nullcontext(), ["*"]),
        (["valid"], nullcontext(), ["valid"]),
        (
            ["valid", "valid", "valid", "valid"],
            nullcontext(),
            ["valid", "valid", "valid", "valid"],
        ),
    ],
)
def test_wrapper_integration(selection, raises, outcome):
    with raises as raised_error:

        @validator(selection=selection)
        def inner_function():
            pass

        if not raised_error:
            assert getattr(inner_function, "_is_validator") == True
            assert getattr(inner_function, "_for_columns") == outcome
