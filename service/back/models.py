import json
from dataclasses import dataclass

from autochat import Message as AutoChatMessage, Image as AutoChatImage
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    LargeBinary,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def format_to_camel_case(**kwargs):
    # change lower_case keys to camelCase keys
    def camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    kwargs = {camel_case(k): v for k, v in kwargs.items()}
    return kwargs


def format_to_snake_case(**kwargs):
    # change camelCase keys to lower_case keys
    def snake_case(name):
        name = name[0].lower() + name[1:]
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip(
            "_"
        )

    kwargs = {snake_case(k): v for k, v in kwargs.items()}
    return kwargs


class DefaultBase:
    createdAt = Column(DateTime, nullable=False, server_default=func.now())
    updatedAt = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


@dataclass
class Database(DefaultBase, Base):
    id: int
    name: str
    description: str
    engine: str
    details: dict
    organisationId: str
    ownerId: str
    public: bool
    safe_mode: bool
    privacy_mode: bool
    dbt_catalog: dict
    dbt_manifest: dict

    __tablename__ = "database"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    _engine = Column(String, nullable=False, name="engine")
    details = Column(JSONB, nullable=False)
    organisationId = Column(String, ForeignKey("organisation.id"))
    ownerId = Column(String, ForeignKey("user.id"))
    public = Column(Boolean, nullable=False, default=False)
    # Information save by the ai
    memory = Column(String)
    tables_metadata = Column(JSONB)
    dbt_catalog = Column(JSONB)
    dbt_manifest = Column(JSONB)

    organisation = relationship("Organisation")
    owner = relationship("User")

    safe_mode = Column(Boolean, nullable=False, default=True, server_default="true")
    privacy_mode = Column(Boolean, nullable=False, default=True, server_default="true")

    # Hotfix for engine, "postgres" should be "postgresql"
    @property
    def engine(self):
        return self._engine  # .replace("postgres", "postgresql")


class Organisation(DefaultBase, Base):
    __tablename__ = "organisation"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


@dataclass
class ConversationMessage(DefaultBase, Base):
    __tablename__ = "conversation_message"

    id: int
    conversationId: int
    name: str
    role: str
    content: str
    data: dict
    functionCall: dict
    queryId: int
    functionCallId: str
    isAnswer: bool

    id = Column(Integer, primary_key=True)
    conversationId = Column(Integer, ForeignKey("conversation.id"), nullable=False)
    role = Column(String, nullable=False)
    name = Column(String)
    content = Column(String, nullable=True)
    functionCall = Column(JSONB)
    data = Column(JSONB)
    queryId = Column(Integer, ForeignKey("query.id"), nullable=True)
    reqId = Column(String, nullable=True)
    functionCallId = Column(String, nullable=True)
    image = Column(LargeBinary, nullable=True)
    isAnswer = Column(Boolean, nullable=False, default=False)

    conversation = relationship("Conversation", back_populates="messages")

    # format params before creating the object
    def __init__(self, **kwargs):
        kwargs = format_to_camel_case(**kwargs)
        super().__init__(**kwargs)

    def to_dict(self):
        # Export to dict, only keys declared in the dataclass
        message = {
            "id": self.id,
            "conversationId": self.conversationId,
            "role": self.role,
            "name": self.name,
            "content": self.content,
            "functionCall": self.functionCall,
            "data": self.data,
            # "createdAt": self.createdAt,
            # "updatedAt": self.updatedAt,
            "queryId": self.queryId,
            "functionCallId": self.functionCallId,
            "isAnswer": self.isAnswer,
        }
        if self.functionCall and self.functionCall.get("name") == "PLOT_WIDGET":
            message["dataSource"] = self.data
            message["visualisationParams"] = self.data
        return message

    def to_autochat_message(self) -> AutoChatMessage:
        message = AutoChatMessage(
            role=self.role,
            name=self.name,
            content=self.content,
            function_call=self.functionCall,
            function_call_id=self.functionCallId,
            # data (only for function call output)
        )
        if self.image:
            message.image = AutoChatImage.from_bytes(self.image)
        if self.isAnswer:
            message.content = "<ANSWER>" + message.content
        return message

    @classmethod
    def from_autochat_message(cls, message: AutoChatMessage):
        kwargs = format_to_camel_case(**message.__dict__)
        # rewrite id to reqId
        kwargs["reqId"] = kwargs.pop("id", None)
        # transfrom image from PIL to binary
        if message.image:
            kwargs["image"] = message.image.to_bytes()
        # isAnswer: parse message.content depends on <ANSWER> tag
        if message.content and message.content.startswith("<ANSWER>"):
            kwargs["isAnswer"] = True
            kwargs["content"] = message.content.split("<ANSWER>", 1)[1]
        return ConversationMessage(**kwargs)


