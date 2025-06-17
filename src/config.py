from dataclasses import dataclass
from typing import Optional, Self, Callable, Any


@dataclass
class ConfigPair:
    Key: str
    Value: str
    Opt: str

    @classmethod
    def deserialize(cls, row: list[str]):
        return cls(*row)

    def serialize(self):
        return [self.Key, self.Value, self.Opt]


@dataclass
class Config:
    configs: list[ConfigPair]

    @classmethod
    def empty(cls) -> Self:
        return cls([])

    @classmethod
    def from_list(cls, configs: list[ConfigPair]) -> Self:
        self = cls.empty()

        for pair in configs:
            self.add_config_pair(pair)
        return self

    def add_config_pair(self, pair: ConfigPair):
        self.configs.append(pair)

    def get(self, key: str) -> Optional[ConfigPair]:
        return next((pair for pair in self.configs if pair.Key == key), None)

    def get_all(self, key: str) -> list[ConfigPair]:
        return [pair for pair in self.configs if pair.Key == key]

    def get_value(self, key: str, default: Optional[Any] = None) -> Optional[str]:
        pair = self.get(key)
        if pair:
            return pair.Value
        return default

    def get_and_apply[T](self, key: str, func: Callable[[ConfigPair], T]):
        q = self.get(key)
        if q is not None:
            return func(q)
