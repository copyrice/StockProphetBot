from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import BigInteger, String, Column, ForeignKey
from .base import Base
from uuid import uuid4
from .user import User
import sqlalchemy as sa


class Portfolio(Base):
    __tablename__ = 'portfolio'

    id: int = Column(
        BigInteger, ForeignKey("users.id"), primary_key=True, index=True, unique=True
    )
    user: Mapped["User"] = relationship("User")
    serialized_portfolio: Mapped[str] = mapped_column(String(10000))
    
