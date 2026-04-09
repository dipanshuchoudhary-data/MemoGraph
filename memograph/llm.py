from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from memograph.schemas import ResearchOutput, SummaryOutput


load_dotenv()


class DeterministicKnowledgeModel:
    def _advanced_insights(self, topic: str, query: str) -> list[str]:
        lowered = query.lower()
        insights = [f"Tradeoff analysis for {topic}"]

        if "production" in lowered:
            insights.insert(0, f"Production deployment patterns for {topic}")
        elif "advanced" in lowered:
            insights.insert(0, f"Advanced optimization strategies for {topic}")
        elif "evaluation" in lowered:
            insights.insert(0, f"Evaluation methods for {topic}")
        else:
            insights.insert(0, f"{topic} in production settings")

        if "scale" in lowered or "scaling" in lowered:
            insights.append(f"Scalability considerations for {topic}")
        if "real-time" in lowered or "realtime" in lowered:
            insights.append(f"Real-time serving constraints for {topic}")

        deduped: list[str] = []
        for item in insights:
            if item.casefold() not in {existing.casefold() for existing in deduped}:
                deduped.append(item)
        return deduped

    def _topic_related_topics(self, topic: str) -> list[str]:
        lowered = topic.lower()
        related: list[str] = []

        if "graph neural network" in lowered or (
            "graph" in lowered and "neural" in lowered and "network" in lowered
        ):
            related.extend(
                [
                    "Representation Learning",
                    "Node Embeddings",
                    "Graph Structure Modeling",
                ]
            )
        if "recommendation" in lowered:
            related.extend(
                [
                    "Recommendation Systems",
                    "Ranking Models",
                    "User-Item Interaction Modeling",
                ]
            )
        if "agent" in lowered:
            related.extend(
                [
                    "Task Orchestration",
                    "State Management",
                    "Tool Invocation",
                ]
            )

        words = [
            word.title()
            for word in re.findall(r"\b[A-Za-z][A-Za-z0-9\-]{4,}\b", topic)
            if word.lower() not in {"systems", "system", "advanced"}
        ]
        related.extend(words[:2])

        deduped: list[str] = []
        for item in related:
            if item.casefold() == topic.casefold():
                continue
            if item.casefold() not in {existing.casefold() for existing in deduped}:
                deduped.append(item)
        return deduped[:5]

    def _extract_topic(self, query: str) -> str:
        cleaned = query.strip().rstrip(".?!")
        lowered = cleaned.lower()
        prefixes = [
            "advanced ",
            "introduction to ",
            "overview of ",
            "deep dive into ",
        ]
        for prefix in prefixes:
            if lowered.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                lowered = cleaned.lower()

        suffix_patterns = [
            r"\s+in production(?:\s+and\s+at\s+scale)?$",
            r"\s+for beginners$",
            r"\s+explained$",
            r"\s+overview$",
        ]
        for pattern in suffix_patterns:
            updated = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
            if updated != cleaned:
                cleaned = updated
                lowered = cleaned.lower()

        if len(cleaned) <= 80:
            return cleaned.title()
        words = cleaned.split()
        return " ".join(words[:8]).title()

    def _key_phrases(self, text: str) -> list[str]:
        phrase_matches = re.findall(r"\b[A-Za-z][A-Za-z0-9\-]{3,}\b", text)
        phrases: list[str] = []
        stopwords = {
            "about",
            "their",
            "there",
            "which",
            "using",
            "build",
            "topic",
            "query",
            "systems",
            "system",
            "advanced",
            "focuses",
            "matters",
            "because",
            "important",
            "working",
            "include",
            "practice",
            "should",
            "capture",
            "definitions",
            "tradeoffs",
            "implementation",
            "patterns",
            "operational",
            "concerns",
            "production",
        }
        for item in phrase_matches:
            lowered = item.lower()
            if lowered in stopwords:
                continue
            if item.title() not in phrases:
                phrases.append(item.title())
            if len(phrases) >= 8:
                break
        return phrases

    def research_runnable(self):
        def run(inputs: dict[str, Any]) -> ResearchOutput:
            query = inputs["user_query"]
            topic = self._extract_topic(query)
            key_phrases = self._key_phrases(query)
            raw_content = (
                f"{topic} focuses on {query.strip()}. "
                f"It matters because teams need durable, reusable knowledge rather than isolated answers. "
                f"Important working ideas include {', '.join(key_phrases[:4]) or 'core concepts'}. "
                f"In practice, we should capture definitions, tradeoffs, implementation patterns, and operational concerns."
            )
            return ResearchOutput(topic_name=topic, raw_content=raw_content)

        return RunnableLambda(run)

    def summary_runnable(self):
        def run(inputs: dict[str, Any]) -> SummaryOutput:
            raw_content = inputs["raw_research"]
            topic = inputs["topic_name"]
            user_query = inputs.get("user_query", topic)
            topic_words = [
                word.title()
                for word in re.findall(r"\b[A-Za-z][A-Za-z0-9\-]{3,}\b", topic)
                if word.lower() not in {"with", "from", "into", "that", "this"}
            ]
            phrases = self._key_phrases(f"{topic} {raw_content}")
            key_concepts = (topic_words[:4] or phrases[:4] or [topic])[:4]
            advanced_concepts = self._advanced_insights(topic, user_query)
            related_topics = self._topic_related_topics(topic) or phrases[4:8]
            summary = (
                f"{topic} is being accumulated as an evolving knowledge node. "
                f"This entry now includes a concise summary, core concepts, and related topics derived from the latest query."
            )
            return SummaryOutput(
                summary=summary,
                key_concepts=key_concepts,
                advanced_concepts=advanced_concepts,
                related_topics=related_topics,
            )

        return RunnableLambda(run)


