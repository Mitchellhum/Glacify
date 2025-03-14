class GlacifyCriticalException(Exception):
    """
    Occurs whenever the glacify validation model runs in to an error
    that prevents the model from validating the dataframe. Often, these 
    errors are caused by bugs/unexpected behaviour and should be reported
    to the Glacify github page.
    """
    pass


class GlacifyValidationException(Exception):
    """
    The main error thrown by the validation model. A regular occurence, as this would
    mean that the validation model is doing a good job.

    Examples
    --------
    >>> # The dataframe failed to pass the validation model. Below is a summary of all validation errors:
    >>> # Row 1:
    >>> #     String Column must be equal to 'must be equal'!
    >>> #
    >>> # Row 2:
    >>> #     Integer Column must be greater than 0!
    """
    def __init__(self, inner: dict[str, list]) -> None:
        self._inner = inner
        self.message = self._inner_as_string()
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self._inner)})"

    def _inner_as_string(self) -> str:
        sections = []
        for identifier, errors in self._inner.items():
            error_messages = "\n    ".join(str(err) for err in errors[0])
            sections.append(f"{identifier}:\n    {error_messages}")

        return (
            "\nThe dataframe failed to pass the validation model. Below is a summary of all validation errors:\n"
            + "\n\n".join(sections)
        )
