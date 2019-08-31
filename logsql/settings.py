""" General application settings """
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/logsql")
