from textual.widgets import Markdown


class HomeView(Markdown):
    def __init__(self):
        with open("views/home.md", "r", encoding="utf-8") as f:
            markdown_text = f.read()

        super().__init__(markdown_text)
