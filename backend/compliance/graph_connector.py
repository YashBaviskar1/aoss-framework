import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Default to localhost if not set, matching user's docker setup
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "admin1234")

class GraphConnector:
    driver = None

    @staticmethod
    def connect():
        if GraphConnector.driver is None:
            GraphConnector.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return GraphConnector.driver

    @staticmethod
    def run(query: str, params: dict = None):
        """
        Executes a Cypher query and returns the results as a list of dictionaries.
        """
        driver = GraphConnector.connect()
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    @staticmethod
    def close():
        if GraphConnector.driver:
            GraphConnector.driver.close()
            GraphConnector.driver = None

    @staticmethod
    def verify_connection():
        """
        Simple check to verify connectivity.
        """
        try:
            GraphConnector.run("RETURN 1 AS status")
            return True
        except Exception as e:
            print(f"Neo4j Connection Failed: {e}")
            return False
