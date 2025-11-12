from pathlib import Path

cmdlen = 48

title = "\n ".join([
    ".------..------..------..------.".center(cmdlen, " "),
    "|S.--. ||C.--. ||C.--. ||K.--. |".center(cmdlen, " "),
    "| :♥ : || :♦ : || :♣ : || :♠ : |".center(cmdlen, " "),
    "| :  : || :  : || :  : || :  : |".center(cmdlen, " "),
    "| '--'S|| '--'C|| '--'C|| '--'K|".center(cmdlen, " "),
    "`------'`------'`------'`------'".center(cmdlen, " "),
    "CLI Tool on Super Computer".center(cmdlen, " "),
    "Author: Chon-Hei Lo".center(cmdlen, " ")
])

config_path = Path.home() / ".sccli-kit"

TITLE = ".------..------..------..------.\n" \
        "|S.--. ||C.--. ||C.--. ||K.--. |\n" \
        "| :♥ : || :♣ : || :♦ : || :♠ : |\n" \
        "| :  : || :  : || :  : || :  : |\n" \
        "| '--'S|| '--'C|| '--'C|| '--'K|\n" \
        "`------'`------'`------'`------'\n" \
        "CLI Tool on Super Computer\n" \
        "Author: Chon-Hei Lo"

STYLE = {
    "title-block": "",
    "title-info": "#aaaaaa",
    "title-info.selected": "bold #ffffff",
    'title-prompt': 'bold',
    "title-menu-item": "fg:#8a8a8a",
    "sec-menu-item": "fg:#8a8a8a",
    "sec-menu-item.onfocus": "fg:#ffffff",
    "sec-menu-item.selected": "bold fg:#00afff",
    "sec.prompt.valid": "bold fg:#00afff",
    "sec.prompt.invalid": "bold fg:red",
    "sec.prompt.active": "bold fg:white",
    "sec.prompt.empty": "fg:#8a8a8a",
    "frame.border": "#bbbbbb",
    "frame.label": "#ffffff",
}

MAX_WIDTH = 60
PROMPT = "╰┈➤ "
