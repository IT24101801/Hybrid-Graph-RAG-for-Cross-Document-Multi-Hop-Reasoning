from __future__ import annotations

import os
from neo4j import GraphDatabase


class Neo4jClient:
    def __init__(self) -> None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not password:
            raise ValueError("NEO4J_PASSWORD is not configured.")

        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database

    def close(self) -> None:
        self.driver.close()

    def execute_write(self, query: str, **params):
        with self.driver.session(database=self.database) as session:
            return session.execute_write(lambda tx: list(tx.run(query, **params)))

    def execute_read(self, query: str, **params):
        with self.driver.session(database=self.database) as session:
            return session.execute_read(lambda tx: [r.data() for r in tx.run(query, **params)])
