from datetime import date, datetime
from typing import Optional

from polars import Expr

from glacier.setters.temporal import get_date_setters, get_datetime_setters
from glacier.setters.general import get_general_setters
from glacier.types import PythonType


def get_setters(
    column: str,
    type_: PythonType,
    strict: bool,
    default: Optional[PythonType],
    format: Optional[str],
) -> list[Expr]:
    setters = []


    if type_ is date:
        setters.extend(get_date_setters(column=column, format=format, strict=strict))

    elif type_ is datetime:
        setters.extend(
            get_datetime_setters(column=column, format=format, strict=strict)
        )

    # Setters run sequentially, so order actually matters
    setters.extend(get_general_setters(column=column, default=default, type_=type_))

    return setters
