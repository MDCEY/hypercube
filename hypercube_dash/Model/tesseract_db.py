from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
engine = create_engine('mssql+pyodbc://Tesseract:Te55eract@ESOLBRANCHLIVE')

metadata = MetaData()
metadata.reflect(engine, only=['SCCall'])

Base = automap_base(metadata=metadata)
Base.prepare()
Call = Base.classes.SCCall

Session = sessionmaker(bind=engine)


# session = Session()
# print(session.query(Call).count()) # Working