# docs/images/

Hosted images embedded in `README.md` and other docs. Keep filenames stable so external links don't rot.

## Conventions

- **Format:** SVG for diagrams (scales cleanly, dark-mode friendly), PNG for screenshots and dashboard captures.
- **Width target:** 720–780 px embedded; source can be larger.
- **Naming:** kebab-case, no version suffixes (use git history for revisions). E.g. `architecture.svg`, `dashboard-hero.png`, `escalation-tree.svg`.
- **Compression:** PNGs run through a lossless optimizer (e.g. `oxipng`, `pngquant`) before commit.
- **Alt text:** always include — both for accessibility and because GitHub's social-card renderer reads it.

## Current contents

The architecture diagram lives at [`../assets/architecture_v2.2.svg`](../assets/architecture_v2.2.svg) for now (legacy path); future revisions will land here.

## Pending captures

- `dashboard-hero.png` — Medical Director dashboard with one decided case, rationale visible. Capture from a running dev server (`docker compose up -d`, then `http://localhost:3000`). Crop tightly. Embed at top of README.
- `escalation-tree.svg` — visual rendering of the 7-branch escalation logic. Sequence-diagram style, one branch per swimlane.

These are tracked in the portfolio overhaul punch list and will land via separate commits so each can be reviewed in isolation.
