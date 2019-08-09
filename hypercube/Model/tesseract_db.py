from sqlalchemy import Column, ForeignKey, MetaData, String, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
import pymssql
import os


def connect():
    return pymssql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_DATABASE"),
    )


engine = create_engine("mssql+pymssql://", creator=connect)

metadata = MetaData()
metadata.reflect(
    engine,
    only=["SCCall", "SCProd", "SCEmploy", "SCFSR", "SCPart", "SPStock", "SCSite"],
)

Base = automap_base(metadata=metadata)
Base.prepare()
Call = Base.classes.SCCall
Product = Base.classes.SCProd
Employ = Base.classes.SCEmploy
FSR = Base.classes.SCFSR
Part = Base.classes.SCPart
Stock = Base.classes.SPStock
Site = Base.classes.SCSite
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
