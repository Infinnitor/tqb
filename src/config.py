from dataclasses import dataclass


@dataclass
class ConfigPair:
    key: str
    value: str
    opt: str

    @classmethod
    def deserialize(cls, row: list[str]):
        return cls(*row)

    def serialize(self):
        return [self.key, self.value, self.opt]


@dataclass
class Config:
    configs: dict[str, ConfigPair]

    @classmethod
    def empty(cls):
        return Config({})

    @classmethod
    def from_list(cls, configs: list[ConfigPair]):
        self = cls.empty()

        for pair in configs:
            self.add_config_pair(pair)

    def add_config_pair(self, pair):
        self.configs[pair.key] = pair

    def get(self, key):
        return self.configs.get(key, None)

    def get_and_apply(self, key, func):
        q = self.get(key)
        if q is not None:
            return func(q)
