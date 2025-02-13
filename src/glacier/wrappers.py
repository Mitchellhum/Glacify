from typing import Callable, Optional


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

    # Set the validation check identifiers, so that the metaclass knows what to do
    def inner(function: Callable) -> Callable:
        function._is_validator = True
        function._for_columns = selection
        return function

    return inner
