from sqlalchemy import Column, Integer, String

from .database import Base


# This class inherits from the "Base" we made in database.py.
# SQLAlchemy will look at this class and automatically build a database table for it.
class User(Base):
    # The actual name of the table inside the database
    __tablename__ = "users"

    # These are the columns in our spreadsheet/table
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

    # Notice we call this "hashed_password". We will mathematically scramble
    # the password before saving it here.
    hashed_password = Column(String)
