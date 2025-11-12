import re

from prompt_toolkit.application import Application
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window, VSplit, FormattedTextControl, Dimension
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Frame, Box

from scck.const import MAX_WIDTH, PROMPT, STYLE
from scck.engine.config import Section, next_section_option


class SectionAutoSuggest(AutoSuggest):
    def __init__(self, sections: list[Section], status: dict):
        self.sections = sections
        self.status = status

    def get_suggestion(self, buffer, document):
        cmd_list, cur_idx, cmd_idx = self.status["cursor-info"]
        cur_idx: int
        if not 0 <= cur_idx < len(self.sections):
            return None

        sec = self.sections[cur_idx]

        if sec.suggestions is None:
            return None

        if cmd_idx == 0:
            return Suggestion(sec.suggestions[0])

        elif len(sec.suggestions) > 1:
            cur_cmd = cmd_list[cur_idx]
            for opt in sec.suggestions:
                if opt.startswith(cur_cmd) and opt != cur_cmd:
                    return Suggestion(opt[len(cur_cmd):])


def parse_command(cmd: str, cursor_pos: int):
    cmd_list = cmd.lstrip().split()
    if cursor_pos == len(cmd) and cmd.endswith(" "):
        return cmd_list + [""], len(cmd_list), 0
    elif cmd_list == []:
        return [""], 0, 0
    elif cursor_pos == 0:
        return cmd_list, -1 if cmd[0] == " " else 0, 0
    elif cmd[cursor_pos-1:cursor_pos+1] == "  ":
        return cmd_list, -1, 0
    else:
        bef_cmd = cmd[:cursor_pos]
        bef_cmd_list = bef_cmd.split()
        if bef_cmd.endswith(" "):
            return cmd_list, len(bef_cmd_list), 0
        cur_idx = len(bef_cmd_list) - 1
        cur_cmd_pos = len(bef_cmd) - bef_cmd.rfind(bef_cmd_list[-1])
        return cmd_list, cur_idx, cur_cmd_pos


def build_param_intro(sections: list[Section], status):
    names = [section.name for section in sections]
    checkers = [section.checker for section in sections]
    texts = [("", "Parameters Input:\n")] + \
        [("class:sec-prompt-empty", f"<{section.name}> ") for section in sections]

    def fn_text():
        cmd_list, cur_idx, cur_cmd_pos = status["cursor-info"]
        # cur_cmd = cmd_list[cur_idx] if cur_idx != -1 else ""

        for i, name in enumerate(names):
            if cur_idx == i:
                texts[i+1] = ("class:sec.prompt.active", f"<{name}> ")
            elif i >= len(cmd_list):  # not filled
                texts[i+1] = ("class:sec.prompt.empty", f"<{name}> ")
            elif checkers[i] is None:
                texts[i+1] = ("class:sec.prompt.valid", f"<{name}> ")
            elif status['cmd-history'][i] == name and texts[i+1][0] != "class:sec.prompt.active":
                continue
            else:
                status['cmd-history'][i] = cmd_list[i]
                if checkers[i](cmd_list[i]):
                    texts[i+1] = ("class:sec.prompt.valid", f"<{name}> ")
                else:
                    texts[i+1] = ("class:sec.prompt.invalid", f"<{name}> ")
        return texts
    return fn_text


def build_param_info(sections: list[Section], status: dict):
    items = []
    for section in sections:
        if section.kind == "text":
            pass
        elif section.layout == "V":
            items.append(
                [f"  {opt}{'\n' if i < len(section.options) - 1 else ''}" for i, opt in enumerate(section.options)])
        else:
            items.append([f" {opt} " for opt in section.options])

    def fn_text():
        cmd_list, cur_idx, _ = status["cursor-info"]
        if cur_idx == -1 or cur_idx >= len(sections):
            return []
        cur_cmd = cmd_list[cur_idx]

        if sections[cur_idx].kind == "menu":
            texts = [
                ("", f"Available options: {'\n' if sections[cur_idx].layout == 'V' else ''}")]
            for i, opt in enumerate(sections[cur_idx].options):
                if opt == cur_cmd:
                    texts.append(
                        ("class:sec-menu-item.selected", items[cur_idx][i]))
                else:
                    texts.append(
                        ("class:sec-menu-item.onfocus" if status["value-on-focus"] else "class:sec-menu-item", items[cur_idx][i]))
            return texts
        else:
            texts = [("", "Default option: "), ("class:sec-menu-item", sections[cur_idx].suggestions[0])]
            return texts
        
    return fn_text


def accept_suggestion_and_advance(buf: Buffer, sections: list[Section], status: dict) -> bool:
    cmd_list, cur_idx, cmd_idx = status["cursor-info"]
    sugg = getattr(buf, "suggestion", None)

    if cur_idx == -1 or not (sugg and sugg.text):
        return False

    if cur_idx > len(cmd_list) - 1 or \
            cmd_list[cur_idx] != "" and \
            cmd_list[cur_idx] + sugg.text not in sections[cur_idx].options:
        return False

    buf.insert_text(sugg.text, overwrite=False)
    return True


