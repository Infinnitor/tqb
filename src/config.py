from dataclasses import dataclass
from typing import Optional, Self


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
    def empty(cls):
        return Config([])

    @classmethod
    def from_list(cls, configs: list[ConfigPair]) -> Self:
        self = cls.empty()

        for pair in configs:
            self.add_config_pair(pair)
        return self

    def add_config_pair(self, pair):
        self.configs.append(pair)

    def get(self, key) -> Optional[ConfigPair]:
        return next((pair for pair in self.configs if pair.Key == key), None)

    def get_all(self, key) -> list[ConfigPair]:
        return [pair for pair in self.configs if pair.Key == key]

    def get_value(self, key, default=None):
        pair = self.get(key)
        if pair:
            return pair.Value
        return default

    def get_and_apply(self, key, func):
        q = self.get(key)
        if q is not None:
            return func(q)
