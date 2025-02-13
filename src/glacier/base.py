from collections import defaultdict
from typing import Optional

import polars.selectors as cs
from polars import DataFrame, col, concat_list, concat_str
from polars.exceptions import PolarsError

from glacier.meta import ValidationMetaClass
from glacier.exceptions import GlacierValidationException, GlacierCriticalException


class ValidationBase(metaclass=ValidationMetaClass):
    def __init__(
        self,
        dataframe: Optional[DataFrame] = None,
        strict_dtypes: bool = True,
    ) -> None:
        self._dataframe = dataframe
        self._strict_dtypes = strict_dtypes
        self._error_inner = defaultdict(list)

        # A shortcut
        if dataframe:
            self.validate(dataframe=dataframe)

    def _dataframe_as_error(self) -> None:
        try:
            dataframe = (
                self._dataframe.lazy()
                .select(
                    [
                        concat_str(self._identifier_columns, separator="_").alias(
                            "identifier"
                        ),
                        concat_list(cs.contains("__error_"))
                        .list.drop_nulls()
                        .alias("errors"),
                    ]
                )
                .filter(col("errors").list.len() > 0)
                .collect()
            )
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute error transformation"
            ) from error

        if dataframe.is_empty():
            return

        rows_by_identifier = dataframe.rows_by_key(key=["identifier"], unique=True)
        raise GlacierValidationException(inner=rows_by_identifier)

    def _execute_validators(self) -> None:
        try:
            self._dataframe = (
                self._dataframe.lazy()
                .with_columns(self._validator_expressions)
                .collect()
            )
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute validator expressions"
            ) from error

    def _execute_dtype_transformation(self) -> None:
        try:
            expressions = [
                col(column).cast(dtype=dtype, strict=self._strict_dtypes).name.keep()
                for column, dtype in self._dataframe_schema.items()
            ]
            self._dataframe = self._dataframe.lazy().with_columns(expressions).collect()
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute dtype transformation: are the columns cleaned up properly?"
            ) from error

    def _execute_setters(self) -> None:
        try:
            self._dataframe = (
                self._dataframe.lazy().with_columns(self._setter_expressions).collect()
            )
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute setter expressions"
            ) from error

    def _validate_columns(self) -> None:
        current_columns = self._dataframe.columns
        missing_columns = [
            column
            for column in self._dataframe_column_names
            if column not in current_columns
        ]

        if missing_columns:
            raise GlacierCriticalException(
                f"Cannot find the following columns inside the dataframe, are the columns spelled correctly? '{missing_columns}'"
            )

    def validate(self, dataframe: DataFrame) -> None:
        """
        Validates a dataframe against the user defined validation checks.

        Parameters
        ----------
        dataframe : DataFrame
            A Polars dataframe which needs to be validated.

        Raises
        ------
        GlacierValidationException
            If any validation errors show up, this exception will be thrown.
            The validation contains a list of errors, either critical or
            row-based.
        """
        self._dataframe = dataframe
        self._error_inner = defaultdict(list)

        self._validate_columns()
        self._execute_setters()
        self._execute_dtype_transformation()
        self._execute_validators()
        self._dataframe_as_error()

    def dump_dataframe(self) -> DataFrame:
        return self._dataframe.lazy().select(self._dataframe_column_names).collect()
