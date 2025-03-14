from dataclasses import dataclass
from typing import Optional


@dataclass(repr=False, eq=False, match_args=False, slots=True)
class ValidationSettings:
    """
    Settings object that hold the general settings for each validator.

    Attributes
    ----------
    strict : Optional[bool]
        If set to true, will force data type validation for each column and throw
        errors if the type cannot be set. If false, will set all failing cases to
        'null'/None. Defaults to true.
    shift_to_row : Optional[int]
        Shifts the entire dataframe to this row. It means that this row must also
        contain all header new header values, otherwise the model will fail later on.
        First row starts at index 1.
    """

    strict: Optional[bool] = True
    shift_to_row: Optional[int] = None
