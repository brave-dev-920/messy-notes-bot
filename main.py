"""Paste a messy note and print a clean to-do checklist."""

import sys

from tasks import ConfigError, ExtractionError, Task, extract_tasks


def main() -> int:
    note = input("Paste a messy note: ")
    if not note.strip():
        print("That note is empty. Paste a line when you have one.")
        return 0

    try:
        tasks = extract_tasks(note)
    except (ConfigError, ExtractionError) as error:
        print(error)
        return 1

    if not tasks:
        print("No pending tasks.")
        return 0

    for task in tasks:
        print(_format_task(task))
    return 0


def _format_task(task: Task) -> str:
    if task.deadline:
        return f"- [ ] {task.title} ({task.deadline})"
    return f"- [ ] {task.title}"


if __name__ == "__main__":
    sys.exit(main())
