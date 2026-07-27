from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.duplicate_ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])


def parse_document(path):
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def main():
    build_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "_build/html")
    documents = {}
    failures = []

    for path in build_dir.glob("*.html"):
        documents[path.name] = parse_document(path)

    for name, document in documents.items():
        if document.duplicate_ids:
            failures.append(
                f"{name}: duplicate anchors {sorted(document.duplicate_ids)}"
            )
        for href in document.links:
            target = urlsplit(href)
            if target.scheme or target.netloc:
                continue
            target_name = unquote(target.path) or name
            if target_name.endswith("/"):
                target_name += "index.html"
            if not target_name.endswith(".html"):
                continue
            target_document = documents.get(Path(target_name).name)
            if target_document is None:
                failures.append(f"{name}: missing document {href}")
                continue
            fragment = unquote(target.fragment)
            if fragment and fragment not in target_document.ids:
                failures.append(f"{name}: missing anchor {href}")

    if failures:
        raise SystemExit("\n".join(failures))

    print(
        f"Validated {len(documents)} rendered documents and all local anchors."
    )


if __name__ == "__main__":
    main()
