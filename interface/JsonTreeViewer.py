import json

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Input,
    Label,
    Tree,
)


class JsonTreeViewer(Container):
    """A collapsible JSON tree viewer with search + custom list-node labels."""

    def __init__(self, data, title="JSON Viewer", label_key=None):
        super().__init__()
        self._original_data = data
        self._title = title
        self._label_key = label_key  # Key to label list items (e.g., "name")

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="section")
        yield Input(placeholder="Search JSON…", id="json_search")
        yield Tree("root", id="json_tree")

    def on_mount(self):
        tree = self.query_one("#json_tree", Tree)

        # Remove the visible "root"
        tree.show_root = False

        root = tree.root

        # Build children under the hidden root
        self._build_tree(root, self._original_data)

        root.expand()

    # ---------------------- JSON → Tree ----------------------
    def _build_tree(self, node, data):
        """Populate the tree node with JSON data."""
        if isinstance(data, dict):
            for key, value in data.items():
                label = Text(str(key), style="bold cyan")
                child = node.add(label)
                self._build_value(child, value)

        elif isinstance(data, list):
            for index, item in enumerate(data):

                # Custom list label using specified key, if present
                if (
                    isinstance(item, dict)
                    and self._label_key
                    and self._label_key in item
                ):
                    label_text = str(item[self._label_key])
                    label = Text(label_text, style="bold magenta")
                else:
                    label = Text(f"[{index}]", style="bold magenta")

                child = node.add(label)
                self._build_value(child, item)

        else:
            node.set_label(self._format_primitive(data))

    def _build_value(self, node, value):
        if isinstance(value, (dict, list)):
            self._build_tree(node, value)
        else:
            node.add(self._format_primitive(value))

    def _format_primitive(self, value) -> Text:
        if isinstance(value, str):
            return Text(f'"{value}"', style="green")
        if isinstance(value, (int, float)):
            return Text(str(value), style="magenta")
        if isinstance(value, bool):
            return Text(str(value).lower(), style="yellow")
        if value is None:
            return Text("null", style="dim")
        return Text(repr(value), style="white")

    # ---------------------- Search / Filter ----------------------
    def on_input_changed(self, event: Input.Changed):
        if event.input.id != "json_search":
            return

        query = event.value.lower().strip()
        tree = self.query_one("#json_tree", Tree)
        tree.root.children.clear()

        if not query:
            # Show full JSON
            self._build_tree(tree.root, self._original_data)
        else:
            filtered = self._filter_json(self._original_data, query)
            self._build_tree(tree.root, filtered)

        tree.root.expand_all()

    def _filter_json(self, data, query: str):
        """Return pruned JSON containing only branches that match the query."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key_match = query in str(key).lower()
                value_match = self._match_any(value, query)
                if key_match or value_match:
                    if isinstance(value, (dict, list)):
                        result[key] = self._filter_json(value, query)
                    else:
                        result[key] = value
            return result

        if isinstance(data, list):
            result_list = []
            for item in data:
                if self._match_any(item, query):
                    if isinstance(item, (dict, list)):
                        result_list.append(self._filter_json(item, query))
                    else:
                        result_list.append(item)
            return result_list

        return data

    def _match_any(self, value, query: str) -> bool:
        if isinstance(value, (dict, list)):
            text = ""
            try:
                text = json.dumps(value)
            except:
                text = str(value)
            return query in text.lower()
        return query in str(value).lower()