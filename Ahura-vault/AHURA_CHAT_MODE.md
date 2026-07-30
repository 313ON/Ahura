```
# Ahura — Chat Mode (REPL) for Windows + WSL

**Owner:** Nima  
**Status:** Draft  
**Last updated:** 2026-07-30  
**Scope:** Ahura CLI (Windows + WSL)  
**Goals:** Persistent interactive chat, consistent behavior across OS, strong logging, safe context handling, minimal dependencies.

---

## 1) Problem Statement

We currently have an Ahura CLI that can:
- Send single prompts to OpenRouter models with resilience/fallback
- Analyze a file via `-f <path>`
- Log to `~/.ahura/logs/`
- Provide `--doctor`

We now want **Chat Mode** (an interactive REPL) that works:
- In **WSL** (bash/zsh)
- In **Windows** terminals (PowerShell, Windows Terminal, CMD)
…with consistent UX, stable session persistence, and safety constraints (token limits, redaction, crash recovery).

---

## 2) Design Principles

1. **Single codebase, multi-platform**  
   The same logic must run in Windows + WSL. Avoid shell-only hacks.

2. **Minimal moving parts**  
   Chat Mode must not depend on heavy frameworks. Prefer Python stdlib.

3. **Observability first**  
   Every user turn and assistant turn is logged with timestamps + model + latency.

4. **Safety constraints**  
   - Token budgeting and truncation strategy
   - Secrets redaction (API keys, tokens)
   - File size limits and explicit user consent for big files

5. **Replaceability / no vendor lock-in**  
   The inference layer stays behind a clean interface (OpenRouter today, can swap tomorrow).

---

## 3) User Experience (UX)

### 3.1 Entry

- `ahura "one-shot prompt"`
- `ahura -f <file> "analyze this"`
- `ahura --chat` or `ahura chat` → enters interactive mode

### 3.2 Chat Mode Commands

Inside REPL, commands start with `/`:

- `/exit` — exit session
- `/reset` — clear conversation context in memory
- `/save` — persist session to disk immediately
- `/load <session_id>` — load a previous session
- `/model` — show current model and fallback list
- `/model set <model>` — pin a model (disable fallback unless explicitly allowed)
- `/models` — list fallback models
- `/system <text>` — set/override system instruction for the session
- `/file <path>` — attach a file (summary extraction + optional full ingest if safe)
- `/doctor` — run connectivity + env checks
- `/help` — show commands

### 3.3 Prompting Conventions

- Normal text → appended as a user message
- Multi-line input supported
- Optional mode:
  - `\` at end continues line
  - or explicit `/multiline` toggles multiline mode

---

## 4) Architecture Overview

### 4.1 Components

1. **CLI Frontend**
   - Parses args
   - Chooses mode (one-shot, file analysis, chat)
   - Routes to Chat REPL or SingleCall

2. **Session Manager**
   - Holds in-memory conversation: list of `{role, content, ts, meta}`
   - Persists to disk (JSONL recommended)
   - Supports load/reset/save

3. **Inference Router**
   - Responsible for:
     - model fallback
     - retry policy
     - timeouts
     - response normalization

4. **Tokenizer/Budgeter (lightweight)**
   - We won’t do true tokenization without deps; we use:
     - character budgets
     - heuristic truncation
   - Optional future: add tiktoken only if needed.

5. **Logger**
   - Structured logs per run and per session
   - Redaction layer before writing logs

---

## 5) Persistence & Filesystem Layout

### 5.1 Base directory

- Linux/WSL: `~/.ahura/`
- Windows: `%USERPROFILE%\.ahura\`

We implement this via a small resolver:

- if `$HOME` exists → use `$HOME/.ahura`
- else use `%USERPROFILE%\.ahura`

### 5.2 Proposed Layout
```

.ahura/

logs/

YYYY-MM-DD_HH-MM-SS_ahura.log

sessions/

session_<id>.jsonl

session_<id>.meta.json

cache/

config/

config.json

                                            _content_copy_                        text

