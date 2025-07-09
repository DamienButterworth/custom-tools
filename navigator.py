import importlib

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Static
from textual.containers import Vertical, ScrollableContainer
from textual import events
import inspect
import io
import sys
import pyperclip
import config
import asyncio
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text


class NavigatorApp(App):
    CSS_PATH = "themes/styles.css"

    def __init__(self):
        super().__init__()
        self.output_widget = None
        self.output_scroll = None
        self.input_widget = Input(placeholder="Enter arguments and press Enter...")
        self.list_view = None
        self.view_state = "sections"
        self.current_section = None
        self.selected_script = None
        self.script_function = None
        self.arg_index = 0
        self.arg_prompts = []
        self.collected_args = []
        self.branch_list = []
        self.selected_branch = None
        self.settings = config.load_settings()
        self.setting_being_edited = None

        config.SECTIONS["Settings"] = [(f"{k.capitalize().replace('_', ' ')}: {v}", lambda key=k: key) for k, v in self.settings.items()]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            self.list_view = ListView()
            yield self.list_view

            yield self.input_widget

            self.output_scroll = ScrollableContainer()
            yield self.output_scroll

        yield Footer()

    async def on_mount(self) -> None:
        self.output_widget = Static(id="output-display")
        await self.output_scroll.mount(self.output_widget)
        await self.input_widget.remove()
        self.load_sections()

    def load_sections(self):
        self.view_state = "sections"
        self.current_section = None
        self.selected_script = None
        self.script_function = None
        if self.input_widget.parent:
            self.call_from_thread(self.input_widget.remove)
        self.output_scroll.visible = False
        self.output_widget.update("")
        self.list_view.clear()
        for section in config.SECTIONS.keys():
            self.list_view.append(ListItem(Label(section)))
        self.set_focus(self.list_view)

    def load_scripts(self, section_name):
        self.view_state = "scripts"
        self.current_section = section_name
        self.selected_script = None
        self.script_function = None
        if self.input_widget.parent:
            self.call_from_thread(self.input_widget.remove)
        self.output_scroll.visible = False
        self.output_widget.update("")
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🖙 Back")))
        for name, _ in config.SECTIONS[section_name]:
            self.list_view.append(ListItem(Label(name)))
        self.set_focus(self.list_view)

    def reload_all(self, section_name=None, highlight_item=None):
        importlib.reload(config)  # 🔄 Reload the config module completely

        self.settings = config.load_settings()
        config.SECTIONS["Settings"] = [
            (f"{k.capitalize().replace('_', ' ')}: {v}", lambda key=k: key)
            for k, v in self.settings.items()
        ]

        self.load_sections()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_label = str(event.item.query_one(Label).renderable)

        if self.view_state == "sections":
            self.load_scripts(selected_label)

        elif self.view_state == "scripts":
            if selected_label == "🖙 Back":
                self.load_sections()
                return

            for name, func in config.SECTIONS[self.current_section]:
                if name == selected_label:
                    self.selected_script = name
                    self.script_function = func
                    self.view_state = "args"

                    if self.current_section == "Settings":
                        self.setting_being_edited = func()
                        if not self.input_widget.parent:
                            await self.mount(self.input_widget, after=self.list_view)
                        self.output_scroll.visible = False
                        current_value = self.settings.get(self.setting_being_edited, "")
                        self.input_widget.placeholder = f"Enter new value for {self.setting_being_edited} (current: {current_value})"
                        self.input_widget.value = ""
                        self.set_focus(self.input_widget)
                    else:
                        self.arg_prompts = list(inspect.signature(func).parameters.items())
                        self.collected_args = []
                        self.arg_index = 0
                        if not self.input_widget.parent:
                            await self.mount(self.input_widget, after=self.list_view)
                        self.output_scroll.visible = False
                        await self.prompt_next_argument()
                    break

        elif self.view_state == "branch_actions":
            if selected_label == "🖙 Back":
                self.view_state = "scripts"
                self.load_scripts(self.current_section)
                return

            branch_index = self.list_view.index(event.item) - 1
            self.selected_branch = self.branch_list[branch_index]
            self.view_state = "branch_action_menu"
            self.show_branch_action_menu()

        elif self.view_state == "branch_action_menu":
            if selected_label == "🖙 Back":
                self.view_state = "branch_actions"
                self.show_branch_list()
                return

            if selected_label == "Copy Branch Name":
                pyperclip.copy(self.selected_branch['name'])
                self.output_widget.update(
                    f"[green]📋 Branch '{self.selected_branch['name']}' copied to clipboard.[/green]")
            elif selected_label == "Show Latest Commit":
                commit_date = self.selected_branch['latest_commit']
                self.output_widget.update(
                    f"[blue]Latest commit for branch '{self.selected_branch['name']}':[/blue] {commit_date}")

            self.output_scroll.visible = True
            self.set_focus(self.list_view)

    async def prompt_next_argument(self):
        while self.arg_index < len(self.arg_prompts):
            name, param = self.arg_prompts[self.arg_index]
            setting_key = f"default_{name.lower()}"

            if setting_key in self.settings and self.settings[setting_key]:
                value = self.settings[setting_key]
                if param.annotation != inspect.Parameter.empty:
                    try:
                        value = param.annotation(value)
                    except Exception:
                        pass
                self.collected_args.append(value)
                self.arg_index += 1
                continue

            if not self.input_widget.parent:
                await self.mount(self.input_widget, after=self.list_view)

            if param.default != inspect.Parameter.empty:
                self.input_widget.placeholder = f"Enter value for: {name} (optional, press Enter for default)"
            else:
                self.input_widget.placeholder = f"Enter value for: {name}"
            self.input_widget.value = ""
            self.set_focus(self.input_widget)
            return

        await self.run_collected_arguments()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if self.view_state == "args" and self.current_section == "Settings" and self.setting_being_edited:
            new_value = message.value.strip()
            self.settings[self.setting_being_edited] = new_value
            config.save_settings(self)

            self.output_widget.update(
                f"""[green]✅ Setting '{self.setting_being_edited}' updated to:[/green] {new_value}
[yellow]Settings updated. Reloaded view.[/yellow]""")
            self.output_scroll.visible = True
            if self.input_widget.parent:
                await self.input_widget.remove()

            highlight_label = f"{self.setting_being_edited.capitalize().replace('_', ' ')}: {new_value}"
            self.setting_being_edited = None
            self.view_state = "scripts"
            self.reload_all(section_name="Settings", highlight_item=highlight_label)
            return

        if self.view_state == "args" and self.script_function:
            raw = message.value.strip()
            name, param = self.arg_prompts[self.arg_index]

            try:
                if not raw:
                    casted = param.default if param.default != inspect.Parameter.empty else None
                else:
                    casted = param.annotation(raw) if param.annotation != inspect.Parameter.empty else raw

                self.collected_args.append(casted)
                self.arg_index += 1
                await self.prompt_next_argument()

            except Exception as e:
                self.input_widget.placeholder = f"❌ Invalid input for {name}: {e}. Try again."
                self.input_widget.value = ""

    async def run_collected_arguments(self):
        global old_stdout
        if self.input_widget.parent:
            await self.input_widget.remove()
        self.output_scroll.visible = True
        self.output_widget.update(Spinner("dots", text="Running function..."))
        self.set_focus(self.output_widget)
        await asyncio.sleep(0.1)

        try:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            result = await asyncio.to_thread(self.script_function, *self.collected_args)
            printed_output = buffer.getvalue()

            sys.stdout = old_stdout

            if isinstance(result, list) and all(isinstance(item, dict) for item in result):
                if not result:
                    self.output_widget.update("(Empty list)")
                else:
                    table = Table(show_header=True, header_style="bold magenta")
                    keys = result[0].keys()
                    for key in keys:
                        table.add_column(str(key), overflow="fold", no_wrap=False)
                    for item in result:
                        table.add_row(*(str(item.get(k, "")) for k in keys))
                    self.output_widget.update(table)
            else:
                result_output = str(result)
                display_text = ""
                if printed_output.strip():
                    display_text += f"[blue]Printed Output:[/blue]\n{printed_output.strip()}\n\n"
                display_text += f"[green]✅ Function '{self.script_function.__name__}' executed.[/green]\n\nResult:\n{result_output}"
                display_text += "\n\n[yellow]Press 'c' to copy this output to clipboard.[/yellow]"
                self.output_widget.update(display_text)

        except Exception as e:
            sys.stdout = old_stdout
            self.output_widget.update(f"[red]❌ Error calling function:[/red]\n{e}")

        self.view_state = "scripts"
        self.set_focus(self.list_view)

    def show_branch_list(self):
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🖙 Back")))
        for branch in self.branch_list:
            label = f"{branch['name']} (⏱ {branch['latest_commit']})"
            self.list_view.append(ListItem(Label(label)))
        self.output_scroll.visible = False
        self.set_focus(self.list_view)

    def show_branch_action_menu(self):
        self.list_view.clear()
        self.list_view.append(ListItem(Label("🖙 Back")))
        actions = ["Copy Branch Name", "Show Latest Commit"]
        for action in actions:
            self.list_view.append(ListItem(Label(action)))

    async def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "escape"):
            if self.input_widget.parent:
                await self.input_widget.remove()

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


if __name__ == "__main__":
    NavigatorApp().run()
