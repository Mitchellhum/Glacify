from datetime import date, datetime

from polars import String, Int64, Boolean, Float64, List, Date, Datetime

PythonType = str | int | float | bool | list | date | datetime
PolarsType = String | Int64 | Float64 | Boolean | List | Date | Datetime

PYTHON_POLARS_TYPE_MAPPING = {
    str: String,
    int: Int64,
    float: Float64,
    bool: Boolean,
    list: List,
    date: Date,
    datetime: Datetime,
}
