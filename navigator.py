from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Static
from textual.containers import Vertical, ScrollableContainer
from textual import events
import inspect
import io
import sys
import git_connector
import check_coverages
import pull_requests
import pyperclip  # <-- Added for clipboard functionality

SECTIONS = {
    "GitHub": [
        ("Team repos", git_connector.get_team_repositories),
        ("Team slugs", git_connector.get_team_slugs),
        ("Repository branches", git_connector.get_repository_branches),
        ("Pull requests", pull_requests.list_open_pull_requests_team),
    ],
    "Scala": [
        ("Recursive coverage percentages", check_coverages.execute)
    ]
}


class NavigatorApp(App):
    CSS_PATH = None

    def __init__(self):
        super().__init__()
        self.view_state = "sections"
        self.current_section = None
        self.selected_script = None
        self.script_function = None
        self.arg_index = 0
        self.arg_prompts = []
        self.collected_args = []
        self.branch_list = []
        self.selected_branch = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            self.list_view = ListView()
            yield self.list_view

            self.input_widget = Input(
                placeholder="Enter arguments and press Enter..."
            )
            yield self.input_widget

            self.output_scroll = ScrollableContainer()
            yield self.output_scroll

        yield Footer()

    async def on_mount(self) -> None:
        self.output_widget = Static(id="output-display")
        await self.output_scroll.mount(self.output_widget)
        self.load_sections()

    def load_sections(self):
        self.view_state = "sections"
        self.current_section = None
        self.selected_script = None
        self.script_function = None
        self.input_widget.visible = False
        self.output_scroll.visible = False
        self.output_widget.update("")
        self.list_view.clear()
        for section in SECTIONS.keys():
            self.list_view.append(ListItem(Label(section)))
        self.set_focus(self.list_view)

    def load_scripts(self, section_name):
        self.view_state = "scripts"
        self.current_section = section_name
        self.selected_script = None
        self.script_function = None
        self.input_widget.visible = False
        self.output_scroll.visible = False
        self.output_widget.update("")
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🔙 Back")))
        for name, _ in SECTIONS[section_name]:
            self.list_view.append(ListItem(Label(name)))
        self.set_focus(self.list_view)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_label = str(event.item.query_one(Label).renderable)

        if self.view_state == "sections":
            self.load_scripts(selected_label)

        elif self.view_state == "scripts":
            if selected_label == "🔙 Back":
                self.load_sections()
                return

            for name, func in SECTIONS[self.current_section]:
                if name == selected_label:
                    self.selected_script = name
                    self.script_function = func
                    self.view_state = "args"
                    self.arg_prompts = list(inspect.signature(func).parameters.items())
                    self.collected_args = []
                    self.arg_index = 0

                    self.input_widget.visible = True
                    self.output_scroll.visible = False
                    self.prompt_next_argument()
                    break

        elif self.view_state == "branch_actions":
            if selected_label == "🔙 Back":
                self.view_state = "scripts"
                self.load_scripts(self.current_section)
                return

            branch_index = self.list_view.index(event.item) - 1
            self.selected_branch = self.branch_list[branch_index]
            self.view_state = "branch_action_menu"
            self.show_branch_action_menu()

        elif self.view_state == "branch_action_menu":
            if selected_label == "🔙 Back":
                self.view_state = "branch_actions"
                self.show_branch_list()
                return

            if selected_label == "Copy Branch Name":
                pyperclip.copy(self.selected_branch['name'])
                self.output_widget.update(
                    f"[green]📋 Branch '{self.selected_branch['name']}' copied to clipboard.[/green]"
                )
            elif selected_label == "Show Latest Commit":
                commit_date = self.selected_branch['latest_commit']
                self.output_widget.update(
                    f"[blue]Latest commit for branch '{self.selected_branch['name']}':[/blue] {commit_date}"
                )

            self.output_scroll.visible = True
            self.set_focus(self.list_view)

    def prompt_next_argument(self):
        if self.arg_index < len(self.arg_prompts):
            name, param = self.arg_prompts[self.arg_index]
            if param.default != inspect.Parameter.empty:
                self.input_widget.placeholder = f"Enter value for: {name} (optional, press Enter for default)"
            else:
                self.input_widget.placeholder = f"Enter value for: {name}"
            self.input_widget.value = ""
            self.set_focus(self.input_widget)
        else:
            self.run_collected_arguments()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if self.view_state == "args" and self.script_function:
            raw = message.value.strip()
            name, param = self.arg_prompts[self.arg_index]

            try:
                if not raw:
                    if param.default != inspect.Parameter.empty:
                        casted = param.default
                    else:
                        casted = None
                else:
                    if param.annotation != inspect.Parameter.empty:
                        casted = param.annotation(raw)
                    else:
                        casted = raw

                self.collected_args.append(casted)
                self.arg_index += 1
                self.prompt_next_argument()

            except Exception as e:
                self.input_widget.placeholder = f"❌ Invalid input for {name}: {e}. Try again."
                self.input_widget.value = ""

    async def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "escape"):
            if self.view_state == "scripts":
                self.load_sections()
            elif self.view_state == "args":
                self.load_scripts(self.current_section)
            elif self.view_state == "branch_actions":
                self.view_state = "scripts"
                self.load_scripts(self.current_section)
            elif self.view_state == "branch_action_menu":
                self.view_state = "branch_actions"
                self.show_branch_list()
        elif event.key == "c":
            if self.output_scroll.visible:
                text_to_copy = self.output_widget.renderable
                if text_to_copy:
                    pyperclip.copy(str(text_to_copy))
                    self.output_widget.update(
                        f"{text_to_copy}\n\n[yellow]📋 Output copied to clipboard.[/yellow]"
                    )

    def run_collected_arguments(self):
        try:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            result = self.script_function(*self.collected_args)
            printed_output = buffer.getvalue()

            sys.stdout = old_stdout

            if isinstance(result, list) and all(isinstance(item, dict) and 'name' in item for item in result):
                self.view_state = "branch_actions"
                self.branch_list = result
                self.show_branch_list()
                return

            if isinstance(result, list):
                result_output = "\n".join(map(str, result)) if result else "(Empty list)"
            else:
                result_output = str(result)

            display_text = ""
            if printed_output.strip():
                display_text += f"[blue]Printed Output:[/blue]\n{printed_output.strip()}\n\n"
            display_text += f"[green]✅ Function '{self.script_function.__name__}' executed.[/green]\n\nResult:\n{result_output}"
            display_text += "\n\n[yellow]Press 'c' to copy this output to clipboard.[/yellow]"

            self.output_widget.update(display_text)
            self.output_scroll.visible = True
            self.view_state = "scripts"

        except Exception as e:
            sys.stdout = old_stdout
            display_text = f"[red]❌ Error calling function:[/red]\n{e}"
            self.output_widget.update(display_text)
            self.output_scroll.visible = True
            self.view_state = "scripts"

        self.input_widget.visible = False
        self.input_widget.value = ""
        self.set_focus(self.list_view)

    def show_branch_list(self):
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🔙 Back")))
        for branch in self.branch_list:
            label = f"{branch['name']} (⏱ {branch['latest_commit']})"
            self.list_view.append(ListItem(Label(label)))
        self.output_scroll.visible = False
        self.set_focus(self.list_view)

    def show_branch_action_menu(self):
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🔙 Back")))
        actions = ["Copy Branch Name", "Show Latest Commit"]
        for action in actions:
            self.list_view.append(ListItem(Label(action)))


if __name__ == "__main__":
    NavigatorApp().run()
