import asyncio
import json
import os
from functools import reduce
from pathlib import Path
from typing import Any, List, Union

import asyncpg
import ejs
import httpx
import nest_asyncio
import yaml
from jinja2 import Template

nest_asyncio.apply()


class OpenAIModel:
    def __init__(
        self, config_service, queries_service, tables_service, databases_service
    ):
        self.model_name = "code-davinci-002"
        self.config_service = config_service
        self.queries_service = queries_service
        self.tables_service = tables_service
        self.databases_service = databases_service
        self.api_key = self.config_service.get("OPENAI_API_KEY")
        self.openai = httpx.AsyncClient(
            base_url="https://api.openai.com/v1/engines",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        self.db_client = None

    async def open_connection(self, database_id: int):
        database = await self.databases_service.find_one(database_id)
        details = database.details
        self.db_client = await asyncpg.connect(**details)

    async def close_connection(self):
        await self.db_client.close()

    async def _call(self, query, model_name, prompt, parser):
        async with self.openai as client:
            response = await client.post(
                f"/{model_name}/completions",
                json={
                    "prompt": prompt,
                    "temperature": 0.7,
                    "max_tokens": 256,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "stop": ["---"],
                },
            )

        output = response.json()["choices"][0]["text"]
        return await parser(output)

    async def _extract_conditions_values(self, query_saved, query):
        prompt_template = ejs.render(
            open("openai.where.ejs", "r").read(), {"query": query}
        )
        parser = lambda output: json.loads(output.strip())
        try:
            values = await self._call(
                query_saved, "text-davinci-002", prompt_template, parser
            )
            return values
        except Exception as e:
            print("extractConditionsValues", e)
            raise ValueError("Could not extract values from the WHERE clause")

    async def select_tables(self, tables, query_saved, database_id, query):
        prompt_template = ejs.render(
            open("openai.select_tables.ejs", "r").read(),
            {"tables": tables, "query": query},
        )
        parser = lambda output: json.loads(output.strip())

        try:
            tables_selected = await self._call(
                query_saved, "text-davinci-002", prompt_template, parser
            )
            return list(filter(lambda table: table in tables, tables_selected))
        except Exception as err:
            print("selectTables response", tables_selected)
            raise err

    async def _find_relevant_tables(
        self, query_saved, database_id, query, schema_name, table_name
    ):
        tables = await self.tables_service.get_database_schema(database_id)

        if schema_name and table_name:
            tables = list(
                filter(
                    lambda table: table.name == table_name
                    and table.schemaName == schema_name,
                    tables,
                )
            )

        if len(tables) > 3 or sum(len(table["columns"]) for table in tables) > 30:
            tables = await self.select_tables(tables, query_saved, database_id, query)

        return tables

    async def _fetch_database_content(
        self, tables: List[Any], values: List[str]
    ) -> List[Any]:
        async def fetch_columns(table):
            for column in table.columns:
                if column.dataType not in ["text", "character varying"]:
                    return table
                closeValues = await self.dbClient.fetchClosedValues(
                    table.name, column.name, values[0]
                ).catch(lambda e: [])
                column.examples = unique_truncate(
                    column.examples + closeValues, length=50
                )

        await asyncio.gather(*[fetch_columns(table) for table in tables])
        await asyncio.sleep(0.05)
        return tables

    async def _prepare_query_examples(self, databaseId: int, query: str) -> List[Any]:
        queries = await self.queriesService.getValidatedQueriesExamplesOnDatabase(
            databaseId, query
        )

        if not queries:
            queries = [
                {"query": "return 1", "validatedSQL": "SELECT 1;"},
                {"query": "show the text 'lorem'", "validatedSQL": "SELECT 'lorem';"},
            ]

        return queries

    async def predict(self, querySaved: Any, params: dict) -> str:
        databaseId = params["databaseId"]
        query = params["query"]
        schemaName = params["schemaName"]
        tableName = params["tableName"]

        await self.open_connection(databaseId)

        tables = await self._find_relevant_tables(
            querySaved, databaseId, query, schemaName, tableName
        )

        values = await self._extract_conditions_values(querySaved, query)

        if values:
            tables = await self._fetch_database_content(tables, values)

        queries = await self._prepare_query_examples(databaseId, query)

        schemaYaml = yaml.dump(tables)

        with open(
            os.path.join(os.path.dirname(__file__), "openai.default.ejs"),
            "r",
            encoding="utf-8",
        ) as file:
            promptTemplate = file.read()

        async def parser(output):
            await self.dbClient.runQueryWithLimit1(output)
            return output

        prompt = Template(promptTemplate).render(
            schemaYaml=schemaYaml, query=query, queries=queries
        )
        modelName = params.get("model") or self.modelName
        sqlQuery = await self._call(querySaved, modelName, prompt, parser)

        await self.close_connection()

        return sqlQuery
