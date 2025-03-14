from dataclasses import dataclass


@dataclass(repr=False, eq=False, match_args=False, slots=True)
class ValidationSettings:
    """
    Settings object that hold the general settings for each validator.

    Attributes
    ----------
    strict : bool
        If set to true, will force data type validation for each column and throw
        errors if the type cannot be set. If false, will set all failing cases to
        'null'/None. Defaults to true.
    """

    strict: bool = True
