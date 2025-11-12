from typing import Any, Callable, NamedTuple, Literal, Optional

class Section(NamedTuple):
    name: str
    kind: Literal["text", "menu"] = "menu"
    layout: Literal["H", "V"] = "H"
    checker: Optional[Callable[[Any], bool]] = None
    options: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None
    help_builder: Optional[Callable] = None
    
def next_section_option(sec: Section, current: str, step: int) -> str:
    if sec.options is not None:
        if current in sec.options:
            return sec.options[(sec.options.index(current) + step) % len(sec.options)]
        return sec.options[0]
    return current
