class StructuralException(Exception):
    def __init__(self, name: str, message: str) -> None:
        self.name = name
        self.message = message
        super().__init__(message)


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
            error_messages = "\n    ".join(str(err) for err in errors)
            sections.append(f"{identifier}:\n    {error_messages}")

        return (
            "\nThe dataframe failed to pass the validation model. Below is a summary of all validation errors:\n"
            + "\n\n".join(sections)
        )


class ValidationCheckException(Exception):
    def __init__(self, identifier: str | list[str], message: str) -> None:
        self._identifier = identifier
        self.message = message
        super().__init__(message)
