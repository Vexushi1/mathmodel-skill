#!/usr/bin/env python3
"""Apply a narrow, idempotent cross-platform font fallback patch to cumcmthesis.cls."""
from __future__ import annotations

import argparse
from pathlib import Path

ORIGINAL_FONT_BLOCK = r"""% 设置字体
\setmainfont{Times New Roman}
%\setmonofont{Courier New}
\setsansfont{Arial}
\setCJKfamilyfont{kai}[AutoFakeBold]{simkai.ttf}
\newcommand*{\kai}{\CJKfamily{kai}}
\setCJKfamilyfont{song}[AutoFakeBold]{SimSun}
\newcommand*{\song}{\CJKfamily{song}}"""

FALLBACK_FONT_BLOCK = r"""% 设置字体：优先使用竞赛常用字体，缺失时回退到 TeX Live 字体文件。
\IfFontExistsTF{Times New Roman}
  {\setmainfont{Times New Roman}}
  {\IfFontExistsTF{TeX Gyre Termes}
     {\setmainfont{TeX Gyre Termes}}
     {\setmainfont{lmroman10-regular.otf}}}
\IfFontExistsTF{Arial}
  {\setsansfont{Arial}}
  {\IfFontExistsTF{TeX Gyre Heros}
     {\setsansfont{TeX Gyre Heros}}
     {\setsansfont{lmsans10-regular.otf}}}
\IfFontExistsTF{KaiTi}
  {\setCJKfamilyfont{kai}[AutoFakeBold]{KaiTi}}
  {\setCJKfamilyfont{kai}[AutoFakeBold]{FandolKai-Regular.otf}}
\newcommand*{\kai}{\CJKfamily{kai}}
\IfFontExistsTF{SimSun}
  {\setCJKfamilyfont{song}[AutoFakeBold]{SimSun}}
  {\setCJKfamilyfont{song}[AutoFakeBold]{FandolSong-Regular.otf}}
\newcommand*{\song}{\CJKfamily{song}}"""


def patch_cumcm_class(path: Path) -> bool:
    """Patch only the known font block and preserve every other byte-level line."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"cumcmthesis class not found: {path}")

    text = path.read_text(encoding="utf-8")
    if FALLBACK_FONT_BLOCK in text:
        return False
    count = text.count(ORIGINAL_FONT_BLOCK)
    if count != 1:
        raise ValueError(
            "cumcmthesis.cls font block does not match the audited template; "
            f"expected exactly one match, found {count}. Refuse broad replacement."
        )

    patched = text.replace(ORIGINAL_FONT_BLOCK, FALLBACK_FONT_BLOCK, 1)
    path.write_text(patched, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("class_file", type=Path)
    args = parser.parse_args()
    changed = patch_cumcm_class(args.class_file)
    print("patched" if changed else "already patched", args.class_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
