import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv('.env')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_DB = os.getenv('PG_DB')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_DSN = f'postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'

engine = create_async_engine(PG_DSN)
Base = declarative_base()
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = 'app_users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(128))
    creation_time = Column(DateTime, server_default=func.now())
    advertisements = relationship('Advertisement', backref='user', lazy='dynamic')

    def __init__(self, name, email, password):
        super().__init__()
        self.name = name
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Advertisement(Base):
    __tablename__ = 'app_advertisements'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(String(500))
    owner = Column(String(50))
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('app_users.id'))

    def __init__(self, title, description, owner, user_id):
        super().__init__()
        self.title = title
        self.description = description
        self.owner = owner
        self.created_at = datetime.now()
        self.user_id = user_id
