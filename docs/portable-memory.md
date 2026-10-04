# Portable memory: taking auto memory across machines

Claude Code's auto memory writes itself as you work — corrective notes, debugging insights, build commands — but by default it doesn't travel. This page covers where it actually lives, what that breaks if you split work across WSL/Windows, multiple machines, or hosted sessions, and the setting and permissions that can make it portable.

## Where auto memory actually lives

By default, each project gets a memory directory at `~/.claude/projects/<project>/memory/`. A typical short-path example is `/home/you/repos/claude-memory-map` mapping to `~/.claude/projects/-home-you-repos-claude-memory-map/memory/`; this illustrates a sanitized project key, not a guaranteed encoding algorithm. The [storage-location docs](https://code.claude.com/docs/en/memory#storage-location) describe how the git repository determines the default project key, so its worktrees and subdirectories normally share a store. The [v2.1.224 long-path collision fix](https://github.com/anthropics/claude-code/releases/tag/v2.1.224) concerns session directories for paths over 200 characters; it does not establish a new auto-memory hash algorithm.

Hosts with a separate config directory per session can use `CLAUDE_CODE_PROJECT_DIR_NAME` (introduced in [v2.1.234](https://github.com/anthropics/claude-code/releases/tag/v2.1.234)) with `CLAUDE_CONFIG_DIR` to choose a short project key. The same config directory and project key share the corresponding directory, so hosts must choose those boundaries deliberately. Run `/memory` to find the active memory location instead of deriving it from a path example.

That keying is also the catch: it's *machine-local by design*. Per Anthropic's docs — [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) — "Files are not shared across machines or cloud environments."

## What that breaks in practice

- **WSL and Windows are different machines.** The same repo checked out on both sides gets two separate memory directories with no sync between them. Claude relearns the same lessons twice.
- **Deleting a workspace orphans its memory.** Remove or rename a project directory and its memory directory has no path back to it — nothing deletes it, nothing finds it again.
- **Hosted sessions do not inherit laptop memory.** Claude Code on the web (cloud sessions) starts from a fresh clone; the laptop's machine-local memory directory isn't part of that clone. Committed memory and configured startup hooks can supply content inside the task sandbox, but they do not sync the laptop's memory directory.

## Making memory portable: `autoMemoryDirectory`

Since Claude Code v2.1.74, `autoMemoryDirectory` redirects where a project's memory lives. Set it in a settings file:

```json
{
  "autoMemoryDirectory": "~/repos/claude-memory-map/.claude/memory"
}
```

Two things make this actually solve the problem:

1. **The value must be absolute, or start with `~/`.** Anthropic's docs are explicit on this.
2. **Point it inside the repo, and commit the memory files and `.claude/settings.json`.** The committed files travel to every machine or hosted session that clones the repo. The setting alone does not track or commit them, and their use still depends on permissions.

`autoMemoryDirectory` is honored from any settings scope (user, project, local, policy, `--settings`), but when set in a project's `.claude/settings.json` or `.claude/settings.local.json` it only takes effect after you accept the workspace-trust dialog for that folder — the same gate hooks go through.

When `permissions.blockReadsOutsideWorkingDirectories` is enabled, an `autoMemoryDirectory` supplied by project or local settings is not loaded into the prompt, recalled, indexed, used by memory extraction, or written to — **even when the chosen directory is inside the repo**. Accepting workspace trust does not override this permission. The [memory docs](https://code.claude.com/docs/en/memory#storage-location) describe the restriction, and [v2.1.273](https://github.com/anthropics/claude-code/releases/tag/v2.1.273) fixed the prompt, recall, indexing, and extraction paths. Repo-tracked memory is therefore portable only when the active permissions allow it.

One layout requirement: every machine must keep the repo at the same `~`-relative path (e.g. `~/repos/claude-memory-map` on both WSL and native Windows). The `~/`-relative form resolves per-machine, so a mismatched layout points different machines at different places.

### Checking whether it's active

Run `/memory` inside a Claude Code session. It lists every CLAUDE.md, rules file, and the auto memory folder currently loaded, with a link to open that folder. If `autoMemoryDirectory` took effect, the link points inside the repo (e.g. `.claude/memory/MEMORY.md`) instead of `~/.claude/projects/<project>/memory/MEMORY.md`.

### Startup index limits

According to the [auto-memory docs](https://code.claude.com/docs/en/memory#how-it-works), startup loads the first **200 lines or 25KB of `MEMORY.md`, whichever comes first**. The measured loaded content excludes frontmatter and HTML comments. The remaining index content is not loaded at the next startup; keep `MEMORY.md` short and move detail into topic files, which Claude reads on demand.

An over-limit write succeeds in saving the file but returns an explicit error asking Claude to shorten the index; it does not reject the write. [v2.1.210](https://github.com/anthropics/claude-code/releases/tag/v2.1.210) added that error, [v2.1.211](https://github.com/anthropics/claude-code/releases/tag/v2.1.211) corrected the measurement to exclude frontmatter and HTML comments, and [v2.1.268](https://github.com/anthropics/claude-code/releases/tag/v2.1.268) made truncation warnings report how many lines were cut and where the cut starts.

## Caveats

- **Public repos publish committed memory.** If `autoMemoryDirectory` points inside a public repo, memory files you commit ship with the next push. Treat memory files like any other repo content — review diffs, never store secrets or PII in them.
- **Hosted sessions don't sync writes back.** A hosted session can read committed memory when the active settings and permissions allow it. What it writes only becomes durable if something commits it — there's no background sync into your local checkout.
- **`CLAUDE_MEMORY_STORES` exists but is undocumented.** The v2.1.172 changelog mentions fixing "memory recall not finding mounted team memory stores (`CLAUDE_MEMORY_STORES`) in remote sessions" — implying shared team memory mountable into hosted sessions. Since then, platform.claude.com has documented a beta [Memory Stores API](https://platform.claude.com/docs/en/api/beta/memory_stores) (`POST /v1/memory_stores`); whether that's what `CLAUDE_MEMORY_STORES` mounts is unconfirmed, and Claude Code's docs still mention neither. Watch this space.

## Migrating existing memory

If auto memory is already scattered across `~/.claude/projects/*/memory/` on one or more machines, don't hand-copy files. Use the [`migrate-claude-memory`](https://github.com/Adam-S-Daniel/agentskills/tree/main/plugins/migrate-claude-memory) plugin from `Adam-S-Daniel/agentskills`:

1. **Inventory** — list what's stored where, across machines and worktrees.
2. **Migrate** — consolidate into one target directory (e.g. inside this repo).
3. **Set the setting** — point `autoMemoryDirectory` at the consolidated directory and commit `.claude/settings.json`.

## Related reading

- [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) — Anthropic's memory docs: CLAUDE.md files, auto memory, storage location, and `autoMemoryDirectory`.
- [Settings reference](https://code.claude.com/docs/en/settings) — the settings-file precedence (user, project, local, policy) that `autoMemoryDirectory` follows.
