from datetime import date, datetime
from functools import partial
from typing import Optional

from glacify.types import PythonType
from glacify.validators.general import get_general_validators
from glacify.validators.numeric import get_numeric_validators
from glacify.validators.string import get_string_validators
from glacify.validators.temporal import get_date_validators


def get_validators(
    column: str,
    nullable: Optional[bool],
    equal_to: Optional[PythonType],
    allow_duplicates: Optional[bool],
    min_length: Optional[int],
    max_length: Optional[int],
    lt: Optional[int | float | date | datetime],
    gt: Optional[int | float | date | datetime],
    le: Optional[int | float | date | datetime],
    ge: Optional[int | float | date | datetime],
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
        validators.extend(
            get_string_validators(
                column=column, min_length=min_length, max_length=max_length
            )
        )

    elif type_ is int:
        validators.extend(
            get_numeric_validators(column=column, lt=lt, gt=gt, le=le, ge=ge)
        )

    elif type_ is float:
        validators.extend(
            get_numeric_validators(column=column, lt=lt, gt=gt, le=le, ge=ge)
        )

    elif type_ is date:
        validators.extend(
            get_date_validators(column=column, lt=lt, gt=gt, le=le, ge=ge)
        )

    elif type_ is datetime:
        validators.extend(
            get_date_validators(column=column, lt=lt, gt=gt, le=le, ge=ge)
        )

    return validators
