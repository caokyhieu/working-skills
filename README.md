# Working Skills

Reusable agent skills for your local projects.

This repository includes [Insight PPT](insight-ppt/SKILL.md), a skill for creating, outlining, reviewing, and revising editable PowerPoint proposals. It connects a product's business value with its architecture and technical fit, with supporting evidence and speaker notes. The skill works with both **Codex** (CLI, app, or IDE extension) and **Claude Code**; it's the same `SKILL.md` instructions, installed under whichever agent's skill directory your project uses.

The skill also guides editable architecture diagrams, sequence diagrams, decision flowcharts, tables, and data charts. Its [visual design guide](insight-ppt/references/visual-design.md) adapts the compositions in `samples/` into one consistent deck style. The sample images are optional references; the installed skill includes the guidance it needs without copying that folder.

## Install in your project

You need Git and either Codex or Claude Code. The commands below use a macOS/Linux shell or Git Bash on Windows.

### 1. Clone this repository

Run this from the directory where you keep your repositories:

```sh
git clone https://github.com/caokyhieu/working-skills.git
cd working-skills
```

If you already cloned the repository, open that local checkout instead.

### 2. Copy the skill into your project

From the `working-skills` directory, replace `/absolute/path/to/your-project` with your project's actual path, then pick the section for your agent below.

```sh
PROJECT_DIR="/absolute/path/to/your-project"
```

Copy the entire `insight-ppt` folder either way: its instructions depend on the bundled references and templates.

#### Codex

```sh
mkdir -p "$PROJECT_DIR/.agents/skills"
cp -R insight-ppt "$PROJECT_DIR/.agents/skills/"
```

Your project should now contain:

```text
your-project/
└── .agents/
    └── skills/
        └── insight-ppt/
            ├── SKILL.md
            ├── agents/
            │   └── openai.yaml
            ├── references/
            └── templates/
```

Codex discovers project skills under `.agents/skills`. See the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

Open your target project in Codex. In the CLI or IDE extension, type `/skills` to find the skill, or mention `$insight-ppt` directly in a prompt:

```text
$insight-ppt Outline a 15-minute proposal for adding semantic search to our
customer support product. The audience is engineering leadership. Use the
architecture notes in docs/architecture.md and identify missing information.
```

If the skill does not appear, restart Codex and confirm that `.agents/skills/insight-ppt/SKILL.md` exists in your project. Skill discovery and invocation are described in the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills).

#### Claude Code

```sh
mkdir -p "$PROJECT_DIR/.claude/skills"
cp -R insight-ppt "$PROJECT_DIR/.claude/skills/"
```

Your project should now contain:

```text
your-project/
└── .claude/
    └── skills/
        └── insight-ppt/
            ├── SKILL.md
            ├── agents/
            │   └── openai.yaml
            ├── references/
            └── templates/
```

Claude Code discovers project skills under `.claude/skills` from the `name` and `description` in each `SKILL.md`'s frontmatter — no separate registration file is needed, so `agents/openai.yaml` is Codex-only metadata that Claude Code simply ignores; keep it if you also use Codex, or delete it if you don't.

Open your target project in Claude Code. Type `/insight-ppt` or describe the task naturally, mentioning the skill by name:

```text
/insight-ppt Outline a 15-minute proposal for adding semantic search to our
customer support product. The audience is engineering leadership. Use the
architecture notes in docs/architecture.md and identify missing information.
```

If the skill does not appear, restart Claude Code and confirm that `.claude/skills/insight-ppt/SKILL.md` exists in your project.

### 3. Provide context

Replace the example topic and document path with your own, for either agent. Include your product, audience, presentation duration, and any relevant architecture notes or existing decks. The skill gathers missing context and asks you to approve the brief and outline before building a new deck, unless you request a fast first draft.

## Share with your team or keep it local

Commit `.agents/skills/insight-ppt/` and/or `.claude/skills/insight-ppt/` to your project's Git repository to share the skill with teammates. To keep it only on your machine, add the relevant line(s) to your project's `.git/info/exclude` instead:

```gitignore
.agents/skills/insight-ppt/
.claude/skills/insight-ppt/
```

## Update the installed skill

The project copy is independent of this checkout. To update it, run `git pull --ff-only` inside your `working-skills` checkout, then copy the updated `insight-ppt` folder into your project's `.agents/skills/` and/or `.claude/skills/` directory again. Back up any project-specific edits first; copying replaces matching files. If an upstream update removes files, remove those obsolete files from the project copy too.
