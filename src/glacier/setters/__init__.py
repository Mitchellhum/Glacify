from typing import Optional

from polars import Expr

from glacier.setters.general import set_default
from glacier.types import PythonType


def get_setters(column: str, default: Optional[PythonType]) -> list[Expr]:
    setters = []

    if default:
        setters.append(set_default(column=column, value=default))

    return setters
