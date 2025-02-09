from typing import Callable, Optional


def validation_check(selection: Optional[list[str]] = None) -> Callable:
    """
    Wraps a function. The wrapped function will become a validation check when used
    in a ValidationBase-derived class. The wrapped function will receive a Polars LazyFrame
    if requested as argument. The LazyFrame will be a subselection based on the columns
    assigned in the 'selection' parameter.

    Allows the user to define a model-bound validation check and conveniently trigger
    the check via the model.validate() function.

    Parameters
    ----------
    selection : Optional[list[str]]
        A selection of column names, which will make the dataframe subselection. If None, will return
        all columns in the dataframe to the wrapped function. If not None, will return the identifier column
        + the columns as specified here. By default None

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
        function._is_validation_function = True
        function._column_selection = selection
        return function

    return inner
