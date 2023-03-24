import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/datamarket"

from datetime import date, datetime


def json_serial(d):
    def _default(obj):
        """JSON serializer, supports datetime and date objects"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    return json.dumps(d, default=_default)


def json_deserial(d):
    def date_hook(json_dict):
        for (key, value) in json_dict.items():
            try:
                json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except:
                pass
        return json_dict

    return json.loads(d, object_hook=date_hook)


engine = create_engine(
    DATABASE_URL, json_serializer=json_serial, json_deserializer=json_deserial
)
Session = sessionmaker(bind=engine)
session = Session()
