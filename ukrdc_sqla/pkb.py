"""Modules which relate to the Repository System Tables"""
from typing import Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped

from .ukrdc import Base


class PKBLink(Base):
    __tablename__ = "pkb_links"

    id :Mapped[int]= Column(Integer, primary_key=True)
    link:Mapped[Optional[str]] = Column(String)
    link_name:Mapped[Optional[str]] = Column(String)
    coding_standard:Mapped[Optional[str]] = Column(String)
    code:Mapped[Optional[str]] = Column(String)
