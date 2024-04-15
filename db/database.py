from sqlalchemy import create_engine
from sqlalchemy.orm import Session, Query
from models import Base


class Database:
    def __init__(self, path='sqlite:///jarvis.db', _base=Base):
        self.path = path
        self._base = _base
        self.engine = self._create_db()
        self.session = self._create_session()

    def _create_db(self):
        # create connection
        engine = create_engine(self.path)
        engine.connect()

        # create tables
        self._base.metadata.create_all(engine)

        return engine

    def _create_session(self):
        return Session(bind=self.engine)

    # adds element/elements in corresponded table
    def add(self, element):

        if isinstance(element, list):
            self.session.add_all([elem for elem in element])
        else:
            self.session.add(element)

        self.session.commit()

    # return corresponded table
    def get_query(self, model) -> Query:

        return self.session.query(model)  # query

        #  query.all() - вернет всю таблицу в виде list
        #  также query итерируемый объект, то есть можно делать:
        #  for user in query:
        #       print(user.id)

    def delete(self, element):
        self.session.delete(element)
        self.session.commit()

