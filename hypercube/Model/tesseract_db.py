from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, scoped_session,relationship
from sqlalchemy import create_engine, MetaData, String, Column, ForeignKey
engine = create_engine('mssql+pyodbc://Tesseract:Te55eract@ESOLBRANCHLIVE')

metadata = MetaData()
metadata.reflect(engine, only=['SCCall','SCProd'])

Base = automap_base(metadata=metadata)
Base.prepare()
Call = Base.classes.SCCall
Product = Base.classes.SCProd

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# session = Session()
# print(session.query(Call).count()) # Working