from sqlalchemy import Column, ForeignKey, MetaData, String, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

engine = create_engine("mssql+pyodbc://Tesseract:Te55eract@ESOLBRANCHLIVE")

metadata = MetaData()
metadata.reflect(engine, only=["SCCall", "SCProd"])

Base = automap_base(metadata=metadata)
Base.prepare()
Call = Base.classes.SCCall
Product = Base.classes.SCProd

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# session = Session()
# print(session.query(Call).count()) # Working
