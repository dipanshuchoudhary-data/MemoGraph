from __future__ import annotations

from typing import TypedDict


class MemoGraphState(TypedDict, total=False):
    user_query: str
    topic_name: str
    raw_research: str
    structured_knowledge: dict
    topic_key: str
    topic_file_path: str
    file_status: str
    related_topics: list[str]
    related_topic_keys: list[str]
    index_file_path: str
    final_response: str
