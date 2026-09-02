from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [ROOT / "SKILL.md", ROOT / "skills/mathmodel-skill/SKILL.md"]

for path in PATHS:
    text = path.read_text(encoding="utf-8")
    old = "3. 使用 `scripts/resolve_runtime.py` 根据当前意图、竞赛和项目状态解析最小 `load_order`、运行时 assurance 与 `pre_delivery_gates`；"
    new = (
        "3. 使用 `scripts/resolve_runtime.py` 根据当前意图、竞赛和项目状态解析最小 `load_order`、运行时 assurance 与 `pre_delivery_gates`；"
        "模型批准、条件式预处理与主数值验证分别委托 `core/model_approval_contract.yaml`、`core/global_preprocessing_contract.yaml`、`core/numerical_verification_contract.yaml`；"
    )
    if text.count(old) != 1:
        raise RuntimeError(f"runtime delegation anchor drifted: {path}")
    text = text.replace(old, new, 1)
    anchor = "以下名称仅用于能力发现与回归，不在本入口重复定义规则：**Template Manifest、Paper Writing Protocol、Primary Evidence Capture、Scientific Figure Synthesis、Model/Solver/Validator、Claim Strength Calibration、within-question local dependency architecture、decisiveness-based detail allocation、adaptive figure-result narrative**。具体定义只读取上表 Authority。"
    addition = (
        anchor
        + "\n\n兼容发现 token 仅保留名称：`preprocessing_decision`、`问题X结果深化分析.py`、**Algorithm Trace**。"
        + "它们用于 lint/路由与 artifact 导航，不在入口重新定义预处理枚举、结果分析流程或算法呈现规则。"
    )
    if text.count(anchor) != 1:
        raise RuntimeError(f"capability anchor drifted: {path}")
    path.write_text(text.replace(anchor, addition, 1), encoding="utf-8", newline="\n")

print("minimal compatibility tokens retained")
