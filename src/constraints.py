import consts
from dataclasses import dataclass
import fnmatch
from colorama import Fore
from typing import Self, Any, Callable, Optional


CONSTRAINT_MAP: dict[str, Callable[[str], Any]] = {
    "int": int,
    "bool": lambda x: x not in ("FALSE", "False", "false", "0", ""),
}


@dataclass
class Constraint:
    HeaderName: str
    Type: str
    Variant: str
    Default: str
    ColWidth: Optional[int]
    Colours: str
    Role: str
    Autofill: bool
    Hide: bool
    AutoHeader: bool

    @classmethod
    def empty(cls, header_name: str) -> Self:
        return cls(
            HeaderName=header_name,
            Type="",
            Variant="",
            Default="",
            ColWidth=None,
            Colours="",
            Role="",
            Autofill=False,
            Hide=False,
            AutoHeader=False
        )

    @classmethod
    def kwargs(cls, **kwargs: Any) -> Self:
        for key in consts.CONSTRAINTS_HEADERS:
            if key not in kwargs:
                kwargs[key] = ""

        return cls(**kwargs)

    @classmethod
    def deserialize(cls, row: list[Any]) -> Self:
        if row[1] and row[1] not in CONSTRAINT_MAP.keys():
            raise ValueError(f"Invalid constraint type '{row[1]}' for column {row[0]}")

        if row[4] and row[4].isnumeric():
            row[4] = int(row[4])
        else:
            row[4] = None

        row[7] = CONSTRAINT_MAP["bool"](row[7])
        row[8] = CONSTRAINT_MAP["bool"](row[8])
        row[9] = CONSTRAINT_MAP["bool"](row[9])

        return cls(*row)

    def serialize(self) -> list[str]:
        row = []
        for header in consts.CONSTRAINTS_HEADERS:
            row.append(self.__dict__[header])

        return row

    def apply_colour(self, value: Any) -> str:
        def get_clr(name: str) -> str:
            if name.startswith("#"):
                if len(name) != 7:
                    return Fore.RESET

                try:
                    r, g, b = int(name[1:3], 16), int(name[3:5], 16), int(name[5:], 16)
                    return f"\033[38;2;{r};{g};{b}m"

                except ValueError:
                    return Fore.RESET

            return Fore.__dict__.get(name, Fore.RESET)

        if not isinstance(value, str):
            value = str(value)

        colours = self.Colours.split("|")
        if not colours:
            return value

        for cpair in colours:
            pattern, _, colour = cpair.partition("=")

            if fnmatch.fnmatch(value.lower(), pattern.lower()):
                return get_clr(colour) + str(value) + Fore.RESET

        return value

    def apply_default(self, value: str) -> Any:
        return self.Default or value

    def constrain_type(self, value: str) -> Any:
        if self.Type and CONSTRAINT_MAP.get(self.Type):
            try:
                return CONSTRAINT_MAP[self.Type](value)
            except ValueError:
                raise AssertionError(
                    f"constraint failed for type {self.Type} on column {self.HeaderName}"
                )
        return value

    def get_variant_constraints(self) -> list[str]:
        return [""] + self.Variant.split("|")

    def constrain_variant(self, value: str) -> str:
        lvalue = str(value).lower()

        if self.Variant:
            for variant in self.get_variant_constraints():
                lvariant = variant.lower()

                if self.Autofill:
                    if lvariant.startswith(lvalue):
                        return variant

                if lvariant == lvalue:
                    return variant

            raise AssertionError(
                f"column {self.HeaderName} must be one of {tuple(self.get_variant_constraints())}"
            )

        return value
