# SME Case Authoring Agent — Installation Guide

> **For:** The clinician's IT-support person, lab IT staff, or any technical
> contact helping a clinician set up `pacca sme-author` on their workstation.
> **Time:** 15–30 minutes (depending on Python installation).
> **Outcome:** The clinician can run `pacca sme-author new` from their terminal.

---

## 1. What you're installing

`pacca` is a Python command-line tool. After install, the clinician will be able to run:

```
$ pacca sme-author new
```

…to author clinical test cases for PACCA's evaluation dataset. The tool needs:

- Python 3.11 or newer
- Git
- An Anthropic API key (provided by the team)
- ~500 MB of disk space for dependencies

---

## 2. The 5-step install

### Step 1 — Install Python 3.11+

**macOS:** Use Homebrew:
```bash
brew install python@3.12
```

**Windows:** Download from https://www.python.org/downloads/ and check "Add Python to PATH" during install.

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3.12 python3.12-venv git
```

Verify:
```bash
python3 --version    # should print 3.11.x or higher
git --version        # should print a git version
```

### Step 2 — Clone the PACCA repository

```bash
git clone https://github.com/drdgreed/pacca.git ~/pacca
cd ~/pacca
```

(Replace `~/pacca` with wherever the clinician wants the project to live.)

### Step 3 — Create a virtual environment + install

```bash
python3 -m venv .venv
source .venv/bin/activate           # macOS / Linux
# OR on Windows:
.venv\Scripts\activate

pip install --upgrade pip
pip install -e ".[dev]"
```

The `.[dev]` install pulls in everything: runtime deps + Click + Anthropic SDK + pytest + ruff + mypy.

Expect this step to take 3–8 minutes depending on network speed.

### Step 4 — Set the Anthropic API key

The clinician's team will provide an API key starting with `sk-ant-`. Set it in the shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Make it persistent.** Add the export line to the clinician's shell profile:

**macOS (zsh):**
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
```

**Linux (bash):**
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
```

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")
```

After this, every new terminal session will have the key available.

**Important — secrets handling per PACCA's CLAUDE.md:**
- Never commit the API key to git.
- Never share via screenshot or email body.
- If the key is exposed, request a rotation from the team.

### Step 5 — Verify

In a fresh terminal (so the new env var takes effect):

```bash
cd ~/pacca
source .venv/bin/activate

pacca --version              # → "pacca, version 2.4.0"
pacca sme-author --help      # → lists 8 subcommands
```

You should see:
```
Commands:
  batch          Show a roadmap batch's case-slot manifest.
  list-batches   List batches from docs/DATASET_GROWTH_ROADMAP.md.
  list-gaps      List the highest-priority coverage gaps.
  list-sessions  List saved SME-authoring sessions.
  new            Interactive workflow to author a new golden case.
  resume         Show a saved session's state.
  status         Report dataset state + distance to milestones.
  validate       Validate a CaseDraftResponse JSON file.
```

If you see this, the install is complete. Hand the clinician `docs/SME_CASE_AGENT_USER_MANUAL.md` and they're ready to author.

---

## 3. Troubleshooting

### "pacca: command not found"

The virtual environment isn't activated. Re-run:
```bash
cd ~/pacca
source .venv/bin/activate
```

Or if the `pip install -e` didn't complete, re-run it:
```bash
pip install -e ".[dev]"
```

### "ANTHROPIC_API_KEY not set"

Either the export didn't persist, or the terminal wasn't restarted. Verify:
```bash
echo $ANTHROPIC_API_KEY    # should print "sk-ant-..."
```

If empty, re-run Step 4.

### "pip install" fails with compiler errors

Some dependencies (e.g., `bcrypt`, `cryptography`) need a C compiler.

**macOS:** Install Xcode Command Line Tools:
```bash
xcode-select --install
```

**Ubuntu/Debian:**
```bash
sudo apt install build-essential python3.12-dev
```

**Windows:** Install Microsoft C++ Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/

### "ModuleNotFoundError: No module named 'pacca'"

Confirm `pip install -e .` ran successfully:
```bash
pip show pacca
```

Should show the package + its install location. If not, re-run the install.

### "AsyncAnthropic not found / anthropic module errors"

Verify the Anthropic SDK is installed:
```bash
pip show anthropic
```

If missing, run:
```bash
pip install "anthropic>=0.40.0"
```

### "Permission denied" on the install

The clinician's account may not have write permissions to the Python site-packages. Use a virtual environment (Step 3) instead of installing globally.

### CI / Test failures

The unit-test suite is not required for SME authoring — but if the clinician wants to verify:
```bash
make test
```

Should print `275 passed`. If it errors, the install is corrupted; re-do Step 3.

---

## 4. Updating to a new release

When the PACCA team ships a new version:

```bash
cd ~/pacca
git pull origin main
source .venv/bin/activate
pip install -e ".[dev]" --upgrade
```

Then re-run `pacca --version` to confirm the new version.

---

## 5. Uninstalling

To remove `pacca` entirely:

```bash
# Deactivate the venv if it's active
deactivate

# Remove the project + venv
rm -rf ~/pacca

# Remove the API key from the shell profile
# (edit ~/.zshrc or ~/.bashrc; delete the ANTHROPIC_API_KEY line)
```

Session state in `~/.pacca/sme_authoring_sessions/` is preserved unless explicitly removed:
```bash
rm -rf ~/.pacca/
```

---

## 6. Network requirements

The tool needs HTTPS outbound access to:

- `api.anthropic.com` (for the LLM)
- `github.com` (for `git pull` during updates)
- `pypi.org` (for `pip install`)

If the clinician's institution has a firewall, those three domains need to be allow-listed.

---

## 7. Privacy + data handling

- **No patient data is sent over the network.** The tool generates synthetic clinical scenarios; the LLM only sees what the clinician types into the scenario field, which per the User Manual is synthetic.
- **Session state is local** (`~/.pacca/sme_authoring_sessions/`) — not transmitted anywhere.
- **The API key is local** — not stored in any repo file. If the institution rotates keys, the clinician just updates the env var.

If the institution has data-handling policies that prohibit any LLM use, the tool's `validate` subcommand can be used standalone (no LLM call) for CI-style validation of pre-drafted cases.

---

## 8. Where to get help

| Problem | Where |
|---|---|
| Install errors | This document § 3 |
| "How do I author a case?" | `docs/SME_CASE_AGENT_USER_MANUAL.md` |
| "What does the agent actually do?" | `docs/SME_CASE_AGENT_DESIGN.md` |
| API key issues | The team that provided the key |
| GitHub issues | https://github.com/drdgreed/pacca/issues |

---

*Last updated: 2026-05-25 (iter-7 close — SMECaseAuthoringAgent v1.0).*
