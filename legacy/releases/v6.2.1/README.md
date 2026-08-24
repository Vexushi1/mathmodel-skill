# HSK v6.2.1 historical release

The v6.2.1 root-level snapshots were removed from the active repository surface to prevent semantic search and agents from loading obsolete rules.

Historical source remains available in Git history at release commit:

```text
409a49e424946d460b56af6a030f3f6dd4b0ebaa
```

Historical files:

- `CHANGELOG_V621.md`
- `HSK_RUNTIME_ROUTER_V621.md`
- `HSK_SKILL_FILE_INDEX_V621.md`
- `HSK_TEMPLATE_INDEX_V621.md`
- `PROJECT_INSTRUCTIONS_HSK_V621.md`

Do not copy these files back into the active root. For current execution, begin with the repository's current `core/bootstrap.yaml` and follow the active root entries and resolver referenced there. This file is a historical pointer only and does not define the current Skill version or runtime contract.
