from functools import lru_cache
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel, Session, select


class Opening(SQLModel, table=True):
    __tableargs__ = (UniqueConstraint('url'), )
    eco: str = Field(primary_key=True)
    url: str

    @staticmethod
    def get(eco: str, url: str = "", *, session: Session):
        o = session.exec(select(Opening).where(Opening.eco==eco)).one_or_none()
        if o:
            return o
        o = Opening(eco=eco, url=url)
        session.add(o)
        return o
