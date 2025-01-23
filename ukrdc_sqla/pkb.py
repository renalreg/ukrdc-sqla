"""Modules which relate to the Repository System Tables"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from .ukrdc import Base


class PKBLink(Base):
    __tablename__ = "pkb_links"

    id = mapped_column(Integer, primary_key=True)
    link = mapped_column(String)
    link_name = mapped_column(String)
    coding_standard = mapped_column(String)
    code = mapped_column(String)
