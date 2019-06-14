from datetime import datetime as dt
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


engine = create_engine('sqlite:///hypercube.db')
Base = declarative_base()

class SerialOfInterest(Base):
    __tablename__ = 'serail_of_interest'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String)
    date_added = Column(DateTime, default=dt.now())
    date_last_seen = Column(DateTime)

Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)