from typing import Optional

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    notionKey: str
    openaiKey: str
    text: str
    model: str
    databaseId: Optional[str] = None
    pageId: Optional[str] = None


class GeneratePosts(BaseModel):
    notionKey: str
    openaiKey: str
    databaseId: str
    templateText: str
    numPosts: int
    model: str
    topics: str


class GetTemplates(BaseModel):
    notionKey: str
    databaseId: str
