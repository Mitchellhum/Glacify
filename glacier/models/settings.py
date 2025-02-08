from dataclasses import dataclass
from typing import Callable


@dataclass
class FunctionSettings:
    check: Callable
    columns: list[str]
