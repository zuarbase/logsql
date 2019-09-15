""" Database model(s) """

import datetime

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


BASE = declarative_base()
Session = sessionmaker()


class Log(BASE):
    """ An instance representing one line of a log file """
    __tablename__ = "logs"

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )

    container_id = sqlalchemy.Column(
        sqlalchemy.String(64),
        nullable=False,
    )

    container_name = sqlalchemy.Column(
        sqlalchemy.String(128),
        nullable=False
    )

    json = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )

    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )

    def as_dict(self):
        """ Convert this Log instance to a dictionary. """
        return {
            "id": self.id,
            "container_id": self.container_id,
            "container_name": self.container_name,
            "json": self.json,
            "created_at": self.created_at.isoformat()
        }
