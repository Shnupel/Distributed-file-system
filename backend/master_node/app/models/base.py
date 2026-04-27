from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(
        naming_convention=settings.naming_convention,
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)