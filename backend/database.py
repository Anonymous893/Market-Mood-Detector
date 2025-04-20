from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .db_models import Base

def init_db(db_uri):
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    return engine

@contextmanager
def session_scope(engine):
    """Provide a transactional scope around a series of operations."""
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()