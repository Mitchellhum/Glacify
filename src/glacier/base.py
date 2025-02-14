from collections import defaultdict
from typing import Optional

from polars import DataFrame, col, concat_list, concat_str
from polars.exceptions import PolarsError
from polars.selectors import contains

from glacier.exceptions import GlacierValidationException, GlacierCriticalException
from glacier.meta import ValidationMetaClass
from glacier.settings import ValidationSettings


class ValidationBase(metaclass=ValidationMetaClass):
    settings = ValidationSettings()

    def __init__(
        self, dataframe: Optional[DataFrame] = None, strict: Optional[bool] = None
    ) -> None:
        self._dataframe = dataframe
        self._error_inner = defaultdict(list)

        if strict is not None:
            self.settings = ValidationSettings(strict=strict)

        # A shortcut
        if dataframe is not None:
            self.validate(dataframe=dataframe)

    def _dataframe_as_error(self) -> None:
        """
        Transforms all new error columns in to a readable error message for the user.

        Raises
        ------
        GlacierCriticalException
            Raised whenever Polars fails to execute the error expression.
        GlacierValidationException
            Raised whenever errors are found during validation.
        """
        if "__error_" not in self._dataframe.columns:
            return

        try:
            dataframe = (
                self._dataframe.lazy()
                .select(
                    [
                        concat_str(self._identifier_columns, separator="_").alias(
                            "identifier"
                        ),
                        concat_list(contains("__error_"))
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
        """
        Tries to execute all default and user defined validators.

        Raises
        ------
        GlacierCriticalException
            Raised whenever Polars fails to execute the validator expressions.
        """
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
        """
        Tries to execute a dtype transformation for if the dataframe has not been set
        to the proper dtypes yet.

        Raises
        ------
        GlacierCriticalException
            Raised whenever Polars fails to execute the cast expressions.
        """
        try:
            expressions = [
                col(column).cast(dtype=dtype, strict=self.settings.strict).name.keep()
                for column, dtype in self._dataframe_schema.items()
            ]
            self._dataframe = self._dataframe.lazy().with_columns(expressions).collect()
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute dtype transformation: are the columns cleaned up properly?"
            ) from error

    def _execute_setters(self) -> None:
        """
        Tries to execute all default setters for each column.

        Raises
        ------
        GlacierCriticalException
            Raised whenever Polars fails to execute the column expressions.
        """
        try:
            self._dataframe = (
                self._dataframe.lazy().with_columns(self._setter_expressions).collect()
            )
        except PolarsError as error:
            raise GlacierCriticalException(
                "Failed to execute setter expressions"
            ) from error

    def _validate_columns(self) -> None:
        """
        Validates whether all columns are actually existing inside the dataframe.

        Raises
        ------
        GlacierCriticalException
            Raised whenever missing columns are found.
        """
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
        Validates a dataframe against the default and user defined validation checks.

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
        """
        Returns the current state of the dataframe.

        Returns
        -------
        DataFrame
            The current state of the dataframe.
        """
        return self._dataframe.lazy().select(self._dataframe_column_names).collect()
