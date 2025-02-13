from polars import Expr, col


def set_as_date(column: str) -> Expr:
    return col(column).str.to_date().name.keep()


def set_as_datetime(column: str) -> Expr:
    return col(column).str.to_datetime().name.keep()


def get_date_setters(column: str) -> list[Expr]:
    setters = []

    setters.append(set_as_date(column=column))

    return setters


def get_datetime_setters(column: str) -> list[Expr]:
    setters = []

    setters.append(set_as_datetime(column=column))

    return setters
