# Portable memory: taking auto memory across machines

Claude Code's auto memory writes itself as you work — corrective notes, debugging insights, build commands — but by default it doesn't travel. This page covers where it actually lives, why that's a problem for anyone who splits work across WSL/Windows, multiple machines, or hosted sessions, and how to fix it.

## Where auto memory actually lives

Each project gets its own memory directory at `~/.claude/projects/<project>/memory/`, where `<project>` is a munged form of the absolute repo path (`/` and `.` become `-`). The directory is keyed off the git repository, so every worktree and subdirectory of the same repo shares one store.

For example, a repo cloned to `/home/alice/repos/claude-memory-map` gets its auto memory at `~/.claude/projects/-home-alice-repos-claude-memory-map/memory/` — every `/` and `.` in the absolute path becomes a `-`.

That keying is also the catch: it's *machine-local by design*. Per Anthropic's docs — [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) — "Files are not shared across machines or cloud environments."

## What that breaks in practice

- **WSL and Windows are different machines.** The same repo checked out under WSL and under native Windows gets two separate `~/.claude/projects/.../memory/` directories, with no sync between them. Claude relearns the same lessons twice.
- **Deleting a workspace orphans its memory.** Remove or rename a project directory and its memory directory has no path back to it — nothing deletes it, nothing finds it again.
- **Hosted sessions see none of it.** Claude Code on the web and cloud sandboxes start from a fresh clone; the machine-local memory directory isn't part of that clone, so hosted sessions never read (or write back to) what's accumulated locally.

## The fix: `autoMemoryDirectory`

Since Claude Code v2.1.74, `autoMemoryDirectory` lets you redirect where a project's memory lives. Set it in a settings file:

```json
{
  "autoMemoryDirectory": "~/repos/claude-memory-map/.claude/memory"
}
```

Two things matter for this to actually solve the problem:

1. **The value must be absolute, or start with `~/`.** Anthropic's docs are explicit on this.
2. **Point it inside the repo, and commit `.claude/settings.json`.** Do this and auto memory becomes a git-tracked directory: it travels to every machine that clones the repo, and into every hosted-session clone, instead of staying pinned to `~/.claude/projects/...` on one machine.

`autoMemoryDirectory` is honored from any settings scope (user, project, local, policy, `--settings`), but when set in a project's `.claude/settings.json` or `.claude/settings.local.json` it only takes effect after you accept the workspace-trust dialog for that folder — the same gate hooks use.

This works cleanly as long as every machine you use keeps the repo under the same `~`-relative path (e.g. `~/repos/claude-memory-map` on both WSL and native Windows) — `autoMemoryDirectory`'s `~/`-relative form resolves per-machine, so a mismatched layout will make it point at different places.

### Checking whether it's active

Run `/memory` inside a Claude Code session. It lists every CLAUDE.md, rules file, and the auto memory folder currently loaded, with a link to open that folder. If `autoMemoryDirectory` took effect, that link points inside the repo (e.g. `.claude/memory/MEMORY.md`) instead of `~/.claude/projects/<project>/memory/MEMORY.md`.

## Caveats

- **Public repos publish their memory.** If `autoMemoryDirectory` points inside a public repo, whatever Claude writes there ships with the next push. Treat memory files like any other repo content — review diffs, never store secrets or PII in them.
- **Hosted sessions don't sync writes back.** A hosted session reads the committed memory files fine, but anything it writes during that session only becomes durable if something commits it — there's no background sync from a hosted session's memory back into your local checkout.
- **`CLAUDE_MEMORY_STORES` exists but is undocumented.** The v2.1.172 changelog mentions fixing "memory recall not finding mounted team memory stores (`CLAUDE_MEMORY_STORES`) in remote sessions" — implying a mechanism for mounting shared team memory into remote/hosted sessions. There's no public documentation of it yet. Watch this space.

## Migrating existing memory

If you already have auto memory scattered across `~/.claude/projects/*/memory/` on one or more machines, don't hand-copy files. Use the [`migrate-claude-memory`](https://github.com/Adam-S-Daniel/agentskills/tree/main/plugins/migrate-claude-memory) plugin from `Adam-S-Daniel/agentskills`:

1. **Inventory** — list what's stored where, across machines/worktrees.
2. **Migrate** — consolidate into one target directory (e.g. inside this repo).
3. **Set the setting** — point `autoMemoryDirectory` at the consolidated directory and commit `.claude/settings.json`.

## Related reading

- [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) — Anthropic's memory docs: CLAUDE.md files, auto memory, storage location, and `autoMemoryDirectory`.
- [Settings reference](https://code.claude.com/docs/en/settings) — full settings-file precedence (user, project, local, policy) that `autoMemoryDirectory` follows.
