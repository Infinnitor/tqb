import consts
from dataclasses import dataclass
import fnmatch
from colorama import Fore
from typing import Self, Any


CONSTRAINT_MAP = {
    "int": int,
    "bool": lambda x: x not in ("FALSE", "False", "false", "0", ""),
}


@dataclass
class Constraint:
    HeaderName: str
    ConstrainType: str
    ConstrainVariant: str
    Default: str
    ColWidth: int
    Colours: str
    Role: str
    Autofill: bool

    @classmethod
    def empty(cls, header_name: str):
        return cls(
            *[
                header_name if k == "HeaderName" else ""
                for k in consts.CONSTRAINTS_HEADERS
            ]
        )

    @classmethod
    def kwargs(cls, **kwargs: dict[str, str]):
        for key in consts.CONSTRAINTS_HEADERS:
            if key not in kwargs:
                kwargs[key] = ""

        return cls(**kwargs)

    @classmethod
    def deserialize(cls, row: list[str]) -> Self:
        if row[1] and row[1] not in CONSTRAINT_MAP.keys():
            raise ValueError(f"Invalid constraint type '{row[1]}' for column {row[0]}")

        if row[4] and row[4].isnumeric():
            row[4] = int(row[4])

        row[7] = CONSTRAINT_MAP["bool"](row[7])

        return cls(*row)

    # TODO: Make this more ironclad
    def serialize(self):
        row = []
        for header in consts.CONSTRAINTS_HEADERS:
            row.append(self.__dict__[header])

        return row

    def apply_colour(self, value: Any):
        if not isinstance(value, str):
            value = str(value)

        colours = self.Colours.split("|")
        if not any(colours):
            return value

        for cpair in colours:
            pattern, _, colour = cpair.partition("=")

            if fnmatch.fnmatch(value.lower(), pattern.lower()):
                return Fore.__dict__.get(colour, Fore.RESET) + str(value) + Fore.RESET

        return value

    def apply_default(self, value: Any):
        return self.Default or value

    def constrain_type(self, value: Any) -> Any:
        if self.ConstrainType and CONSTRAINT_MAP.get(self.ConstrainType):
            try:
                return CONSTRAINT_MAP[self.ConstrainType](value)
            except ValueError:
                raise AssertionError(f"constraint failed for type {self.ConstrainType} on column {self.HeaderName}")
        return value

    def get_variant_constraints(self):
        return [""] + self.ConstrainVariant.split("|")

    def constrain_variant(self, value: Any) -> Any:
        lvalue = str(value).lower()

        if self.ConstrainVariant:
            for variant in self.get_variant_constraints():
                lvariant = variant.lower()

                if self.Autofill:
                    if lvariant.startswith(lvalue):
                        return variant

                if lvariant == lvalue:
                    return variant

            raise ValueError(f"constraint for ConstrainVariant failed for value \"{value}\" on column {self.HeaderName} (must be one of {self.get_variant_constraints()})")

        return value
