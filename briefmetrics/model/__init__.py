from .meta import Session, metadata
from .objects import *


def init(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)


def create_all(engine=None):
    engine = engine or Session.bind
    metadata.create_all(bind=engine)


def drop_all(engine=None):
    engine = engine or Session.bind
    metadata.drop_all(bind=engine)
