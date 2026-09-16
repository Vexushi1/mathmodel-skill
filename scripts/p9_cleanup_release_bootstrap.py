from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_REFRESH = '''name: Refresh generated repository metadata

on:
  push:
    branches:
      - main
      - "codex/**"
      - "docs/**"
      - "feat/**"
      - "fix/**"
      - "refactor/**"
      - "upgrade/**"
    paths-ignore:
      - SKILL_FILE_INDEX.md
      - TEMPLATE_INDEX.md
      - HSK_SKILL_FILE_INDEX_V622.md
      - HSK_TEMPLATE_INDEX_V622.md
      - MANIFEST.sha256
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: refresh-generated-${{ github.ref }}
  cancel-in-progress: true

jobs:
  refresh-feature-branch:
    if: github.actor != 'github-actions[bot]' && github.ref_name != 'main'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      actions: write
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.ref_name }}
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Rebuild active indexes and manifest
        run: python scripts/generate_indexes.py
      - name: Commit generated metadata and validate final head
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          if git diff --quiet -- SKILL_FILE_INDEX.md TEMPLATE_INDEX.md HSK_SKILL_FILE_INDEX_V622.md HSK_TEMPLATE_INDEX_V622.md MANIFEST.sha256; then
            echo "Generated metadata is current."
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add SKILL_FILE_INDEX.md TEMPLATE_INDEX.md HSK_SKILL_FILE_INDEX_V622.md HSK_TEMPLATE_INDEX_V622.md MANIFEST.sha256
          git commit -m "chore: refresh generated repository metadata"
          git push
          final_head=$(git rev-parse HEAD)
          echo "Generated metadata final head: ${final_head}"
          gh workflow run ci.yml --ref "$GITHUB_REF_NAME"
          gh workflow run optimization-baseline.yml --ref "$GITHUB_REF_NAME"

  verify-main:
    if: github.ref_name == 'main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Verify generated metadata is already current
        run: python scripts/generate_indexes.py --check
'''

README_RELEASE = (
    "\n## v9.2.0：全面优化、运行协议与条件式证据链\n\n"
    "v9.2.0 汇总 P1–P8 已分阶段合并并通过回归的兼容优化：按任务 `reading_plan` 与 Authority 去重、compact `模型论文框架.md` 实例化、canonical `RUN_CONFIG` + versioned `RUN_RECEIPT`、MATLAB publication profile 与真实 preview gate、条件式 Analysis Necessity Gate / 附录，以及基于测量证据的基础设施整理。P9 只做综合回归、兼容窗口裁决和 release carrier 收尾，不重写这些阶段的业务实现。\n\n"
    "旧 `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG` 与 P5a 过渡期缺 receipt marker/version 的项目在 9.2.0 中继续**只读兼容**；新 writer 仍必须使用 `RUN_CONFIG` 并声明 `run_receipt_protocol_version=1.0.0`，未知显式协议版本继续 fail closed。上述 reader 的删除只允许在未来明确的 major migration 中进行，并须先提供旧项目识别/迁移证据、兼容矩阵更新与专门回归。\n"
)
README_V91_HEADER = "\n## v9.1.0：MATLAB Publication Rendering\n"


def strict_replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one occurrence, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    # The release applicator inserts the new README section immediately after the old
    # v9.1 heading marker. Reorder it before v9.1 without changing either section body.
    readme = ROOT / "README.md"
    strict_replace(readme, README_V91_HEADER + README_RELEASE, README_RELEASE + README_V91_HEADER)

    # Keep the P9 regression language aligned with the Chinese release record.
    test_path = ROOT / "tests/test_p9_release_closeout.py"
    strict_replace(
        test_path,
        '        self.assertIn("unknown", record.lower())\n',
        '        self.assertIn("未知", record)\n',
    )

    # Restore the canonical generated-metadata workflow and remove the one-shot
    # branch-local execution harness before the final P9 commit is produced.
    (ROOT / ".github/workflows/refresh-generated.yml").write_text(CANONICAL_REFRESH, encoding="utf-8")
    for relative in (
        ".github/workflows/p9-release-apply.yml",
        "scripts/p9_release_apply.py",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()
    Path(__file__).unlink()


if __name__ == "__main__":
    main()
