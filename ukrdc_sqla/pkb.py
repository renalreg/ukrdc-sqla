"""Modules which relate to the Repository System Tables"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .ukrdc import Base


class PKBLink(Base):
    __tablename__ = "pkb_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link: Mapped[str | None] = mapped_column(String)
    link_name: Mapped[str | None] = mapped_column(String)
    coding_standard: Mapped[str | None] = mapped_column(String)
    code: Mapped[str | None] = mapped_column(String)
