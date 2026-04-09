from __future__ import annotations

import argparse
from pathlib import Path

from memograph.graph import MemoGraphApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MemoGraph knowledge-building CLI")
    parser.add_argument("query", help="User query or topic to process")
    parser.add_argument(
        "--knowledge-dir",
        default="knowledge",
        help="Directory containing Markdown knowledge files",
    )
    parser.add_argument(
        "--show-markdown",
        action="store_true",
        help="Print the updated Markdown content after execution",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = MemoGraphApp(knowledge_dir=args.knowledge_dir)
    result = app.run(args.query)

    print(result["final_response"])
    print(f"Topic file created or updated: {result['topic_file_path']}")

    if args.show_markdown:
        path = Path(result["topic_file_path"])
        print()
        print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
