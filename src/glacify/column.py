from dataclasses import dataclass, field
from datetime import date, datetime
from functools import partial
from typing import Optional, get_args, get_origin, List as TypedList

from polars import Expr, String

from glacify.setters import get_setters
from glacify.types import PolarsType, PythonType, PYTHON_POLARS_TYPE_MAPPING
from glacify.validators import get_validators


@dataclass(repr=False, eq=False, match_args=False)
class Column:
    """
    Represents a column inside a dataframe. Expects at least the full column name as argument ('name').
    A Column contains basic/default validators so that the user does not have to define any of those.
    For example, the argument 'min_length' will add a validation expression to the list of validators,
    which will then check this column for a certain length. Will only work if the validator is applicable
    on the annotated python type for this column.

    Attributes
    ----------
    name : str
        Name of the column that this Column object represents.
    is_identifier : bool
        This column can be used as identifier for each row/error.
    nullable : bool
        Column can contain nullable values. By default true.
    allow_duplicates : bool
        Column allows duplicates to exist. By default True.
    default : Optional[PythonType]
        Replaces all null values with the default value. Be sure to have the same type for the default value
        just like the annotated type for the column.
    format : Optional[str]
        Format used to transform date field from strings. Whenever a date/datetime field is found,
        all values are transformed in to Polars dates via this format. If None, will use Polars'
        native default value.
    strict : Optional[bool]
        Determines whether the datatype is strictly set, meaning if true, any wrong datatypes will throw an error.
        If false, any wrong datatypes will turn in to null. This parameter overwrites ValidationSettings.strict! 
    min_length : Optional[int]
        Sets the minimal length of iteratable column types, such as strings and lists.
    max_length : Optional[int]
        Sets the maximal length of iteratable column types, such as strings and lists.
    lt : Optional[int | float | date | datetime]
        All values inside the column must be lower than the assigned value.
    gt : Optional[int | float | date | datetime]
        All values inside the column must be greater than the assigned value.
    le : Optional[int | float | date | datetime]
        All values inside the column must be lower than or equal to the assigned value.
    ge : Optional[int | float | date | datetime]
        All values inside the column must be greater than or equal to the assigned value.
    equal_to : Optional[PythonType]
        All values inside the column must be equal to the assigned value.

    Examples
    --------
    >>> from polars import Expr, col, lit
    >>> from glacify import ValidationBase, Column, validator, ValidationSettings
    ...
    >>> class NewClass(ValidationBase):
    ...    settings = ValidationSettings(strict=False)
    ...    index: int = Column(name="Index", is_identifier=True)
    ...    string_column: str = Column(name="String Column", equal_to="must be equal")
    ...
    >>> # Error:
    >>> # The dataframe failed to pass the validation model. Below is a summary of all validation errors:
    >>> # 1:
    >>> #     String Column must be equal to 'must be equal'!
    """

    name: str
    is_identifier: bool = False
    nullable: bool = True
    allow_duplicates: bool = True
    default: Optional[PythonType] = None
    format: Optional[str] = None
    strict: Optional[bool] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    lt: Optional[int | float | date | datetime] = None
    gt: Optional[int | float | date | datetime] = None
    le: Optional[int | float | date | datetime] = None
    ge: Optional[int | float | date | datetime] = None
    equal_to: Optional[PythonType] = None
    
    # Private Fields
    _type: Optional[PolarsType] = field(default=None, init=False)
    _setters: list[Expr] = field(default_factory=lambda: [], init=False)
    _validators: list[partial] = field(default_factory=lambda: [], init=False)
    _model_validators: list[partial] = field(default_factory=lambda: [], init=False)

    def _resolve_polars_type(self, type_: PythonType) -> None:
        """
        Transforms the python type to a polars type.
        """
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

    def resolve(self, type_: PythonType, strict: bool) -> None:
        """
        Resolves all types, setters and validators that are default for this column and python type.

        Parameters
        ----------
        type_ : PythonType
            Type that is used as attribute annotation inside the model.
        """
        self._type = self._resolve_polars_type(type_=type_)
        self._setters = get_setters(
            column=self.name,
            type_=type_,
            strict=self.strict or strict,
            default=self.default,
            format=self.format,
        )
        self._validators = get_validators(
            column=self.name,
            nullable=self.nullable,
            equal_to=self.equal_to,
            allow_duplicates=self.allow_duplicates,
            min_length=self.min_length,
            max_length=self.max_length,
            lt=self.lt,
            gt=self.gt,
            le=self.le,
            ge=self.ge,
            type_=type_,
        )

    def add_validator(self, validator: partial) -> None:
        """
        Adds a validator to the list of column validators.

        Parameters
        ----------
        validator : partial
            A partial that accepts 'index' as argument, which identifies
            which __error_index it is supposed to set in the dataframe.
        """
        self._validators.append(validator)

    def get_validators(self) -> list[partial]:
        """
        Returns all currently set validators.

        Returns
        -------
        list[partial]
            A list of partial functions that return an Expression.
        """
        return self._validators

    def add_setter(self, setter: Expr) -> None:
        """
        Adds a setter expression to the list of column setters.

        Parameters
        ----------
        setter : Expr
            An expression that sets or changes a value inside a column.
        """
        self._setters.append(setter)

    def get_setters(self) -> list[Expr]:
        """
        Returns all currently set setter expressions.

        Returns
        -------
        list[Expr]
            A list of setters expressions.
        """
        return self._setters
