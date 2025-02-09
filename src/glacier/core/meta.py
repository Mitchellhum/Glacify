from typing import get_args, get_origin, List as TypedList
from polars import String, Int64, Boolean, Float64, List

from glacier.models.column import Column
from glacier.models.settings import FunctionSettings

PYTHON_TYPES = str | int | float | bool | list
POLARS_TYPES = String | Int64 | Float64 | Boolean | List

PYTHON_POLARS_TYPE_MAPPING = {
    str: String,
    int: Int64,
    float: Float64,
    bool: Boolean,
    list: List,
}

IGNORE_ATTRIBUTES = [
    "_validation_functions",
    "_identifier_columns",
    "_polars_schema",
]


class ValidationMetaClass(type):
    _validation_functions: list[FunctionSettings]
    _identifier_columns: list[str]
    _polars_schema: dict[str, POLARS_TYPES]

    @classmethod
    def _resolve_polars_type(cls, type_: PYTHON_TYPES) -> POLARS_TYPES:
        """
        Resolves the types as annotated by the user and transforms them to Polars
        types. Will be used for casting later on.

        Raises
        ------
        TypeError
            Raised whenever a list is assigned as type, but without the inner type.
        """
        origin, args = get_origin(type_), get_args(type_)

        # Do we have a list?
        if origin in {list, TypedList} or type_ in {list, TypedList}:
            if not args:
                raise TypeError("List annotations need to have an inner type!")
            return PYTHON_POLARS_TYPE_MAPPING[list](cls._resolve_polars_type(args[0]))

        # Warn the user for now
        if type_ not in PYTHON_POLARS_TYPE_MAPPING:
            print(
                f"WARNING! There is currently no support yet for type '{type_}', defaulting to String."
            )

        return PYTHON_POLARS_TYPE_MAPPING.get(type_, String)

    @classmethod
    def _resolve_column_types(cls, namespace: dict) -> None:
        """
        Checks the annotated types of the user added column attributes and
        transforms those types in to Polars types.
        """
        namespace.setdefault("_polars_schema", {})
        namespace.setdefault("_identifier_columns", [])
        class_annotations = namespace.get("__annotations__", {})

        for name, type_ in class_annotations.items():
            # We defined some attributes ourselves too, so ignore those
            if name in IGNORE_ATTRIBUTES:
                continue

            column = namespace.get(name, Column(name=name))
            # Multiple identifiers are allowed
            if column.is_identifier:
                namespace["_identifier_columns"].append(column.name)

            # Set the polars types for later use
            namespace["_polars_schema"][column.name] = cls._resolve_polars_type(type_)

    @classmethod
    def _resolve_validation_functions(cls, namespace: dict) -> None:
        """
        Finds all functions that have been defined by the user via the validation_check wrapper.

        Raises
        ------
        ValueError
            Raised whenever the columns that the user provided for selection, do not exist in the model.
        """
        namespace.setdefault("_validation_functions", [])

        # Get all functions from the namespace
        for value in filter(callable, namespace.values()):

            # Check if the function is tagged by the wrapper
            if getattr(value, "_is_validation_function", False):

                # Get the columns that the user tagged for selection
                columns = getattr(value, "_column_selection")

                if any(
                    col not in namespace["_polars_schema"]
                    for col in columns
                    if col != "*"
                ):
                    missing = [
                        col for col in columns if col not in namespace["_polars_schema"]
                    ]
                    raise ValueError(f"Columns {missing} do not exist in the model!")

                namespace["_validation_functions"].append(
                    FunctionSettings(check=value, columns=columns)
                )

    def __new__(cls, name: str, bases: tuple, namespace: dict) -> "ValidationMetaClass":
        cls._resolve_column_types(namespace=namespace)
        cls._resolve_validation_functions(namespace=namespace)
        return super().__new__(cls, name, bases, namespace)
