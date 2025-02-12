import polars as pl

from glacier.types import PythonType


def set_default(column: str, value: PythonType) -> pl.Expr:
    return pl.col(column).fill_null(pl.lit(value)).alias(column)
