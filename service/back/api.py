from back.datalake import DatalakeFactory
from back.models import (
    Conversation,
    ConversationMessage,
    Database,
    Project,
    ProjectTables,
)
from flask import Blueprint, g, jsonify, request
from middleware import user_middleware
from sqlalchemy import and_, or_

api = Blueprint("back_api", __name__)

import dataclasses
import json
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
        g.session.query(Conversation)
        .filter(
            Conversation.ownerId == g.user.id,
        )
        .all()
    )
    return jsonify(conversations)


@api.route("/conversations/<int:conversation_id>", methods=["GET", "PUT"])
@user_middleware
def get_conversation(conversation_id):
    conversation = (
        g.session.query(Conversation)
        .join(ConversationMessage, Conversation.messages, isouter=True)
        .filter(Conversation.id == conversation_id)
        .one()
    )

    if request.method == "PUT":
        # Update conversation name
        conversation.name = request.json["name"]
        g.session.commit()

    # TODO: redesign this to use a single query
    conversation_dict = dataclass_to_dict(conversation)
    conversation_dict["messages"] = dataclass_to_dict(conversation.messages)
    conversation_dict["messages"].sort(key=lambda x: x["id"])
    return jsonify(conversation_dict)


@api.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@user_middleware
def delete_conversation(conversation_id):
    # Delete conversation and all related messages
    g.session.query(ConversationMessage).filter_by(
        conversationId=conversation_id
    ).delete()
    g.session.query(Conversation).filter_by(id=conversation_id).delete()
    g.session.commit()
    return jsonify({"success": True})


@api.route("/databases", methods=["POST"])
@user_middleware
def create_database():
    # Instaniate a new datalake object
    datalake = DatalakeFactory.create(
        request.json["engine"],
        **request.json["details"],
    )
    # Test connection
    datalake.test_connection()

    # Create a new database
    database = Database(
        name=request.json["name"],
        description=request.json["description"],
        _engine=request.json["engine"],
        details=request.json["details"],
        # organisationId=request.json["organisationId"],
        ownerId=g.user.id,
        privacy_mode=request.json["privacy_mode"],
        safe_mode=request.json["safe_mode"],
        dbt_catalog=request.json["dbt_catalog"],
        dbt_manifest=request.json["dbt_manifest"],
    )

    database.tables_metadata = datalake.load_metadata()

    g.session.add(database)
    g.session.commit()
    return jsonify(database)


@api.route("/databases/<int:database_id>", methods=["DELETE"])
@user_middleware
def delete_database(database_id):
    # Delete database
    g.session.query(Database).filter_by(id=database_id).delete()
    g.session.commit()
    return jsonify({"success": True})


@api.route("/databases/<int:database_id>", methods=["PUT"])
@user_middleware
def update_database(database_id):
    # Update database
    database = g.session.query(Database).filter_by(id=database_id).first()
    database.name = request.json["name"]
    database.description = request.json["description"]

    # If the engine info has changed, we need to check the connection
    datalake = DatalakeFactory.create(
        request.json["engine"],
        **request.json["details"],
    )
    if (
        database.engine != request.json["engine"]
        or database.details != request.json["details"]
        or database.name != request.json["name"]
    ):
        try:
            datalake.test_connection()
        except Exception as e:
            return jsonify({"message": str(e.args[0])}), 400

    database.tables_metadata = datalake.load_metadata()
    database._engine = request.json["engine"]
    database.details = request.json["details"]
    database.privacy_mode = request.json["privacy_mode"]
    database.safe_mode = request.json["safe_mode"]
    database.dbt_catalog = request.json["dbt_catalog"]
    database.dbt_manifest = request.json["dbt_manifest"]

    g.session.commit()
    return jsonify(database)


@api.route("/databases", methods=["GET"])
@user_middleware
def get_databases():
    user = getattr(g, "user", None)
    # organisationId = g.organisationId
    # Filter databases based on ownerId (userId) OR organisationId
    databases = (
        g.session.query(Database).filter(Database.ownerId == user.id)
        # .filter(
        #     or_(
        #
        #         Database.organisationId == organisationId
        #     )
        # )
        .all()
    )
    return jsonify(databases)


@api.route("/databases/<int:database_id>/questions", methods=["GET"])
@user_middleware
def get_questions(database_id):
    database = g.session.query(Database).filter_by(id=database_id).first()

    from autochat import ChatGPT

    chat_gpt = ChatGPT()
    # if exist ; add database.memory, dbt.catalog, dbt.manifest
    chat_gpt.context = json.dumps(database.tables_metadata)

    def questions(question1: str, question2: str, question3: str):
        pass

    chat_gpt.add_function(questions)
    message = chat_gpt.ask(
        "Generate 3 questions that the user can ask based on the context (database schema, past conversations, etc)"
    )
    response_dict = message.function_call["arguments"]
    response_values = list(response_dict.values())
    return jsonify(response_values)


@api.route("/databases/<int:database_id>/schema", methods=["GET"])
def get_schema(database_id):
    # Filter databases based on user ID and specific database ID
    database = g.session.query(Database).filter_by(id=database_id).first()

    if not database:
        return jsonify({"error": "Database not found"}), 404

    return jsonify(database.tables_metadata)


# Get all projects of the user or it's organisation
@api.route("/projects", methods=["GET"])
@user_middleware
def get_projects():
    projects = (
        g.session.query(Project)
        .filter(
            or_(
                Project.creatorId == g.user.id,
                # Project.organisationId == g.organisationId,
            )
        )
        .all()
    )

    return jsonify(projects)


# Get specific project
@api.route("/projects/<int:project_id>", methods=["GET"])
@user_middleware
def get_project(project_id):
    project = (
        g.session.query(Project)
        # .join(ProjectTables, Project.tables, isouter=True)
        .filter_by(id=project_id).first()
    )

    # # Verify user access
    if (
        project.creatorId
        != g.user.id
        # and project.organisationId != g.user.organisationId
    ):
        return jsonify({"error": "Access denied"}), 403

    project_dict = dataclass_to_dict(project)
    project_dict["tables"] = dataclass_to_dict(project.tables)
    return jsonify(project_dict)


# Create, update, delete projects
@api.route("/projects", methods=["POST"])
@user_middleware
def create_project():
    data = request.get_json()
    required_fields = ["name", "description"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_project = Project(**{field: data[field] for field in required_fields})
    new_project.creatorId = g.user.id

    # Handle creation of ProjectTables
    if "tables" in data:
        new_project.tables = [
            ProjectTables(
                databaseName=table.get("databaseName"),
                schemaName=table.get("schemaName"),
                tableName=table.get("tableName"),
            )
            for table in data["tables"]
        ]

    g.session.add(new_project)
    g.session.commit()
    return jsonify(new_project)


@api.route("/projects/<int:project_id>", methods=["PUT"])
@user_middleware
def update_project(project_id):
    data = request.get_json()
    project = g.session.query(Project).filter_by(id=project_id).first()
    # update name, description or tables
    project.name = data.get("name")
    project.description = data.get("description")
    project.tables = [
        ProjectTables(
            projectId=project_id,
            databaseName=table.get("databaseName"),
            schemaName=table.get("schemaName"),
            tableName=table.get("tableName"),
        )
        for table in data.get("tables", [])
    ]
    g.session.commit()
    return "ok"


@api.route("/projects/<int:project_id>", methods=["DELETE"])
@user_middleware
def delete_project(project_id):
    project = g.session.query(Project).filter_by(id=project_id).first()
    g.session.delete(project)
    g.session.commit()
    return jsonify({"message": "Project deleted successfully"})
