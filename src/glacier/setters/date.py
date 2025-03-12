from typing import Optional
from polars import Expr, col


def set_as_date(column: str, format: Optional[str]) -> Expr:
    return col(column).str.to_date(format=format).name.keep()


def set_as_datetime(column: str, format: Optional[str]) -> Expr:
    return col(column).str.to_datetime(format=format).name.keep()


def get_date_setters(column: str, format: Optional[str]) -> list[Expr]:
    setters = []

    setters.append(set_as_date(column=column, format=format))

    return setters


def get_datetime_setters(column: str, format: Optional[str]) -> list[Expr]:
    setters = []

    setters.append(set_as_datetime(column=column, format=format))

    return setters