def _extract_json_object(text: str) -> str:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model response.")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ValueError("Incomplete JSON object in model response.")


def _build_resilient_structured_chain(
    llm: ChatOpenAI,
    prompt: ChatPromptTemplate,
    schema: type[BaseModel],
    prefer_json_only: bool = False,
):
    parser = PydanticOutputParser(pydantic_object=schema)

    fallback_prompt = ChatPromptTemplate.from_messages(
        [
            *prompt.messages,
            (
                "system",
                "Return valid JSON only. Do not add markdown, prose, or code fences.\n"
                "{format_instructions}",
            ),
        ]
    )

    def run(inputs: dict[str, Any]):
        if not prefer_json_only:
            try:
                strict_chain = prompt | llm.with_structured_output(schema)
                return strict_chain.invoke(inputs)
            except Exception:
                pass

        message = (fallback_prompt | llm).invoke(
            {
                **inputs,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        content = message.content if hasattr(message, "content") else str(message)
        json_blob = _extract_json_object(content)
        data = json.loads(json_blob)
        return schema.model_validate(data)

    return RunnableLambda(run)


def build_models():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        fallback = DeterministicKnowledgeModel()
        return fallback.research_runnable(), fallback.summary_runnable(), "deterministic-fallback"

    model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4.1-mini")
    base_url = os.getenv("OPENAI_BASE_URL")
    prefer_json_only = bool(base_url and "openrouter.ai" in base_url.lower())
    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=api_key,
        base_url=base_url or None,
    )

    research_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a research agent in a knowledge-building system. "
                "Produce concise but information-dense research notes for the query. "
                "Return a canonical topic name and a practical raw content draft.",
            ),
            ("human", "User query: {user_query}"),
        ]
    )
    summary_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a summarizer agent in a persistent knowledge system. "
                "Convert research notes into structured knowledge with summary, key concepts, "
                "advanced concepts, and related topics. Keep output focused on reusable knowledge.",
            ),
            (
                "human",
                "User query: {user_query}\n\nTopic: {topic_name}\n\nResearch notes:\n{raw_research}",
            ),
        ]
    )

    research_chain = _build_resilient_structured_chain(
        llm,
        research_prompt,
        ResearchOutput,
        prefer_json_only=prefer_json_only,
    )
    summary_chain = _build_resilient_structured_chain(
        llm,
        summary_prompt,
        SummaryOutput,
        prefer_json_only=prefer_json_only,
    )
    return research_chain, summary_chain, model_name
