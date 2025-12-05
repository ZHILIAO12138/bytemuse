from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DBBase:

    def __str__(self):
        return f'{self.__class__.__name__}({self.__dict__})'

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
