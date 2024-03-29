from functools import wraps

from back.datalake import DatalakeFactory
from back.models import Database, User
from flask import g, jsonify, request

# TODO: remove this
# organisationId = None  # "6264fdaf-e8e2-41a8-a110-0fccc0e71277"


def user_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.organisationId = organisationId
        # Extract user information from the request
        logged_user = (
            g.session.query(User).filter(User.email == "admin@localhost").first()
        )
        if logged_user:
            g.user = logged_user
        return f(*args, **kwargs)

    return decorated_function


def database_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        database_id = request.json.get("databaseId")
        database = g.session.query(Database).filter_by(id=database_id).first()
        # Add a datalake object to the request
        datalake = DatalakeFactory.create(
            database.engine,
            **database.details,
        )
        datalake.privacy_mode = database.privacy_mode
        datalake.safe_mode = database.safe_mode
        g.datalake = datalake

        return f(*args, **kwargs)

    return decorated_function
