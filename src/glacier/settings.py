from dataclasses import dataclass


@dataclass(repr=False, eq=False, match_args=False, slots=True)
class ValidationSettings:
    strict: bool = True
