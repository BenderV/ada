from functools import wraps

from back.datalake import DatalakeFactory
from back.models import User
from back.session import session
from flask import g, request

user = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
database = "formula1"

# TODO: remove this
organisationId = "6264fdaf-e8e2-41a8-a110-0fccc0e71277"


def user_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.organisationId = organisationId
        # Extract user information from the request
        logged_user = (
            session.query(User).filter(User.email == "admin@localhost").first()
        )
        if logged_user:
            g.user = logged_user

        # Add a datalake object to the request
        datalake = DatalakeFactory.create(
            "postgresql",
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        g.datalake = datalake

        return f(*args, **kwargs)

    return decorated_function
