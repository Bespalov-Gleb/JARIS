from sqlalchemy import Integer, String, Column

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    """
    id
    login
    password
    openai_token
    picovoice_token
    eden_token
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False)
    password = Column(String, nullable=False)
    openai_token = Column(String, nullable=False)
    picovoice_token = Column(String, nullable=False)
    eden_token = Column(String, nullable=False)

