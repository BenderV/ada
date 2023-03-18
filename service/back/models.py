from dataclasses import dataclass

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


@dataclass
class Database(Base):
    id: int
    name: str
    description: str
    engine: str
    details: dict
    organisationId: str
    ownerId: str
    public: bool

    __tablename__ = "database"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    engine = Column(String, nullable=False)
    details = Column(JSONB, nullable=False)
    organisationId = Column(String, ForeignKey("organisation.id"))
    ownerId = Column(String, ForeignKey("user.id"))
    public = Column(Boolean, nullable=False, default=False)

    organisation = relationship("Organisation")
    owner = relationship("User")


class Organisation(Base):
    __tablename__ = "organisation"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class Prediction(Base):
    __tablename__ = "prediction"

    id = Column(Integer, primary_key=True)
    queryId = Column(Integer, ForeignKey("query.id"))
    modelName = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    output = Column(String, nullable=False)
    openAIResponse = Column(JSONB)
    value = Column(JSONB)

    query = relationship("Query")


class Query(Base):
    __tablename__ = "query"

    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    databaseId = Column(Integer, ForeignKey("database.id"), nullable=False)
    validatedSQL = Column(String)
    result = Column(JSONB)
    comment = Column(String)
    creatorId = Column(String, ForeignKey("user.id"))
    createdAt = Column(TIMESTAMP, nullable=False, default=text("now()"))
    updatedAt = Column(TIMESTAMP, nullable=False, default=text("now()"))
    tag = Column(String)
    tables = Column(String)
    wheres = Column(String)

    database = relationship("Database")
    creator = relationship("User")


class Table(Base):
    __tablename__ = "table"

    description = Column(String)
    databaseId = Column(Integer, ForeignKey("database.id"), primary_key=True)
    schemaName = Column(String, primary_key=True, default="public")
    name = Column(String, primary_key=True)
    used = Column(Boolean, nullable=False, default=True)

    database = relationship("Database")


class TableColumn(Base):
    __tablename__ = "table_column"

    columnName = Column(String, primary_key=True)
    dataType = Column(String, nullable=False)
    description = Column(String)
    tableDatabaseId = Column(Integer, primary_key=True)
    tableSchemaName = Column(String, primary_key=True, default="public")
    tableName = Column(String, primary_key=True)
    isIdentity = Column(Boolean, nullable=False, default=False)
    foreignTableSchema = Column(String)
    foreignTable = Column(String)
    foreignColumn = Column(String)
    examples = Column(ARRAY(String))

    __table_args__ = (
        ForeignKeyConstraint(
            ["tableDatabaseId", "tableSchemaName", "tableName"],
            ["table.databaseId", "table.schemaName", "table.name"],
            ondelete="CASCADE",
        ),
    )


class User(Base):
    __tablename__ = "user"

    email = Column(String, nullable=False, unique=True)
    id = Column(String, primary_key=True)
    pictureUrl = Column(String)
    # organisationId = Column(String, ForeignKey("organisation.id"))
    # organisation = relationship("Organisation")


class UserOrganisation(Base):
    __tablename__ = "user_organisation"

    userId = Column(String, ForeignKey("user.id"), primary_key=True)
    organisationId = Column(String, ForeignKey("organisation.id"), primary_key=True)

    organisation = relationship("Organisation")
    user = relationship("User")


if __name__ == "__main__":
    from sqlalchemy import create_engine

    from session import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
