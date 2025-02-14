from functools import partial
from typing import Optional

from polars import Expr, col, when, lit


def check_min_length(column: str, length: int, index: int) -> Expr:
    return (
        when(col(column).str.len_chars().lt(lit(length)))
        .then(lit(f"{column} requires a minimal length of {length} characters."))
        .alias(f"__error_{index}")
    )


def get_string_validators(column: str, min_length: Optional[int]) -> list[Expr]:
    validators = []

    if min_length:
        validators.append(partial(check_min_length, column=column))

    return validators
