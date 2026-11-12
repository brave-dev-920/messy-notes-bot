# messy-notes-bot

Paste a messy note into the terminal. An OpenAI model lists what still needs doing.

## Setup

From this folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `OPENAI_API_KEY`. `.env` stays out of Git.

To use a model other than the default (`gpt-6-astra`), set `OPENAI_MODEL` in `.env` or in the environment. A variable already set in the environment wins over `.env`.

## Run

```powershell
python main.py
```

Paste one line and press Enter.

- A blank line does not call the API.
- Pending tasks print as a checklist. A deadline appears in parentheses only when the note mentioned one.
- A note with nothing left to do prints `No pending tasks.`
- A missing API key, a failed model call, or an unusable response prints a short message.

## Examples

These show the kind of checklist to expect. The model writes the wording.

Input:

```text
fix login tmrw, email sam, and i already bought milk
```

Output:

```text
- [ ] Fix login (tomorrow)
- [ ] Email Sam
```

Input:

```text
the slides are done but i still gotta send em to maya before lunch
```

Output:

```text
- [ ] Send the slides to Maya (before lunch)
```

Input:

```text
already sent the slides and paid the bill
```

Output:

```text
No pending tasks.
```

## Files

- `main.py` reads one line and prints the checklist.
- `tasks.py` sends that note to the model and checks the task list before returning it.
