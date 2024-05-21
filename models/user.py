from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Boolean, Integer
from .base import Base
from uuid import uuid4

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(30))
    token: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, default=lambda: uuid4().hex)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_time: Mapped[str] = mapped_column(String(10), default=' ')
    job_id: Mapped[str] = mapped_column(String(30), default=' ')