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