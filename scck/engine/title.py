from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, VSplit, Window, WindowAlign, FormattedTextControl, Layout, Dimension
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Box, Frame
from prompt_toolkit.formatted_text import FormattedText

from scck.const import TITLE, MAX_WIDTH, PROMPT, STYLE


def get_selection_controller(options: list[tuple[int | str, str, ...]], state: dict, column=2):
    control_blocks = []
    for c in range(column):
        c_options = options[c::column]
        c_texts = [
            f"{key:2d}) {hint}{'\n' if i < len(c_options) - 1 else ''}" for i, (key, hint, *_) in enumerate(c_options)]
        c_idx = {key: i for i, (key, hint, *_) in enumerate(c_options)}

        def make_variable_control(c_texts, c_idx: dict):
            def block():
                return [("class:title-info.selected" if c_idx.get(state["select"], None) == i else "class:title-info", text) for i, text in enumerate(c_texts)]
            return block

        control_blocks.append(Window(FormattedTextControl(
            make_variable_control(c_texts, c_idx)), ignore_content_width=True))

    return control_blocks


def run_title_prompt(options: dict):
    state = {"select": None}

    containers = [Box(Window(FormattedTextControl(TITLE),
                             width=Dimension(preferred=MAX_WIDTH),
                             align=WindowAlign.CENTER,
                             dont_extend_width=True,
                             style="class:title-block"),
                      padding_top=1,
                      padding_left=0)]

    for title, fn_list in options.items():
        if fn_list is None or len(fn_list) == 0:
            continue
        list_items = get_selection_controller(fn_list, state)
        frame = Frame(Box(VSplit(list_items, padding=1),
                          padding_left=1,
                          padding_right=1),
                      title=title,
                      width=Dimension(max=MAX_WIDTH),
                      style="class:title-frame")

        left_frame = VSplit([frame, Window(width=Dimension(min=0))])
        containers.append(left_frame)

    prompt_char = FormattedText([("class:title-prompt", PROMPT)])

    input_field = TextArea(
        multiline=False, prompt=prompt_char)

    containers.append(input_field)

    def on_text_changed(_):
        text = input_field.text.strip().lower()
        if text.isdigit():
            select = int(text)
        else:
            select = text
        if select != state["select"]:
            state["select"] = select
            app.invalidate()

    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        exit()

    @kb.add("enter", eager=True)
    def _(event):
        event.app.exit(result=input_field.text)

    app = Application(layout=Layout(VSplit([Box(HSplit(containers, padding=1),
                                                padding_left=1,
                                                padding_right=1)])),
                      full_screen=False,
                      key_bindings=kb,
                      style=Style.from_dict(STYLE))

    input_field.buffer.on_text_changed += on_text_changed
    return app.run()


if __name__ == "__main__":
    FNS = {
        "BASIC": [
            (1, "Hello World", lambda: print("Hello, World!")),
            (2, "Job Generator", lambda: print("Job Generator")),
        ],
        "INFO": [
            (90, "Generate User Information", lambda: run_gen_user_info()),
            (91, "Slurm jobs statistics", lambda: run_slurm_table_generator()),
            (92, "Directory statistics", lambda: run_dirstat()),
        ],
        "CUSTOM": [
            # (100, "Custom", lambda: print("Custom")),
        ]
    }
    reply = run_title_prompt(FNS)
    
    def get_fn():
        for key, value in FNS.items():
            for idx, name, fn in value:
                if str(idx) == reply:
                    return fn
        return None
    
    fn = get_fn()
    if fn is not None:
        fn()

    exit(0)