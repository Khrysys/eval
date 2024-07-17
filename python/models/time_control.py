from sqlmodel import Field, SQLModel, Session, select # type: ignore


class TimeControl(SQLModel, table=True):
    code: str = Field(primary_key=True)

    @staticmethod
    def get(code: str, *, session: Session):
        c = session.exec(select(TimeControl).where(TimeControl.code==code)).one_or_none()
        if c:
            return c
        c = TimeControl(code=code)
        session.add(c)
        return c
    