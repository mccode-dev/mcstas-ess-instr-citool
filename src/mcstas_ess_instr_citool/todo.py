"""The TODO file of a project, and its items.

Format (a plain text file named TODO, at the top level of the project):

* Optionally a title and other text first, in lines starting at the left
  margin (e.g. a title, a line of "=" below it, and an introduction).
* Then the items, each starting with "* " at the left margin, e.g.:

      * The parameter documentation is missing. Fill in the
        %parameters section of the header.

  The following lines of an item are indented (with spaces), and may
  contain anything, e.g. lists ("  - ..."). Blank lines are ignored.
* After the first item, every line starting at the left margin must start a
  new item, so the number of items is always clear.
"""

TODO_FILE_NAME = "TODO"
DOC_URL = ("https://mccode-dev.github.io/mcstas-ess-instr-citool/"
           "layout.html#the-todo-file")


def parse_todo(text: str, filename: str = TODO_FILE_NAME) -> list[str]:
    """The items of a TODO file (each as one string, without the leading "* "
    and with the lines joined), or a ValueError explaining the problem."""
    items: list[list[str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if line.startswith("\t"):
            raise ValueError(f"{filename}, line {lineno}: indent with spaces,"
                             " not tabs.")
        if line.startswith("* "):
            if not line[2:].strip():
                raise ValueError(f"{filename}, line {lineno}: empty item.")
            items.append([line[2:].strip()])
        elif line.startswith(" "):
            if items:
                items[-1].append(line.strip())
            # (Indented lines before the first item are part of the text
            # before the items.)
        elif items:
            raise ValueError(
                f"{filename}, line {lineno}: unexpected line after the first"
                " item. Each item must start with \"* \" at the left margin,"
                f" and its following lines must be indented (see {DOC_URL}).")
    return [" ".join(lines) for lines in items]
