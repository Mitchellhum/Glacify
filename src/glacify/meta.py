from functools import partial
from inspect import signature
from typing import Callable, Generator

from polars import Expr, lit, when

from glacify.column import Column
from glacify.settings import ValidationSettings
from glacify.types import PolarsType


IGNORE_ATTRIBUTES = [
    "settings",
    "_setter_expressions",
    "_validator_expressions",
    "_model_validator_expressions",
    "_identifier_columns",
    "_dataframe_column_mapping",
    "_dataframe_column_names",
    "_dataframe_schema",
    "_index_generator",
]


def index_generator() -> Generator[int, None, None]:
    start = 1
    while True:
        yield start
        start += 1


class ValidationMetaClass(type):
    _setter_expressions: list[Expr]
    _validator_expressions: list[Expr]
    _model_validator_expressions: list[Expr]
    _identifier_columns: list[str]
    _dataframe_column_mapping: list[Column]
    _dataframe_column_names: list[str]
    _dataframe_schema: dict[str, PolarsType]
    _index_generator = index_generator()

    @classmethod
    def _resolve_columns(cls, namespace: dict) -> None:
        """
        Checks the annotated types of the user added column attributes and
        transforms those types in to Polars types.
        """
        class_annotations = namespace.get("__annotations__", {})
        settings = namespace.get("settings", {})

        for name, type_ in class_annotations.items():
            # We defined some attributes ourselves too, so ignore those
            if name in IGNORE_ATTRIBUTES:
                continue

            column: Column = namespace.get(name, Column(name=name))
            column.resolve(type_=type_, strict=settings.strict)

            # Multiple identifiers are allowed
            if column.is_identifier:
                namespace["_identifier_columns"].append(column.name)

            namespace["_dataframe_column_mapping"][column.name] = name
            namespace["_dataframe_column_names"].append(column.name)
            namespace["_dataframe_schema"][column.name] = column._type

    @classmethod
    def _create_validator(cls, expression: Expr, error: str) -> partial[Expr]:
        """
        Creates a partial out of the user defined function, so that it is in line
        with the other validators.
        """

        def _full_expression(index: int) -> Expr:
            return when(expression).then(lit(error)).alias(f"__error_{index}")

        return partial(_full_expression)

    @classmethod
    def _validate_function(cls, function_: Callable) -> bool:
        """
        Checks if a function is a user-defined validator with proper signature.

        Raises
        ------
        ValueError
            Raised whenever the user defined function does not accept the 'column_name' parameter.
        """
        if not getattr(function_, "_is_validator", False):
            return False

        if len(signature(function_).parameters) == 0:
            raise ValueError(
                f"Expected '{function_.__name__}' to take at least 1 parameter: 'column_name'"
            )

        return True

    @classmethod
    def _validate_columns(
        cls, columns: list[str], dataframe_columns: list[str]
    ) -> None:
        """
        Checks if the selected columns exist in the model.

        Raises
        ------
        ValueError
            Raised whenever the selected columns are not defined in the model.
        """
        missing = [
            col for col in columns if col != "*" and col not in dataframe_columns
        ]
        if missing:
            raise ValueError(f"Columns {missing} do not exist in the model!")

    @classmethod
    def _resolve_user_defined_expressions(cls, namespace: dict) -> None:
        """
        Finds all functions that have been defined by the user via the validator wrapper.

        Raises
        ------
        ValueError
            Raised whenever the user output is not a tuple of Expr (validator) and str (error).
        """
        dataframe_columns = namespace["_dataframe_column_names"]
        column_mapping = namespace.get("_dataframe_column_mapping", {})

        for user_function in filter(callable, namespace.values()):
            # The function needs to be wrapped (which gives it an id attribute)
            if not cls._validate_function(function_=user_function):
                continue

            # Lets make sure all columns are valid
            columns = getattr(user_function, "_for_columns")
            cls._validate_columns(columns=columns, dataframe_columns=dataframe_columns)

            if "*" in columns:
                columns = cls._dataframe_column_names

            # For each column assigned by the user, add the validator to the list
            for column_name in columns:
                attribute_name = column_mapping.get(column_name)
                column: Column = namespace.get(attribute_name)

                # We double check if we get the expected output
                try:
                    expression, error = user_function(column_name)
                    if not isinstance(expression, Expr) or not isinstance(error, str):
                        raise ValueError
                except:
                    raise ValueError(
                        f"Expected '{user_function.__name__}' to return 2 values: a filter expression and its error!"
                    )

                # Add the validator
                validator = cls._create_validator(expression=expression, error=error)
                column.add_validator(validator=validator)

    @classmethod
    def _resolve_expressions(cls, namespace: dict) -> None:
        """
        Resolves all user and default setters and validator expressions.
        """
        class_annotations = namespace.get("__annotations__", {})

        for name, type_ in class_annotations.items():
            # We defined some attributes ourselves too, so ignore those
            if name in IGNORE_ATTRIBUTES:
                continue

            column: Column = namespace.get(name, Column(name=name))

            # Get all setters and validators that are assigned to the columns
            setters = column.get_setters()
            validators = column.get_validators()

            # Set them to the model so it is easier to read in the end
            for setter in setters:
                namespace["_setter_expressions"].append(setter)

            # Validators return errors, so we need to add a unique identifier for the errors
            for validator in validators:
                namespace["_validator_expressions"].append(
                    validator(index=next(cls._index_generator))
                )

    def __new__(cls, name: str, bases: tuple, namespace: dict) -> "ValidationMetaClass":
        if not namespace.get("settings"):
            namespace.setdefault("settings", ValidationSettings())

        namespace.setdefault("_identifier_columns", [])
        namespace.setdefault("_setter_expressions", [])
        namespace.setdefault("_validator_expressions", [])
        namespace.setdefault("_model_validator_expressions", [])
        namespace.setdefault("_dataframe_column_mapping", {})
        namespace.setdefault("_dataframe_column_names", [])
        namespace.setdefault("_dataframe_schema", {})

        cls._resolve_columns(namespace=namespace)
        cls._resolve_user_defined_expressions(namespace=namespace)
        cls._resolve_expressions(namespace=namespace)
        return super().__new__(cls, name, bases, namespace)
