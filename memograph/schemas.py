from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchOutput(BaseModel):
    topic_name: str = Field(description="Concise canonical topic name for the query.")
    raw_content: str = Field(description="Research notes with practical and conceptual detail.")


class SummaryOutput(BaseModel):
    summary: str = Field(description="A compact summary of the topic.")
    key_concepts: list[str] = Field(description="Important foundational concepts.")
    advanced_concepts: list[str] = Field(description="Advanced concepts when relevant.")
    related_topics: list[str] = Field(description="Other topics that should be linked.")
