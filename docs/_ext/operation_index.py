"""Build the operation index from the published reference sections."""

import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from docutils import nodes
from sphinx.util.docutils import SphinxDirective


_REFERENCES = ("endpoints", "education")
_ROUTE = re.compile(
    r"(GET|POST|PUT|PATCH|DELETE) "
    r"(/(?:user|tradingdata|ai)\?request_type=[a-z0-9_]+"
    r"|/backtest\?action=[a-z0-9_]+"
    r"|/education/v1(?:/[a-z0-9_{}-]+)+"
    r"|/)(?=&|$)"
)


@dataclass(frozen=True)
class Operation:
    method: str
    route: str
    title: str
    group: str
    reference: str


class OperationIndex(nodes.General, nodes.Element):
    pass


class OperationIndexDirective(SphinxDirective):
    def run(self):
        return [OperationIndex("")]


def public_operations(env):
    operations = {}
    for docname in _REFERENCES:
        for section in env.get_doctree(docname).findall(nodes.section):
            if not section["ids"]:
                continue
            parent = section.parent
            if not isinstance(parent, nodes.section) or not isinstance(parent.parent, nodes.section):
                continue
            if parent[0].astext() in {"Rate Limits", "Errors"}:
                continue
            # Match the route literals that begin a reference paragraph.
            # Additional route literals in prose are cross-references.
            for paragraph in section.children:
                if not isinstance(paragraph, nodes.paragraph) or not paragraph.children:
                    continue
                first = paragraph.children[0]
                if not isinstance(first, nodes.literal):
                    continue
                match = _ROUTE.match(first.astext())
                if not match:
                    continue
                method, route = match.groups()
                operations.setdefault(
                    (method, route),
                    Operation(
                        method, route, section[0].astext(), parent[0].astext(),
                        f"{docname}.html#{section['ids'][0]}",
                    ),
                )
    return list(operations.values())


def render_index(app, doctree, docname):
    for index in list(doctree.findall(OperationIndex)):
        grouped = defaultdict(list)
        for operation in public_operations(app.env):
            grouped[operation.group].append(operation)

        content = []
        for group, operations in grouped.items():
            content.append(nodes.rubric("", group))
            entries = nodes.bullet_list()
            for item in operations:
                route = nodes.literal("", f"{item.method} {item.route}")
                link = nodes.reference("", item.title, refuri=item.reference)
                entry = nodes.paragraph("", "", route, nodes.Text(" — "), link)
                entries += nodes.list_item("", entry)
            content.append(entries)
        index.replace_self(content)


def write_catalog(app, exception):
    if exception is not None or app.builder.format != "html":
        return
    path = Path(app.outdir, "operations.json")
    path.write_text(
        json.dumps(
            {"operations": [asdict(item) for item in public_operations(app.env)]},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def setup(app):
    app.add_node(OperationIndex)
    app.add_directive("operation-index", OperationIndexDirective)
    app.connect("doctree-resolved", render_index)
    app.connect("build-finished", write_catalog)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
