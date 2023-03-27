from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Database, Table, TableColumn
from back.session import session
from flask import Blueprint, g, jsonify, request
from middleware import database_middleware, user_middleware
from sqlalchemy import or_

api = Blueprint("back_api", __name__)

import dataclasses
from datetime import datetime
from typing import List, Union


def dataclass_to_dict(obj: Union[object, List[object]]) -> Union[dict, List[dict]]:
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]

    if dataclasses.is_dataclass(obj):
        data = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat()
            elif dataclasses.is_dataclass(value) or isinstance(value, list):
                data[field.name] = dataclass_to_dict(value)
            else:
                data[field.name] = value
        return data

    return obj


@api.route("/conversations", methods=["GET"])
@user_middleware
def get_conversations():
    # Filter conversations based on ownerId (userId) OR organisationId
    conversations = (
        session.query(Conversation)
        .filter(
            Conversation.ownerId == g.user.id,
        )
        .all()
    )
    return jsonify(conversations)


@api.route("/conversations/<int:conversation_id>", methods=["GET"])
@user_middleware
def get_conversation(conversation_id):
    conversation = (
        session.query(Conversation)
        .join(ConversationMessage, Conversation.messages, isouter=True)
        .filter(Conversation.id == conversation_id)
        .one()
    )

    # TODO: redesign this to use a single query
    conversation_dict = dataclass_to_dict(conversation)
    conversation_dict["messages"] = dataclass_to_dict(conversation.messages)
    conversation_dict["messages"].sort(key=lambda x: x["id"])
    return jsonify(conversation_dict)


@api.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@user_middleware
def delete_conversation(conversation_id):
    # Delete conversation and all related messages
    session.query(ConversationMessage).filter_by(
        conversationId=conversation_id
    ).delete()
    session.query(Conversation).filter_by(id=conversation_id).delete()
    session.commit()
    return jsonify({"success": True})


@api.route("/databases", methods=["POST"])
@user_middleware
def create_database():
    # Create a new database
    database = Database(
        name=request.json["name"],
        description=request.json["description"],
        _engine=request.json["engine"],
        details=request.json["details"],
        # organisationId=request.json["organisationId"],
        ownerId=g.user.id,
    )

    session.add(database)
    session.commit()
    return jsonify(database)


@api.route("/databases", methods=["GET"])
@user_middleware
def get_databases():
    user = getattr(g, "user", None)
    organisationId = g.organisationId
    # Filter databases based on ownerId (userId) OR organisationId
    databases = (
        session.query(Database)
        .filter(
            or_(Database.ownerId == user.id, Database.organisationId == organisationId)
        )
        .all()
    )
    return jsonify(databases)


@api.route("/databases/<int:database_id>/schema", methods=["GET"])
def get_schema(database_id):
    # Get the user ID from request headers or other means (e.g. JWT)
    user_id = request.headers.get("user_id")

    # Filter databases based on user ID and specific database ID
    database = session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    # Query the Table and TableColumn models to get the schema data
    tables = session.query(Table).filter_by(databaseId=database_id).all()
    columns = session.query(TableColumn).filter_by(tableDatabaseId=database_id).all()

    # Convert the result into the desired JSON format
    result = []
    for table in tables:
        schema_data = {
            "schemaName": table.schemaName,
            "name": table.name,
            "columns": [],
        }

        for column in columns:
            if (
                column.tableName == table.name
                and column.tableSchemaName == table.schemaName
            ):
                schema_data["columns"].append(
                    {
                        "name": column.columnName,
                        "dataType": column.dataType,
                        "isIdentity": column.isIdentity,
                        "examples": column.examples,
                    }
                )

        result.append(schema_data)

    return jsonify(result)
