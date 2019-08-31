import docker
import pytest
import sqlalchemy
from sqlalchemy.pool import NullPool

from logsql import settings, models

from .logger import Logger

ENGINE = sqlalchemy.create_engine(settings.DATABASE_URL, poolclass=NullPool)
models.Session.configure(bind=ENGINE)


@pytest.fixture(scope="session", name="docker_client")
def docker_client_fixture():
    return docker.client.from_env()


@pytest.fixture(scope="session", name="python_image")
def python_image_fixture():
    return Logger.PYTHON_IMAGE


@pytest.fixture(name="logger")
def logger_fixture(docker_client, python_image):
    logger = Logger(docker_client)
    yield logger
    logger.container.kill()


@pytest.fixture(scope="function", name="session")
def session_fixture():

    if not settings.DATABASE_URL.startswith("sqlite://"):
        assert settings.DATABASE_URL.endswith("_test")

    def _drop_all():
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=ENGINE)
        meta.drop_all(bind=ENGINE)

    _drop_all()
    models.BASE.metadata.create_all(ENGINE)
    session = models.Session()
    yield session
    session.close()
