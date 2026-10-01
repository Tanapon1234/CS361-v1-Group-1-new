"""Base for SQLModel/PostgreSQL DAO implementations.

`self.session` is the request-scoped session from `app.core.database.get_session`,
which commits or rolls back for you. Inside a DAO:

    self.session.get(Lecturer, lecturer_id)                      # by primary key
    self.session.exec(select(Lecturer).where(...)).all()         # query
    self.session.exec(select(func.count()).select_from(stmt.subquery())).one()   # total
    self.session.add(entity); self.session.flush(); self.session.refresh(entity)  # insert
    entity.sqlmodel_update(values); self.session.flush()          # update
    self.session.delete(entity); self.session.flush()             # delete

Never call `self.session.commit()` here.
"""

from sqlmodel import Session


class SqlDAO:
    def __init__(self, session: Session) -> None:
        self.session = session
