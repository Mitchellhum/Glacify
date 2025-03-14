from functools import partial
from typing import Optional

from polars import when, col, lit, Expr

from glacify.types import PythonType


def check_nullable(column: str, index: int) -> Expr:
    return (
        when(col(column).is_null())
        .then(lit(f"{column} cannot be null!"))
        .alias(f"__error_{index}")
    )


def check_equality(column: str, value: PythonType, index: int) -> Expr:
    return (
        when(~col(column).eq(lit(value)))
        .then(lit(f"{column} must be equal to '{value}'!"))
        .alias(f"__error_{index}")
    )


def check_duplicates(column: str, index: int) -> Expr:
    return (
        when(col(column).is_duplicated())
        .then(lit(f"{column} cannot contain duplicate values!"))
        .alias(f"__error_{index}")
    )


def get_general_validators(
    column: str,
    nullable: Optional[bool],
    equal_to: Optional[PythonType],
    allow_duplicates: Optional[bool],
) -> list[partial]:
    validators = []

    if not nullable:
        validators.append(partial(check_nullable, column=column))

    if equal_to is not None:
        validators.append(partial(check_equality, column=column, value=equal_to))

    if not allow_duplicates:
        validators.append(partial(check_duplicates, column=column))

    return validators
