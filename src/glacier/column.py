from dataclasses import dataclass
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
    _setters: Optional[list[Expr]] = None
    _validators: Optional[list[partial]] = None
    _model_validators: Optional[list[partial]] = None

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

    def _resolve(self, type_: PythonType) -> None:
        self._type = self._resolve_polars_type(type_=type_)
        self._setters = get_setters(column=self.name, default=self.default)
        self._validators = get_validators(
            column=self.name,
            nullable=self.nullable,
            equal_to=self.equal_to,
            allow_duplicates=self.allow_duplicates,
        )


# TODO: expand with setter and getter functions just for clean code purposes