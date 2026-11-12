"""Ask an OpenAI model for the pending tasks in a messy note."""

import os
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

DEFAULT_MODEL = "gpt-6-astra"
ENV_PATH = Path(__file__).with_name(".env")

INSTRUCTIONS = """You turn one messy note into a list of pending tasks.

Include only actions the writer still needs to do.
Leave out anything the note says is already finished.
Write each title as a short, clear action. Capitalize names and the first word.
Put a deadline only when the note itself mentions one, and keep the writer's timing
(clean up obvious shorthand such as tmrw to tomorrow).
If the note does not mention a deadline, use null. Do not invent dates or times.
Keep the deadline in the deadline field, not in the title.
When nothing is still pending, return an empty list.
"""


class ConfigError(Exception):
    """The bot is missing something it needs, such as an API key."""


class ExtractionError(Exception):
    """The model call failed, or its response could not be used."""


@dataclass(frozen=True)
class Task:
    title: str
    deadline: str | None = None


class TaskDraft(BaseModel):
    title: str = Field(
        description="Short pending action. Do not include the deadline in the title."
    )
    deadline: str | None = Field(
        description="Deadline mentioned in the note, or null when the note gives no deadline."
    )


class TaskListResponse(BaseModel):
    tasks: list[TaskDraft]


def extract_tasks(note: str) -> list[Task]:
    """Return pending tasks for a note. A blank note does not call the API."""
    if not note or not note.strip():
        return []

    client = OpenAI(api_key=_api_key(), timeout=60)
    try:
        response = client.responses.parse(
            model=_model_name(),
            instructions=INSTRUCTIONS,
            input=note,
            text_format=TaskListResponse,
        )
    except ValidationError as error:
        raise ExtractionError(
            "The model response did not match the task list format. Try the note again."
        ) from error
    except OpenAIError as error:
        raise ExtractionError(_call_failed_message()) from error

    return _validate_response(response.output_parsed)


def _load_local_env() -> None:
    """Fill unset settings from a gitignored .env file, if one is present."""
    if not ENV_PATH.is_file():
        return
    try:
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ConfigError("Could not read .env. Check the file and try again.") from error

    for line in lines:
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        name, value = parsed
        if name not in {"OPENAI_API_KEY", "OPENAI_MODEL"} or os.environ.get(name):
            continue
        os.environ[name] = value


def _parse_env_line(line: str) -> tuple[str, str] | None:
    text = line.strip()
    if not text or text.startswith("#") or "=" not in text:
        return None
    if text.startswith("export "):
        text = text[len("export ") :].strip()
    name, value = text.split("=", 1)
    name = name.strip()
    value = value.strip().strip('"').strip("'")
    if not name:
        return None
    return name, value


def _api_key() -> str:
    _load_local_env()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "Missing OPENAI_API_KEY. Add it to your environment or a .env file, then run the bot again."
        )
    return key


def _model_name() -> str:
    _load_local_env()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    return model or DEFAULT_MODEL


def _call_failed_message() -> str:
    return (
        "The model call failed. Check OPENAI_API_KEY, OPENAI_MODEL, and your connection, "
        "then try again."
    )


def _validate_response(parsed: object) -> list[Task]:
    if isinstance(parsed, dict):
        try:
            parsed = TaskListResponse.model_validate(parsed)
        except ValidationError as error:
            raise ExtractionError(
                "The model response did not match the task list format. Try the note again."
            ) from error

    if not isinstance(parsed, TaskListResponse):
        raise ExtractionError(
            "The model did not return a task list. Try the note again."
        )

    tasks: list[Task] = []
    for index, item in enumerate(parsed.tasks, start=1):
        if not isinstance(item, TaskDraft) or not isinstance(item.title, str):
            raise ExtractionError(f"Task {index} from the model was not usable.")
        title = item.title.strip()
        if not title:
            raise ExtractionError(f"Task {index} from the model had an empty title.")
        tasks.append(Task(title=title, deadline=_clean_deadline(item.deadline, index)))
    return tasks


def _clean_deadline(value: object, index: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ExtractionError(f"Task {index} from the model had a deadline that is not text.")
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"null", "none", "n/a"}:
        return None
    return cleaned
