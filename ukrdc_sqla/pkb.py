"""Modules which relate to the Repository System Tables"""

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

from .ukrdc import Base


class PKBLink(Base):
    __tablename__ = "pkb_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link: Mapped[Optional[str]] = mapped_column(String)
    link_name: Mapped[Optional[str]] = mapped_column(String)
    coding_standard: Mapped[Optional[str]] = mapped_column(String)
    code: Mapped[Optional[str]] = mapped_column(String)
