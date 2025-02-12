import polars as pl

from glacier.types import PythonType


def check_nullable(column: str, index: int) -> pl.Expr:
    return (
        pl.when(pl.col(column).is_null())
        .then(pl.lit(f"{column} cannot be null!"))
        .alias(f"__error_{index}")
    )


def check_equality(column: str, value: PythonType, index: int) -> pl.Expr:
    return (
        pl.when(~pl.col(column).eq(pl.lit(value)))
        .then(pl.lit(f"{column} must be equal to {value}!"))
        .alias(f"__error_{index}")
    )


def check_duplicates(column: str, index: int) -> pl.Expr:
    return (
        pl.when(pl.col(column).is_duplicated())
        .then(pl.lit(f"{column} cannot contain duplicate values!"))
        .alias(f"__error_{index}")
    )