@dataclass
class Conversation(DefaultBase, Base):
    __tablename__ = "conversation"

    id: int
    name: str
    ownerId: str
    databaseId: int
    projectId: int
    createdAt: str
    updatedAt: str
    # messages: List[ConversationMessage] = field(default_factory=list)

    id = Column(Integer, primary_key=True)
    name = Column(String)
    ownerId = Column(String, ForeignKey("user.id"))
    projectId = Column(Integer, ForeignKey("project.id"))
    databaseId = Column(Integer, ForeignKey("database.id"), nullable=False)

    owner = relationship("User")
    database = relationship("Database")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="joined",
        # Order by id
        order_by="ConversationMessage.id",
    )
    project = relationship("Project")


class Query(DefaultBase, Base):
    __tablename__ = "query"

    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=True)
    databaseId = Column(Integer, ForeignKey("database.id"), nullable=False)
    sql = Column(String)
    result = Column(JSONB)
    comment = Column(String)
    creatorId = Column(String, ForeignKey("user.id"))
    tag = Column(String)
    tables = Column(String)
    wheres = Column(String)
    embedding = Column(Vector(1536))

    database = relationship("Database")
    creator = relationship("User")

    visualisationParams = Column(JSONB)


class User(DefaultBase, Base):
    __tablename__ = "user"

    email = Column(String, nullable=False, unique=True)
    id = Column(String, primary_key=True)
    pictureUrl = Column(String)
    # organisationId = Column(String, ForeignKey("organisation.id"))
    # organisation = relationship("Organisation")


class UserOrganisation(DefaultBase, Base):
    __tablename__ = "user_organisation"

    userId = Column(String, ForeignKey("user.id"), primary_key=True)
    organisationId = Column(String, ForeignKey("organisation.id"), primary_key=True)

    organisation = relationship("Organisation")
    user = relationship("User")


@dataclass
class ProjectTables(DefaultBase, Base):
    __tablename__ = "project_tables"

    databaseName: str
    schemaName: str
    tableName: str

    id = Column(Integer, primary_key=True)
    projectId = Column(Integer, ForeignKey("project.id"), nullable=False)
    databaseName = Column(String)
    schemaName = Column(String)
    tableName = Column(String)

    project = relationship("Project", back_populates="tables")


@dataclass
class Project(DefaultBase, Base):
    __tablename__ = "project"

    id: int
    name: str
    description: str
    creatorId: str  # warning, it's a string
    organisationId: str
    databaseId: int  # temporary
    # TODO: change
    # tables: [ProjectTables]
    # tables: List[ConversationMessage] = field(default_factory=list)

    id = Column(Integer, primary_key=True)  # TODO: transform to uuid
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    creatorId = Column(String, ForeignKey("user.id"), nullable=False)
    organisationId = Column(String, ForeignKey("organisation.id"))
    databaseId = Column(Integer, ForeignKey("database.id"), nullable=False)

    creator = relationship("User")
    organisation = relationship("Organisation")
    tables = relationship(
        "ProjectTables",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="joined",
        # Order by id
        # order_by="ProjectTable.id",
    )
    conversations = relationship("Conversation", back_populates="project")
    notes = relationship("Note", back_populates="project")


@dataclass
class Note(DefaultBase, Base):
    __tablename__ = "note"

    id: int
    title: str
    content: str
    projectId: int

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    projectId = Column(Integer, ForeignKey("project.id"))

    project = relationship("Project", back_populates="notes")


if __name__ == "__main__":
    from session import DATABASE_URL
    from sqlalchemy import create_engine

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
