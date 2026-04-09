from __future__ import annotations

from pathlib import Path

from langgraph.graph import END, START, StateGraph

from memograph.llm import build_models
from memograph.markdown_store import (
    build_topic_registry,
    ensure_bidirectional_link,
    migrate_knowledge_base,
    merge_knowledge,
    topic_path,
    topic_key,
    update_index,
    resolve_topic,
)
from memograph.state import MemoGraphState


class MemoGraphApp:
    def __init__(self, knowledge_dir: str = "knowledge") -> None:
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        migrate_knowledge_base(self.knowledge_dir)
        self.research_chain, self.summary_chain, self.model_label = build_models()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(MemoGraphState)
        builder.add_node("research", self._research_node)
        builder.add_node("summarize", self._summarize_node)
        builder.add_node("write", self._write_node)
        builder.add_node("link", self._link_node)
        builder.add_edge(START, "research")
        builder.add_edge("research", "summarize")
        builder.add_edge("summarize", "write")
        builder.add_edge("write", "link")
        builder.add_edge("link", END)
        return builder.compile()

    def _research_node(self, state: MemoGraphState) -> MemoGraphState:
        result = self.research_chain.invoke({"user_query": state["user_query"]})
        return {
            "topic_name": result.topic_name.strip(),
            "topic_key": topic_key(result.topic_name.strip()),
            "raw_research": result.raw_content.strip(),
        }

    def _summarize_node(self, state: MemoGraphState) -> MemoGraphState:
        result = self.summary_chain.invoke(
            {
                "user_query": state["user_query"],
                "topic_name": state["topic_name"],
                "raw_research": state["raw_research"],
            }
        )
        structured = {
            "summary": result.summary.strip(),
            "key_concepts": result.key_concepts,
            "advanced_concepts": result.advanced_concepts,
            "related_topics": result.related_topics,
        }
        return {
            "structured_knowledge": structured,
            "related_topics": structured["related_topics"],
        }

    def _write_node(self, state: MemoGraphState) -> MemoGraphState:
        file_path = topic_path(self.knowledge_dir, state["topic_name"])
        file_status = "updated" if file_path.exists() else "created"
        existing_content = file_path.read_text(encoding="utf-8") if file_path.exists() else None
        updated_markdown = merge_knowledge(
            existing_content=existing_content,
            topic=state["topic_name"],
            new_data=state["structured_knowledge"],
        )
        file_path.write_text(updated_markdown, encoding="utf-8")
        return {
            "topic_file_path": str(file_path.resolve()),
            "file_status": file_status,
            "topic_key": file_path.stem,
        }

    def _link_node(self, state: MemoGraphState) -> MemoGraphState:
        topic = state["topic_name"]
        registry = build_topic_registry(self.knowledge_dir)
        normalized_related: list[str] = []
        related_topic_keys: list[str] = []
        for related in state.get("related_topics", []):
            resolved_title, resolved_key = resolve_topic(related, registry)
            cleaned = resolved_title.strip()
            if not cleaned or cleaned.casefold() == topic.casefold():
                continue
            if cleaned.casefold() in {item.casefold() for item in normalized_related}:
                continue
            normalized_related.append(cleaned)
            related_topic_keys.append(resolved_key)

        for related in normalized_related:
            related_path = topic_path(self.knowledge_dir, related)
            ensure_bidirectional_link(related_path, topic, related)

        index_path = update_index(self.knowledge_dir)
        response = (
            f"Processed topic '{topic}' ({state['topic_key']}) with model '{self.model_label}'. "
            f"File {state['file_status']}: {state['topic_file_path']}. "
            f"Related topics added: {', '.join(related_topic_keys) if related_topic_keys else 'none'}."
        )
        return {
            "related_topics": normalized_related,
            "related_topic_keys": related_topic_keys,
            "index_file_path": str(index_path.resolve()),
            "final_response": response,
        }

    def run(self, user_query: str) -> MemoGraphState:
        return self.graph.invoke({"user_query": user_query})
