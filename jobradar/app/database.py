from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Render free-tier PostgreSQL drops idle connections after ~5 minutes.
# pool_pre_ping: test each connection before use (detects dropped connections).
# pool_recycle: proactively replace connections older than 4 min.
# pool_size / max_overflow: cap concurrent connections (Render free = 25 max).
# connect_args keepalives: send TCP keepalive probes so Render doesn't silently
#   close the socket while a query is in flight.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=240,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
        "connect_timeout": 10,
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
