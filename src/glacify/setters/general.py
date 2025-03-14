from typing import Optional

from polars import col, Expr, lit

from glacify.types import PythonType


def set_default(column: str, value: PythonType, type_: PythonType) -> Expr:
    if not isinstance(value, type_):
        raise TypeError(
            f"Default value for {column} is set to '{value}', which is not of type '{type_}'. Please make sure that the default value is of the same type."
        )

    return col(column).fill_null(lit(value)).name.keep()


def get_general_setters(
    column: str, default: Optional[PythonType], type_: PythonType
) -> list[Expr]:
    setters = []

    if default:
        setters.append(set_default(column=column, value=default, type_=type_))

    return setters
