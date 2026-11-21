from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field

from riskminer.schemas.common import ORM


class KnowledgeColumn(BaseModel):
    key: str
    label: str
    type: str = "text"  # text | longtext | number | bool | list | enum | rcodes
    options: list[str] | None = None


class KnowledgeTableOut(ORM):
    sector: str
    name: str
    version: int
    title: str | None = None
    columns: list[KnowledgeColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    source_file: str | None = None
    edited_by: str | None = None
    comment: str | None = None
    updated_at: dt.datetime | None = None


class KnowledgeTableSummary(BaseModel):
    sector: str
    name: str
    title: str | None = None
    version: int
    n_rows: int
    edited_by: str | None = None
    updated_at: dt.datetime | None = None


class KnowledgeTableIn(BaseModel):
    rows: list[dict[str, Any]]
    columns: list[KnowledgeColumn] | None = None
    comment: str | None = None


class KnowledgeImportReport(BaseModel):
    sector: str
    files: list[str]
    tables: dict[str, int]  # name -> n rows
    written: list[str]


class SectorOut(BaseModel):
    code: str
    name: str
    knowledge_path: str
    active: bool
    tables: list[str] = Field(default_factory=list)
