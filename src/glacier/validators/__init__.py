from functools import partial
from typing import Optional

import polars as pl

from glacier.types import PythonType
from glacier.validators.general import check_duplicates, check_equality, check_nullable


def get_validators(
    column: str,
    nullable: Optional[bool],
    equal_to: Optional[PythonType],
    allow_duplicates: Optional[bool],
) -> list[partial]:
    validators = []

    if not nullable:
        validators.append(partial(check_nullable, column=column))

    if equal_to is not None:
        validators.append(
            partial(check_equality, column=column, value=equal_to)
        )

    if not allow_duplicates:
        validators.append(partial(check_duplicates, column=column))

    return validators
