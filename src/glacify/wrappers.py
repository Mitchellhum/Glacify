from typing import Callable, Optional

from glacify.types import ModeType


def validation_check(
    selection: Optional[list[str]] = None, mode: ModeType = "repeating"
) -> Callable:
    """
    Wraps a function that returns a validation expression. All wrapped functions
    are expected to receive at least 1 argument, which would be the column name.
    Wrapped functions are expected to return 2 arguments: a filter Expression
    that would be valid polars, and an error which is shown whenever the filter
    is true for a row.

    Parameters
    ----------
    selection : Optional[list[str]]
        A list of all columns on which this validation expression needs to be
        executed. By default None, which would mean all columns get checked by this
        expression.
    mode : Literal["repeating", "model"]
        Decides the usage strategy of the validation check. 'Repeating' will execute the
        validation check on each provided column as assigned in 'selection'. 'Repeating'
        checks will receive the 'column_name' parameter. 'Model' will execute the
        validation check once. NOTE: in case of the 'model' mode, be sure to still provide
        a list of all applicable columns, as this will check whether those columns exist.

    Returns
    -------
    Callable
        Returns the wrapped function.

    Raises
    ------
    TypeError
        Raised when 'selection' is not a valid list with strings.


    Examples
    --------
    Creating a validator class and defining validation rules:

    >>> from polars import Expr, col, lit
    >>> from glacify import ValidationBase, Column, validation_check, ValidationSettings
    ...
    >>> class ExampleValidator(ValidationBase):
    ...     settings = ValidationSettings(strict=False)
    ...     id: int = Column(name="Index")
    ...     first_name: str = Column(name="First Name")
    ...     last_name: str = Column(name="Last Name")
    ...     address: str = Column(name="Address")
    ...     gross_income: float = Column(name="Gross-Income")
    ...
    ...     @validation_check(selection=["First Name", "Last Name"])
    ...     def check_is_alphabetic(column: str) -> Tuple[Expr, str]:
    ...         expression = col(column).str.contains(pattern="/^[A-Za-z]+$/").not_()
    ...         error = f"{column} can only contain alphabetic characters!"
    ...         return expression, error
    ...
    ...     @validation_check(selection=["Gross-Income"])
    ...     def check_not_negative(column: str) -> Tuple[Expr, str]:
    ...         expression = col(column).lt(lit(0.0))
    ...         error = f"{column} cannot be lower than 0!"
    ...         return expression, error
    """
    type_error = "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!"

    if not selection:
        selection = ["*"]

    # Lets make sure that the user actually inputted a list...
    if not isinstance(selection, list):
        raise TypeError(type_error)

    # We also have to make sure that the values are string too
    for column in selection:
        if not isinstance(column, str):
            raise TypeError(type_error)

    if mode not in ("repeating", "model"):
        raise TypeError("Function mode can only be 'repeating' or 'model'")

    # Set the validation check identifiers, so that the metaclass knows what to do
    def inner(function: Callable) -> Callable:
        function._is_validator = True
        function._for_columns = selection
        function._mode = mode
        return function

    return inner