`### 5.3 Session Format  **JSONL** (append-friendly, crash tolerant):  Each line: ```json {"ts":"2026-07-30T15:17:28Z","role":"user","content":"...","meta":{"source":"repl"}}`

`meta.json`:

                                            _content_copy_                        json_note_add_ویرایش با Canvas

`{   "session_id": "20260730_151728_ABC123",   "created_at": "...",   "model_policy": {"fallback": true, "preferred": null},   "system_prompt": "...",   "files_attached": ["..."] }`

---

## 6) Redaction & Safety

### 6.1 Secret Redaction

Before logs or session persistence:

- Detect patterns resembling keys:
    - `OPENROUTER_API_KEY=...`
    - `sk-...`
    - `Bearer ...`
- Replace with `***REDACTED***`

### 6.2 File Ingestion Safety

- Default max file bytes (e.g., 200 KB)
- For larger files:
    - Summarize first (`head`, `tail`, and key sections)
    - Ask user to confirm full ingest OR chunk it
- Never auto-upload binary files unless explicitly requested.

### 6.3 Token/Context Budget

Heuristic approach:

- Maintain a rolling window:
    - Keep system prompt
    - Keep last N turns
    - Keep file summaries, not full raw logs
- Optional `/compress` command:
    - ask model to summarize the conversation into a compact state message
    - replace older turns with summary

---

## 7) Cross-Platform REPL Implementation (Python)

### 7.1 Why Python REPL?

- Works identically on Windows/WSL
- Better multiline input handling
- Easier structured persistence + redaction + logging

### 7.2 Dependencies

- Python 3.12+
- Stdlib only:
    - `argparse`, `json`, `pathlib`, `datetime`, `os`, `sys`, `re`, `readline` (optional on Linux)
- Optional future:
    - `prompt_toolkit` for nicer UX (only if needed)

---

## 8) CLI Spec (Proposed)

### 8.1 One-shot

                                            _content_copy_                        bash_note_add_ویرایش با Canvas

`ahura "Explain CVE-2024-xxxx impact"`

### 8.2 File analysis

                                            _content_copy_                        bash_note_add_ویرایش با Canvas

`ahura -f /mnt/d/ASUS\ X550/systeminfo.txt "Analyze for security risks"`

### 8.3 Chat mode

                                            _content_copy_                        bash_note_add_ویرایش با Canvas

`ahura --chat # or ahura chat`

### 8.4 Chat + file preload

                                            _content_copy_                        bash_note_add_ویرایش با Canvas

`ahura --chat -f ./systeminfo.txt`

### 8.5 Session options

                                            _content_copy_                        bash_note_add_ویرایش با Canvas

`ahura chat --session new ahura chat --session load:20260730_151728_ABC123 ahura chat --session last`

---

## 9) Implementation Plan (Incremental)

### Phase 1 — Minimal viable Chat Mode

- Python entrypoint `ahura.py`
- `--chat` starts REPL
- `/exit`, `/reset`, `/help`
- Keep in-memory conversation and send to inference layer
- Logging per run

### Phase 2 — Persistence

- Create session store in `~/.ahura/sessions`
- Autosave every turn (JSONL)
- `/save`, `/load`

### Phase 3 — File attach in REPL

- `/file <path>`:
    - load file (with size guard)
    - store summary in session
    - include in context for next inference call

### Phase 4 — Compression and budgeting

- Rolling window
- `/compress` summarization feature

### Phase 5 — Windows packaging

- `ahura.cmd` shim for Windows
- Optional PyInstaller later (only if necessary)

---

## 10) Test Strategy

- Unit tests:
    - redaction correctness
    - session JSONL append & load
    - rolling window trimming
- Integration tests:
    - mock OpenRouter HTTP response
    - fallback behavior on 429/5xx

---

## 11) Open Questions / Decisions Needed

1. Should the REPL maintain _multiple_ named sessions simultaneously or only one active?
2. Do we require strict deterministic trimming or allow model-based summarization by default?
3. How should we handle files on Windows paths (`D:\...`) vs WSL (`/mnt/d/...`)—should Ahura auto-normalize?

---

## Appendix A — Recommended Defaults

- `max_file_bytes`: 200_000
- `max_context_chars`: 40_000 (heuristic)
- `fallback_models`:
    - `openai/gpt-oss-20b:free`
    - `qwen/qwen-2.5-7b-instruct:free`
    - (others as available)

---

## Appendix B — Example REPL Session

                                            _content_copy_                        text_note_add_ویرایش با Canvas

`$ ahura --chat Ahura Chat — session 20260730_151728_ABC123 Type /help for commands.  you> /file /mnt/d/ASUS X550/systeminfo.txt ahura> Loaded file (3.2 KB). Summary stored.  you> What are my top 3 security risks? ahura> ...`