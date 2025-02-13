from functools import partial
from typing import Optional

from glacier.types import PythonType
from glacier.validators.general import get_general_validators
from glacier.validators.string import get_string_validators


def get_validators(
    column: str,
    nullable: Optional[bool],
    equal_to: Optional[PythonType],
    allow_duplicates: Optional[bool],
    min_length: Optional[int],
    type_: PythonType,
) -> list[partial]:
    validators = []

    validators.extend(
        get_general_validators(
            column=column,
            nullable=nullable,
            equal_to=equal_to,
            allow_duplicates=allow_duplicates,
        )
    )

    if type_ is str:
        validators.extend(get_string_validators(column=column, min_length=min_length))

    return validators
