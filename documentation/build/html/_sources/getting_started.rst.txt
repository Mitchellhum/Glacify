Getting Started
===============
Welcome to the quick-start guide for the Glacier dataframe validation package.

Let's get started with installing the package

.. code-block:: bash

  > python3 -m pip install glacier

Glacier comes with shipped with a polars version lower than 2.0.0

To make our model, we must first identify our dataframe layout. Let's say that we have the following CSV:
``> index;first name;last name;address;datetime added``

We can design our validation model as follows:

.. code-block:: python
    
    from datetime import datetime

    from glacier import ValidationBase, Column, ValidationSettings

    class ExampleValidator(ValidationBase):
        settings = ValidationSettings(strict=True)
        id: int = Column(name="index", is_identifier=True)
        first_name: str = Column(name="first name")
        last_name: str = Column(name="last name")
        address: str = Column(name="address")
        datetime_added: datetime = Column(name="datetime added")
  
Afterwards, we can use this validator to validate our dataframe:

.. code-block:: 
    
    import polars as pl

    if __name__ == "__main__":
        validator = ExampleValidator()
        dataframe = pl.read_csv("./test.csv")

        # Validate!
        validator.validate(dataframe=dataframe)

        new_dataframe = validator.dump()

Inside the Glacier Validator, you can define your own validation checks outside of the default checks.

.. code-block:: python

    from datetime import datetime

    import polars as pl
    from glacier import ValidationBase, Column, ValidationSettings, validation_check

    class ExampleValidator(ValidationBase):
        settings = ValidationSettings(strict=True)
        id: int = Column(name="index", is_identifier=True)
        first_name: str = Column(name="first name")
        last_name: str = Column(name="last name")
        address: str = Column(name="address")
        datetime_added: datetime = Column(name="datetime added")

        @validation_check(selection=["last name"])
        def check_is_hummel(column: str) -> tuple[pl.Expr, str]:
            expression = pl.col(column).eq(pl.lit("Hummel"))
            error = f"{column} must always be 'Hummel'!"

            return expression, error

If the data were to have last names that are not 'Hummel', the validator will throw a GlacierValidationException,
which will look like this:

.. code-block:: python

    # The dataframe failed to pass the validation model. Below is a summary of all validation errors:
    # 2:
    #     last name must always be 'Hummel'!

Till this far for the quick-start guide, feel free to look around in the API Documentation for more default validators and 
other tricks!