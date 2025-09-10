from typing import TypedDict

class BaseConfig(TypedDict):
    """Base configuration for all clients"""
    server_url: str
    server_port: int
    software_statement: str
