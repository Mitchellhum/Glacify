from collections import defaultdict
from inspect import signature
from typing import Optional

from polars import DataFrame, col
from polars.exceptions import PolarsError

from glacier.core.meta import ValidationMetaClass
from glacier.exc.model import StructuralException
from glacier.exc.validation import GlacierValidationException, ValidationCheckException


class ValidationBase(metaclass=ValidationMetaClass):
    def __init__(
        self,
        dataframe: Optional[DataFrame] = None,
        ignore_extra_columns: bool = True,
        strict_dtypes: bool = True,
    ) -> None:
        self._dataframe = dataframe
        self._ignore_extra_columns = ignore_extra_columns
        self._strict_dtypes = strict_dtypes

        self._error_inner = defaultdict(list)

        # A shortcut
        if dataframe:
            self.validate(dataframe=dataframe)

    def _initial_column_validation(self) -> None:
        """
        Executes the default column validation as first line validation. Checks if the provided dataframe
        actually contains the expected columns.
        """
        required_columns = list(self._polars_schema.keys())
        dataframe_columns = self._dataframe.columns

        # Flag all missing columns
        missing_columns = [
            column for column in required_columns if column not in dataframe_columns
        ]
        if missing_columns:
            raise StructuralException(
                name="Column Error",
                message=f"Some of the defined columns are missing. Missing columns: {missing_columns}",
            )

        # If we do not want to ignore the extra columns, they should at least be flagged.
        if not self._ignore_extra_columns:
            self._dataframe = self._dataframe.lazy().select(required_columns).collect()

    def _initial_dtype_validation(self) -> None:
        """
        Executes the default datatype validation as first line validation. Checks if the provided dataframe
        can be cast to the correct datatypes as stated in the validation model.
        """
        expressions = [
            col(name).cast(dtype=dtype, strict=self._strict_dtypes).name.keep()
            for name, dtype in self._polars_schema.items()
        ]

        # We executed quite some expressions at once, so a general exception is fine
        try:
            self._dataframe = self._dataframe.lazy().with_columns(expressions).collect()
        except PolarsError as error:
            raise StructuralException(
                name="Datatype Error",
                message=f"Failed to transform the columns to the annotated datatypes. Please make sure that columns are cleaned properly to allow the transformation. \n\
    If datatype conversion needs to be less strict, be sure to set the 'strict_dtypes' parameter to false! Error: {error}",
            ) from error

    def _run_initial_validations(self) -> None:
        """
        Execute the two initial validations that are included by default.
        """
        self._initial_column_validation()
        self._initial_dtype_validation()

    def _run_validations(self) -> None:
        """
        Run all the user defined validation functions in sequence.
        """
        for settings in self._validation_functions:
            # Each user defined function contains a set of settings
            check = settings.check
            selection = (
                self._identifier_columns + settings.columns
                if settings.columns != ["*"]
                else settings.columns
            )

            # Create a lazyframe with the user provided selection
            dataframe = self._dataframe.lazy().select(selection)

            try:
                # Implemented for when there will be more arguments
                arguments = [dataframe]
                function_signature = signature(check)
                argument_count = len(function_signature.parameters)

                # Add all the arguments dynamically
                check(*arguments[:argument_count])

            except ValidationCheckException as error:
                identifiers = (
                    error._identifier
                    if isinstance(error._identifier, list)
                    else [error._identifier]
                )
                for identifier in identifiers:
                    self._error_inner[identifier].append(error.message)

            except Exception as error:
                self._error_inner["Critical Error"].append(error)

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

        try:
            self._run_initial_validations()
        except StructuralException as error:
            self._error_inner[error.name].append(error.message)

        self._run_validations()

        if self._error_inner:
            raise GlacierValidationException(inner=self._error_inner)

    def dump_dataframe(self) -> DataFrame:
        """
        Returns the dataframe after validation. Currently, it is not possible
        to change the dataframe while validating, however, the dtype cast
        - which is default for validation - does alter the dataframe dtypes.

        Returns
        -------
        DataFrame
            The current state of the dataframe.
        """
        return self._dataframe
