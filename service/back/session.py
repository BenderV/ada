from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/datamarket"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
