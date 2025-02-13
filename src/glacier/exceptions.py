class GlacierCriticalException(Exception):
    pass


class GlacierValidationException(Exception):
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
