from typing import Callable, Optional


def _validate_inner_type(selection: list[str], error: str) -> None:
    """
    Validates the inner type of the list as string values.

    Raises
    ------
    TypeError
        Raised whenever the inner type is not a string.
    """
    for column in selection:
        if not isinstance(column, str):
            raise TypeError(error)

def _validate_outer_type(selection: list, error: str) -> None:
    """
    Validates whether the user selection is actually a list and not a single item.

    Raises
    ------
    TypeError
        Raised whenever it is not a list.
    """
    if not isinstance(selection, list):
        raise TypeError(error)

def validator(selection: Optional[list[str]] = None) -> Callable:
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
    ```python
    from polars import Expr, col, lit
    from glacier import ValidationBase, Column, validator

    class ExampleValidator(ValidationBase):
        settings = ValidationSettings(strict=False)
        id: int = Column(name="Index")
        first_name: str = Column(name="First Name")
        last_name: str = Column(name="Last Name")
        address: str = Column(name="Address")
        gross_income: float = Column(name="Gross-Income")

        @validator(selection=["First Name", "Last Name"])
        def check_is_alphabetic(column: str) -> tuple[Expr, str]:
            # Anything that is not alphabetic needs to receive the error
            expression = col(column).str.contains(pattern="/^[A-Za-z]+$/").not_()
            error = f"{column} can only contain alphabetic characters!"

            return expression, error

        @validator(selection=["Gross-Income"])
        def check_not_negative(column: str) -> tuple[Expr, str]:
            expression = col(column).lt(lit(0.0))
            error = f"{column} cannot be lower than 0!"

            return expression, error
    ```
    """
    type_error = "Argument 'selection' expects a list of strings representing the column names needed for executing the validation check!"

    if not selection:
        selection = ["*"]

    # Lets make sure that the user actually inputted a list...
    _validate_outer_type(selection=selection, error=type_error)

    # We also have to make sure that the values are string too
    _validate_inner_type(selection=selection, error=type_error)

    # Set the validation check identifiers, so that the metaclass knows what to do
    def inner(function: Callable) -> Callable:
        function._is_validator = True
        function._for_columns = selection
        return function

    return inner
