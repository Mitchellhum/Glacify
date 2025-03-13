from typing import Optional
from polars import Expr, col


def set_as_date(column: str, format: Optional[str], strict: bool) -> Expr:
    return col(column).str.to_date(format, strict=strict).name.keep()


def set_as_datetime(column: str, format: Optional[str], strict: bool) -> Expr:
    return col(column).str.to_datetime(format, strict=strict).name.keep()


def get_date_setters(column: str, format: Optional[str], strict: bool) -> list[Expr]:
    setters = []
    setters.append(set_as_date(column=column, format=format, strict=strict))

    return setters


def get_datetime_setters(
    column: str, format: Optional[str], strict: bool
) -> list[Expr]:
    setters = []

    setters.append(set_as_datetime(column=column, format=format, strict=strict))

    return setters