def run_section_prompt(title: str, sections: list[Section]):
    status = {"cursor-info": ([""], 0, 0),
              "cmd-history": ["" for _ in sections],
              "value-on-focus": 0}

    input_field = TextArea(multiline=False,
                           prompt=PROMPT,
                           style="class:sec-prompt",
                           auto_suggest=SectionAutoSuggest(sections, status))

    param_intro = Window(FormattedTextControl(build_param_intro(
        sections, status)), dont_extend_height=True)
    param_info = Window(FormattedTextControl(build_param_info(
        sections, status)), dont_extend_height=True)

    param_block = HSplit([param_intro, param_info], padding=1)

    param_frame = Frame(Box(param_block,
                            padding_top=0,
                            padding_bottom=0,
                            padding_left=1,
                            padding_right=1),
                        title=title,
                        width=Dimension(max=MAX_WIDTH),
                        )

    left_frame = VSplit([param_frame, Window(width=Dimension(min=0))])

    controller = HSplit([left_frame, input_field], padding=1)

    kb = KeyBindings()

    @kb.add("enter", eager=True)
    def _(event):
        event.app.exit(result=input_field.text)

    @kb.add("tab", eager=True)
    def _(event):
        buf = input_field.buffer
        if not status["value-on-focus"]:
            if not accept_suggestion_and_advance(buf, sections, status):
                status["value-on-focus"] = True
            return

        cmd_list, cur_idx, cmd_idx = status["cursor-info"]
        cur_cmd = cmd_list[cur_idx]
        if not 0 <= cur_idx < len(sections):
            return

        section = sections[cur_idx]

        if section and section.kind == "menu" and cur_cmd in section.options:
            txt = buf.text
            new_v = next_section_option(section, cur_cmd, +1)
            if cur_idx + 1 < len(cmd_list):
                find_txt = txt[: buf.cursor_position]
                cur_cmd_idx = find_txt.rfind(cur_cmd[:cmd_idx])
            else:
                cur_cmd_idx = txt.rfind(cur_cmd)
            new_s = txt[:cur_cmd_idx] + new_v + \
                txt[cur_cmd_idx + len(cur_cmd):]
            buf.text = new_s
            buf.cursor_position = cur_cmd_idx + len(new_v)
            status["value-on-focus"] = True

    @kb.add("s-tab", eager=True)
    def _(event):
        buf = input_field.buffer
        if not status["value-on-focus"]:
            status["value-on-focus"] = True
            return

        cmd_list, cur_idx, cmd_idx = status["cursor-info"]
        cur_cmd = cmd_list[cur_idx]
        if not 0 <= cur_idx < len(sections):
            return

        section = sections[cur_idx]

        if section and section.kind == "menu" and cur_cmd in section.options:
            new_v = next_section_option(section, cur_cmd, -1)
            cur_cmd_idx = buf.text[:buf.cursor_position].rfind(cur_cmd)
            new_s = buf.text[:cur_cmd_idx] + new_v + \
                buf.text[cur_cmd_idx + len(cur_cmd):]
            buf.text = new_s
            buf.cursor_position = cur_cmd_idx + len(new_v)
            status["value-on-focus"] = True

    @kb.add("right", eager=True)
    def _(event):
        buf = input_field.buffer
        if accept_suggestion_and_advance(buf, sections, status):
            return
        if buf.cursor_position < len(buf.text):
            buf.cursor_right(count=1)

    @kb.add("c-c")
    def _(event):
        event.app.exit(result="")

    app = Application(layout=Layout(controller), full_screen=False,
                      key_bindings=kb, style=Style.from_dict(STYLE), cursor=CursorShape.BEAM)

    def on_text_changed(_):
        buf = input_field.buffer
        status["cursor-info"] = parse_command(buf.text, buf.cursor_position)
        status["value-on-focus"] = False
        app.invalidate()

    def on_cursor_position_changed(_):
        buf = input_field.buffer
        status["cursor-info"] = parse_command(buf.text, buf.cursor_position)
        status["value-on-focus"] = False
        app.invalidate()

    input_field.buffer.on_text_changed += on_text_changed
    input_field.buffer.on_cursor_position_changed += on_cursor_position_changed

    return app.run()


if __name__ == "__main__":
    schema = [
        Section("user", "menu", "V",
                  checker=lambda s: s in ["alice", "bob", "carol"],
                  options=["alice", "bob", "carol"],
                  suggestions=["alice", "bob", "carol"],
                  help_builder=lambda v: [("", "Job user (str)\n")]
                  ),
        Section("nodes", "menu",
                  checker=lambda s: s in ["1", "2", "3", "4"],
                  options=["1", "2", "3", "4"],
                  suggestions=["1", "2", "3", "4"],
                  help_builder=lambda v: [("", "Task nodes (1 <= int <= 4)\n")]),
        Section("cores", "text",
                  checker=lambda s: s.isdigit(),
                  suggestions=["32"],
                  help_builder=lambda v: [("", "Cores per node (1 <= int <= 32)\n")]),
        Section("time-limit", "text",
                  checker=lambda s: bool(
                      re.match(r"^\d+-\d{2}-\d{2}-\d{2}$", s)),
                  suggestions=["0-01-00-00"],
                  help_builder=lambda v: [("", "Task time limit (d-HH-MM-SS)\n")]),
    ]

    result = run_section_prompt("Job", schema)
