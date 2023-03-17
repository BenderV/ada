import sqlalchemy
from sqlalchemy import text


class Database:
    def __init__(self, uri):
        self.engine = sqlalchemy.create_engine(uri)
        self.inspector = sqlalchemy.inspect(self.engine)
        self.metadata = []
        self._load_metadata()

    @property
    def name(self):
        return self.engine.url.database

    def _load_metadata(self):
        for schema in self.inspector.get_schema_names():
            if schema == "information_schema":
                continue
            for table in self.inspector.get_table_names(schema=schema):
                columns = []
                for column in self.inspector.get_columns(table, schema):
                    column_comment = column.get("comment")
                    columns.append(
                        {
                            "name": column["name"],
                            "type": column["type"],
                            "nullable": column["nullable"],
                            "comment": column_comment,
                        }
                    )

                self.metadata.append(
                    {
                        "schema": schema,
                        "table": table,
                        "is_view": False,
                        "columns": columns,
                    }
                )

            # TODO add support for views

        # Load Table objects
        self.tables = []
        for table_metadata in self.metadata:
            self.tables.append(Table(self, table_metadata))

    def query(self, query):
        with self.engine.connect() as connection:
            return [
                dict(r._mapping) for r in connection.execute(text(query)).fetchall()
            ]

    def create_transformation(self, name, query, materialized="table", schema="public"):
        if materialized == "table":
            self.engine.execute(
                text(f"CREATE MATERIALIZED VIEW {schema}.{name} AS {query}")
            )
        elif materialized == "view":
            self.engine.execute(text(f"CREATE VIEW {schema}.{name} AS {query}"))
        else:
            raise ValueError("materialized must be 'table' or 'view'")
        # Reload metadata
        self._load_metadata()


class Table:
    def __init__(self, database, metadata):
        self.database = database
        self.metadata = metadata

    @property
    def _schema(self):
        return self.metadata["schema"]

    @property
    def _table(self):
        return self.metadata["table"]

    def fetch_sample(self, n=1):
        return self.database.query(
            f"SELECT * FROM {self._schema}.{self._table} ORDER BY RANDOM() LIMIT {n}"
        )
