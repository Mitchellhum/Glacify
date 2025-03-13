from functools import partial
from typing import Optional

from polars import Expr, col, when, lit


def check_lt(column: str, value: int | float, index: int) -> Expr:
    return (
        when(col(column).ge(lit(value)))
        .then(lit(f"{column} must be lower than {value}"))
        .alias(f"__error_{index}")
    )


def check_gt(column: str, value: int | float, index: int) -> Expr:
    return (
        when(col(column).le(lit(value)))
        .then(lit(f"{column} must be greater than {value}"))
        .alias(f"__error_{index}")
    )


def check_le(column: str, value: int | float, index: int) -> Expr:
    return (
        when(col(column).gt(lit(value)))
        .then(lit(f"{column} must be lower than, or equal to, {value}"))
        .alias(f"__error_{index}")
    )


def check_ge(column: str, value: int | float, index: int) -> Expr:
    return (
        when(col(column).lt(lit(value)))
        .then(lit(f"{column} must be greate than, or equal to, {value}"))
        .alias(f"__error_{index}")
    )


def get_numeric_validators(
    column: str,
    lt: Optional[int | float],
    gt: Optional[int | float],
    le: Optional[int | float],
    ge: Optional[int | float],
) -> list[Expr]:
    validators = []

    for value in (lt, gt, le, ge):
        if value is None:
            continue

        if not isinstance(value, int) and not isinstance(value, float):
            raise ValueError(
                f"Column {column} is annotated as a numeric field, but the lt, gt, le or ge fields are not the same type!"
            )

    if lt:
        validators.append(partial(check_lt, column=column, value=lt))

    if gt:
        validators.append(partial(check_gt, column=column, value=gt))

    if le:
        validators.append(partial(check_le, column=column, value=le))

    if ge:
        validators.append(partial(check_ge, column=column, value=ge))

    return validators
