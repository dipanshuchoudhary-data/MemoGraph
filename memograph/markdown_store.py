from __future__ import annotations

import re
from pathlib import Path


SECTION_ORDER = [
    "Summary",
    "Key Concepts",
    "Advanced Concepts",
    "Related Topics",
]

PLACEHOLDER_BULLETS = {
    "No key concepts recorded yet.",
    "No advanced concepts recorded yet.",
    "No related topics linked yet.",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def normalize_topic_title(topic: str) -> str:
    return re.sub(r"\s+", " ", topic.strip()).strip(" .")


def topic_key(topic: str) -> str:
    normalized = normalize_topic_title(topic)
    lowered = normalized.lower()

    split_markers = [" for ", " using ", " with ", " in "]
    for marker in split_markers:
        if marker in lowered:
            normalized = normalized[: lowered.index(marker)]
            lowered = normalized.lower()
            break

    tokens = re.findall(r"[a-z0-9]+", lowered)
    tokens = [token for token in tokens if token not in STOPWORDS]
    if not tokens:
        return "untitled_topic"
    return "_".join(tokens[:4])


def topic_path(knowledge_dir: Path, topic: str) -> Path:
    return knowledge_dir / f"{topic_key(topic)}.md"


def normalize_list_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = normalize_topic_title(item)
        if not normalized or normalized in PLACEHOLDER_BULLETS:
            continue
        lowered = normalized.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(normalized)
    return cleaned


def _dedupe_related_topics(items: list[str]) -> list[str]:
    deduped: list[str] = []
    by_key: dict[str, str] = {}
    for item in normalize_list_items(items):
        key = topic_key(item)
        current = by_key.get(key)
        if current is None or len(item) < len(current):
            by_key[key] = item
    seen_keys: set[str] = set()
    for item in normalize_list_items(items):
        key = topic_key(item)
        if key in seen_keys or key not in by_key:
            continue
        seen_keys.add(key)
        deduped.append(by_key[key])
    return deduped


def _dedupe_advanced_concepts(items: list[str]) -> list[str]:
    deduped: list[str] = []
    template_map: dict[str, str] = {}

    for item in normalize_list_items(items):
        template_key = item.casefold()
        for pattern in [
            r"^(tradeoff analysis for) (.+)$",
            r"^(production deployment patterns for) (.+)$",
            r"^(scalability considerations for) (.+)$",
            r"^(.+) (in production settings)$",
            r"^(advanced optimization strategies for) (.+)$",
            r"^(evaluation methods for) (.+)$",
            r"^(real-time serving constraints for) (.+)$",
        ]:
            match = re.match(pattern, item, flags=re.IGNORECASE)
            if match:
                if pattern == r"^(.+) (in production settings)$":
                    prefix = match.group(2)
                    subject = match.group(1)
                else:
                    prefix = match.group(1)
                    subject = match.group(2)
                template_key = f"{prefix.casefold()}::{topic_key(subject)}"
                break

        current = template_map.get(template_key)
        if current is None or len(item) < len(current):
            template_map[template_key] = item

    seen: set[str] = set()
    for item in normalize_list_items(items):
        template_key = item.casefold()
        for pattern in [
            r"^(tradeoff analysis for) (.+)$",
            r"^(production deployment patterns for) (.+)$",
            r"^(scalability considerations for) (.+)$",
            r"^(.+) (in production settings)$",
            r"^(advanced optimization strategies for) (.+)$",
            r"^(evaluation methods for) (.+)$",
            r"^(real-time serving constraints for) (.+)$",
        ]:
            match = re.match(pattern, item, flags=re.IGNORECASE)
            if match:
                if pattern == r"^(.+) (in production settings)$":
                    prefix = match.group(2)
                    subject = match.group(1)
                else:
                    prefix = match.group(1)
                    subject = match.group(2)
                template_key = f"{prefix.casefold()}::{topic_key(subject)}"
                break
        if template_key in seen or template_key not in template_map:
            continue
        seen.add(template_key)
        deduped.append(template_map[template_key])
    return deduped


def parse_markdown_sections(content: str) -> dict[str, list[str] | str]:
    result: dict[str, list[str] | str] = {
        "title": "",
        "Summary": "",
        "Key Concepts": [],
        "Advanced Concepts": [],
        "Related Topics": [],
    }
    current_section: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# "):
            result["title"] = normalize_topic_title(line[2:])
            current_section = None
            continue
        if line.startswith("## "):
            section_name = line[3:].strip()
            current_section = section_name if section_name in SECTION_ORDER else None
            continue
        if current_section == "Summary":
            if line:
                existing = str(result["Summary"])
                result["Summary"] = f"{existing} {line}".strip()
        elif current_section in {"Key Concepts", "Advanced Concepts", "Related Topics"}:
            if line.startswith("* "):
                item = line[2:].strip()
                link_match = re.match(r"\[(.+?)\]\([^)]+\)", item)
                if link_match:
                    item = link_match.group(1).strip()
                cast_list = list(result[current_section])
                cast_list.append(item)
                result[current_section] = cast_list

    result["Key Concepts"] = normalize_list_items(list(result["Key Concepts"]))
    result["Advanced Concepts"] = normalize_list_items(list(result["Advanced Concepts"]))
    result["Related Topics"] = _dedupe_related_topics(list(result["Related Topics"]))
    return result


def render_markdown(
    topic: str,
    summary: str,
    key_concepts: list[str],
    advanced_concepts: list[str],
    related_topics: list[str],
) -> str:
    normalized_topic = normalize_topic_title(topic)
    key_concepts = normalize_list_items(key_concepts)
    advanced_concepts = _dedupe_advanced_concepts(advanced_concepts)
    related_topics = _dedupe_related_topics(related_topics)

    lines = [
        f"# {normalized_topic}",
        "",
        "## Summary",
        "",
        summary.strip() or "No summary available yet.",
        "",
        "## Key Concepts",
        "",
    ]
    lines.extend(f"* {item}" for item in key_concepts)
    if not key_concepts:
        lines.append("* No key concepts recorded yet.")

    lines.extend(["", "## Advanced Concepts", ""])
    lines.extend(f"* {item}" for item in advanced_concepts)
    if not advanced_concepts:
        lines.append("* No advanced concepts recorded yet.")

    lines.extend(["", "## Related Topics", ""])
    lines.extend(f"* {item}" for item in related_topics)
    if not related_topics:
        lines.append("* No related topics linked yet.")

    lines.append("")
    return "\n".join(lines)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    return normalize_list_items(items)


def _canonical_title(existing_title: str, incoming_title: str) -> str:
    existing_title = normalize_topic_title(existing_title)
    incoming_title = normalize_topic_title(incoming_title)
    if not existing_title:
        return incoming_title
    if not incoming_title:
        return existing_title
    if len(incoming_title) < len(existing_title):
        return incoming_title
    return existing_title


def _clean_summary(summary: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", summary.strip())
    deduped: list[str] = []
    seen: set[str] = set()
    evolving_sentence: str | None = None
    for sentence in sentences:
        normalized = sentence.strip()
        if not normalized:
            continue
        lowered = normalized.casefold()
        if "is being accumulated as an evolving knowledge node" in lowered:
            if evolving_sentence is None or len(normalized) < len(evolving_sentence):
                evolving_sentence = normalized
            continue
        lowered = normalized.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(normalized)
    if evolving_sentence:
        deduped.insert(0, evolving_sentence)
    return " ".join(deduped)


def _merge_summary(existing_summary: str, incoming_summary: str) -> str:
    existing_summary = _clean_summary(existing_summary)
    incoming_summary = _clean_summary(incoming_summary)
    if not existing_summary:
        return incoming_summary
    if not incoming_summary:
        return existing_summary
    return existing_summary


def merge_knowledge(existing_content: str | None, topic: str, new_data: dict) -> str:
    existing = parse_markdown_sections(existing_content) if existing_content else None
    canonical_topic = _canonical_title(
        str(existing["title"]) if existing else "",
        topic,
    )

    summary = _merge_summary(
        str(existing["Summary"]) if existing else "",
        new_data["summary"].strip(),
    )
    key_concepts = dedupe_preserve_order(
        (list(existing["Key Concepts"]) if existing else []) + list(new_data["key_concepts"])
    )
    advanced_concepts = _dedupe_advanced_concepts(
        (list(existing["Advanced Concepts"]) if existing else [])
        + list(new_data["advanced_concepts"])
    )
    related_topics = _dedupe_related_topics(
        (list(existing["Related Topics"]) if existing else []) + list(new_data["related_topics"])
    )

    normalized_topic = normalize_topic_title(topic)
    related_topics = [
        item for item in related_topics if normalize_topic_title(item).casefold() != canonical_topic.casefold()
    ]

    return render_markdown(
        topic=canonical_topic,
        summary=summary,
        key_concepts=key_concepts,
        advanced_concepts=advanced_concepts,
        related_topics=related_topics,
    )


def load_topic_file(file_path: Path) -> dict[str, list[str] | str]:
    return parse_markdown_sections(file_path.read_text(encoding="utf-8"))


def list_topic_files(knowledge_dir: Path) -> list[Path]:
    if not knowledge_dir.exists():
        return []
    return sorted(
        [
            path
            for path in knowledge_dir.glob("*.md")
            if path.name.casefold() != "index.md"
        ]
    )


def build_topic_registry(knowledge_dir: Path) -> dict[str, dict[str, str]]:
    registry: dict[str, dict[str, str]] = {}
    for file_path in list_topic_files(knowledge_dir):
        parsed = load_topic_file(file_path)
        title = normalize_topic_title(str(parsed["title"]) or file_path.stem.replace("_", " "))
        key = topic_key(title or file_path.stem)
        registry[key] = {
            "title": title,
            "path": str(file_path.resolve()),
            "key": key,
        }
    return registry


def resolve_topic(topic: str, registry: dict[str, dict[str, str]]) -> tuple[str, str]:
    normalized = normalize_topic_title(topic)
    candidate_key = topic_key(normalized)
    if candidate_key in registry:
        entry = registry[candidate_key]
        return entry["title"], entry["key"]

    for entry in registry.values():
        if normalize_topic_title(entry["title"]).casefold() == normalized.casefold():
            return entry["title"], entry["key"]

    return normalized, candidate_key


def ensure_bidirectional_link(
    file_path: Path,
    this_topic: str,
    related_topic: str,
) -> None:
    this_topic = normalize_topic_title(this_topic)
    related_topic = normalize_topic_title(related_topic)

    if not file_path.exists():
        starter = render_markdown(
            topic=related_topic,
            summary=f"Knowledge node created because it is related to {this_topic}.",
            key_concepts=[],
            advanced_concepts=[],
            related_topics=[this_topic],
        )
        file_path.write_text(starter, encoding="utf-8")
        return

    existing = file_path.read_text(encoding="utf-8")
    parsed = parse_markdown_sections(existing)
    updated = render_markdown(
        topic=str(parsed["title"]) or related_topic,
        summary=str(parsed["Summary"]),
        key_concepts=list(parsed["Key Concepts"]),
        advanced_concepts=list(parsed["Advanced Concepts"]),
        related_topics=_dedupe_related_topics(list(parsed["Related Topics"]) + [this_topic]),
    )
    file_path.write_text(updated, encoding="utf-8")


def update_index(knowledge_dir: Path) -> Path:
    topic_ids = [file_path.stem for file_path in list_topic_files(knowledge_dir)]
    lines = ["# Knowledge Base", "", "## Topics", ""]
    lines.extend(f"* {topic_id}" for topic_id in topic_ids)
    if not topic_ids:
        lines.append("* No topics recorded yet.")
    lines.append("")

    index_path = knowledge_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path


def migrate_knowledge_base(knowledge_dir: Path) -> None:
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    collected: dict[str, dict[str, list[str] | str]] = {}

    for file_path in list(knowledge_dir.glob("*.md")):
        if file_path.name.casefold() == "index.md":
            continue
        parsed = parse_markdown_sections(file_path.read_text(encoding="utf-8"))
        title = normalize_topic_title(str(parsed["title"]) or file_path.stem.replace("-", " ").replace("_", " "))
        key = topic_key(title or file_path.stem)

        existing = collected.get(
            key,
            {
                "title": title,
                "Summary": "",
                "Key Concepts": [],
                "Advanced Concepts": [],
                "Related Topics": [],
            },
        )
        existing["title"] = _canonical_title(str(existing["title"]), title)
        existing["Summary"] = _merge_summary(str(existing["Summary"]), str(parsed["Summary"]))
        existing["Key Concepts"] = dedupe_preserve_order(
            list(existing["Key Concepts"]) + list(parsed["Key Concepts"])
        )
        existing["Advanced Concepts"] = _dedupe_advanced_concepts(
            list(existing["Advanced Concepts"]) + list(parsed["Advanced Concepts"])
        )
        existing["Related Topics"] = _dedupe_related_topics(
            list(existing["Related Topics"]) + list(parsed["Related Topics"])
        )
        collected[key] = existing

    for file_path in knowledge_dir.glob("*.md"):
        file_path.unlink()

    for key, parsed in collected.items():
        target_path = knowledge_dir / f"{key}.md"
        target_path.write_text(
            render_markdown(
                topic=str(parsed["title"]),
                summary=str(parsed["Summary"]),
                key_concepts=list(parsed["Key Concepts"]),
                advanced_concepts=list(parsed["Advanced Concepts"]),
                related_topics=[
                    item
                    for item in list(parsed["Related Topics"])
                    if normalize_topic_title(item).casefold()
                    != normalize_topic_title(str(parsed["title"])).casefold()
                ],
            ),
            encoding="utf-8",
        )

    update_index(knowledge_dir)
