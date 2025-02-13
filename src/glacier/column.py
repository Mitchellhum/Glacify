from dataclasses import dataclass, field
from datetime import date, datetime
from functools import partial
from typing import Optional, get_args, get_origin, List as TypedList

from polars import Expr, String

from glacier.setters import get_setters
from glacier.types import PolarsType, PythonType, PYTHON_POLARS_TYPE_MAPPING
from glacier.validators import get_validators


@dataclass(repr=False, eq=False, match_args=False)
class Column:
    name: str
    is_identifier: Optional[bool] = False
    nullable: Optional[bool] = True
    default: Optional[PythonType] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    lower_than: Optional[int | float | date | datetime] = None
    greater_than: Optional[int | float | date | datetime] = None
    equal_to: Optional[PythonType] = None
    allow_duplicates: Optional[bool] = True
    _type: Optional[PolarsType] = None
    _setters: list[Expr] = field(default_factory=lambda: [])
    _validators: list[partial] = field(default_factory=lambda: [])
    _model_validators: list[partial] = field(default_factory=lambda: [])

    def _resolve_polars_type(self, type_: PythonType) -> None:
        origin, args = get_origin(type_), get_args(type_)

        # Do we have a list?
        if origin in {list, TypedList} or type_ in {list, TypedList}:
            if not args:
                raise TypeError("List annotations need to have an inner type!")
            return PYTHON_POLARS_TYPE_MAPPING[list](self._resolve_polars_type(args[0]))

        # Warn the user for now
        if type_ not in PYTHON_POLARS_TYPE_MAPPING:
            print(
                f"WARNING! {self.name}: There is currently no support yet for type '{type_}', defaulting to String."
            )

        return PYTHON_POLARS_TYPE_MAPPING.get(type_, String)

    def resolve(self, type_: PythonType) -> None:
        self._type = self._resolve_polars_type(type_=type_)
        self._setters = get_setters(column=self.name, type_=type_, default=self.default)
        self._validators = get_validators(
            column=self.name,
            nullable=self.nullable,
            equal_to=self.equal_to,
            allow_duplicates=self.allow_duplicates,
            min_length=self.min_length,
            type_=type_,
        )

    def add_validator(self, validator: partial) -> None:
        self._validators.append(validator)

    def get_validators(self) -> list[partial]:
        return self._validators

    def add_setter(self, setter: Expr) -> None:
        self._setters.append(setter)

    def get_setters(self) -> list[Expr]:
        return self._setters
