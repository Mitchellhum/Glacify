from collections import defaultdict
from typing import Optional

from polars import DataFrame, col, concat_list, concat_str
from polars.exceptions import PolarsError
from polars.selectors import contains

from glacify.exceptions import GlacifyValidationException, GlacifyCriticalException
from glacify.meta import ValidationMetaClass


class ValidationBase(metaclass=ValidationMetaClass):
    """
    Base class that is used to define a validator class. The idea of the class is to improve
    readability of validation code for polars dataframes, while still integrating properly with
    other pipelines, such as excel file validations.

    Attributes
    ----------
    settings : ValidationSettings
        Allows a custom definition of all model-wide settings. Uses all default values is not set
        by the user.

    Examples
    --------
    >>> from polars import Expr, col, lit
    >>> from glacify import ValidationBase, Column, validator, ValidationSettings
    ...
    >>> class ExampleValidator(ValidationBase):
    ...    settings = ValidationSettings(strict=False)
    ...    id: int = Column(name="Index")
    ...    first_name: str = Column(name="First Name")
    ...    last_name: str = Column(name="Last Name")
    ...    address: str = Column(name="Address")
    ...    gross_income: float = Column(name="Gross-Income")
    ...
    ...    @validation_check(selection=["First Name", "Last Name"])
    ...    def check_is_alphabetic(column: str) -> tuple[Expr, str]:
    ...        # Anything that is not alphabetic needs to receive the error
    ...        expression = col(column).str.contains(pattern="/^[A-Za-z]+$/").not_()
    ...        error = f"{column} can only contain alphabetic characters!"
    ...
    ...        return expression, error
    ...
    ...    @validation_check(selection=["Gross-Income"])
    ...    def check_not_negative(column: str) -> tuple[Expr, str]:
    ...        expression = col(column).lt(lit(0.0))
    ...        error = f"{column} cannot be lower than 0!"
    ...
    ...        return expression, error
    """

    def __init__(
        self, dataframe: Optional[DataFrame] = None, strict: Optional[bool] = None
    ) -> None:
        self._dataframe = dataframe
        self._error_inner = defaultdict(list)

        if strict is not None:
            self.settings.strict = strict

        # A shortcut
        if dataframe is not None:
            self.validate(dataframe=dataframe)

    def _dataframe_as_error(self) -> None:
        """
        Transforms all new error columns in to a readable error message for the user.

        Raises
        ------
        GlacifyCriticalException
            Raised whenever Polars fails to execute the error expression.
        GlacifyValidationException
            Raised whenever errors are found during validation.
        """
        if not any("__error_" in column for column in self._dataframe.columns):
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
            raise GlacifyCriticalException(
                "Failed to execute error transformation"
            ) from error

        if dataframe.is_empty():
            return

        rows_by_identifier = dataframe.rows_by_key(key=["identifier"], unique=True)
        raise GlacifyValidationException(inner=rows_by_identifier)

    def _execute_validators(self) -> None:
        """
        Tries to execute all default and user defined validators.

        Raises
        ------
        GlacifyCriticalException
            Raised whenever Polars fails to execute the validator expressions.
        """
        try:
            self._dataframe = (
                self._dataframe.lazy()
                .with_columns(self._validator_expressions)
                .collect()
            )
        except PolarsError as error:
            raise GlacifyCriticalException(
                "Failed to execute validator expressions"
            ) from error

    def _execute_dtype_transformation(self) -> None:
        """
        Tries to execute a dtype transformation for if the dataframe has not been set
        to the proper dtypes yet.

        Raises
        ------
        GlacifyCriticalException
            Raised whenever Polars fails to execute the cast expressions.
        """
        try:
            expressions = [
                col(column).cast(dtype=dtype, strict=self.settings.strict).name.keep()
                for column, dtype in self._dataframe_schema.items()
            ]
            self._dataframe = self._dataframe.lazy().with_columns(expressions).collect()
        except PolarsError as error:
            raise GlacifyCriticalException(
                "Failed to execute dtype transformation: are the columns cleaned up properly?"
            ) from error

    def _execute_setters(self) -> None:
        """
        Tries to execute all default setters for each column.

        Raises
        ------
        GlacifyCriticalException
            Raised whenever Polars fails to execute the column expressions.
        """
        try:
            lazyframe = self._dataframe.lazy()

            for setter in self._setter_expressions:
                lazyframe = lazyframe.with_columns(setter)
            
            self._dataframe = lazyframe.collect()
        except PolarsError as error:
            raise GlacifyCriticalException(
                "Failed to execute setter expressions"
            ) from error

    def _validate_columns(self) -> None:
        """
        Validates whether all columns are actually existing inside the dataframe.

        Raises
        ------
        GlacifyCriticalException
            Raised whenever missing columns are found.
        """
        current_columns = self._dataframe.columns
        missing_columns = [
            column
            for column in self._dataframe_column_names
            if column not in current_columns
        ]

        if missing_columns:
            raise GlacifyCriticalException(
                f"Cannot find the following columns inside the dataframe, are the columns spelled correctly? '{missing_columns}'"
            )
    
    def _validate_identifiers(self) -> None:
        """
        Checks whether any identifiers exist, otherwise adds a row index as identifier.
        """
        if not self._identifier_columns:
            self._dataframe = self._dataframe.with_row_index(name="__index", offset=1)
            self._identifier_columns.append("__index")

    def validate(self, dataframe: DataFrame) -> None:
        """
        Validates a dataframe against default and user defined validation checks.

        Parameters
        ----------
        dataframe : DataFrame
            A Polars dataframe which needs to be validated.

        Raises
        ------
        GlacifyValidationException
            If any validation errors show up, this exception will be thrown.
            The validation contains a list of errors, either critical or
            row-based.
        """
        self._dataframe = dataframe
        self._error_inner = defaultdict(list)

        self._validate_identifiers()
        self._validate_columns()
        self._execute_setters()
        self._execute_dtype_transformation()
        self._execute_validators()
        self._dataframe_as_error()

    def dump(self) -> DataFrame:
        """
        Returns the current state of the dataframe.

        Returns
        -------
        DataFrame
            The current state of the dataframe.
        """
        return self._dataframe.lazy().select(self._dataframe_column_names).collect()
