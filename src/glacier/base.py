from collections import defaultdict
from typing import Optional

from polars import DataFrame, col
from polars.exceptions import PolarsError

from glacier.meta import ValidationMetaClass
from glacier.exceptions import StructuralException
from glacier.exceptions import GlacierValidationException, ValidationCheckException


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

    def _execute_validators(self) -> None:
        self._dataframe = (
            self._dataframe.lazy().with_columns(self._validator_expressions).collect()
        )

    def _execute_dtype_transformation(self) -> None:
        expressions = [
            col(column).cast(dtype=dtype, strict=self._strict_dtypes).name.keep()
            for column, dtype in self._dataframe_schema.items()
        ]
        self._dataframe = self._dataframe.lazy().with_columns(expressions).collect()

    def _execute_setters(self) -> None:
        self._dataframe = (
            self._dataframe.lazy().with_columns(self._setter_expressions).collect()
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

        self._execute_setters()
        self._execute_dtype_transformation()
        self._execute_validators()

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
        # return self._dataframe.lazy().select(self._dataframe_column_names).collect()
        return self._dataframe
