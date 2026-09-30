"""Small synthetic D2 fixtures; functions only, with no discovery classes."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import case_memory as memory  # noqa: E402
import semantic_identity as semantic  # noqa: E402


TITLES = {
    1: "每晚观察闸口排队量，估计下一观察期的等待需求。",
    2: "比较服务站的多项指标，在统一口径下给出条件性等级。",
    3: "同一计划期内分配连续工时，使共享资源下的总效益更好。",
    4: "解释均匀氧舱中库存随外部流入和流出变化的关系。",
    5: "安排巡检任务，联合处理通行连接、作业时段和设备占用。",
    6: "估计固定期限内保障池触发事件的风险及抽样不确定性。",
    7: "前问估计下一班次用量，后问使用该口径形成资源安排。",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def canonical_sha(value: object) -> str:
    def normalize(item):
        if isinstance(item, str):
            return item.replace("\r\n", "\n").replace("\r", "\n")
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        return item
    raw = json.dumps(normalize(value), ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def copy_corpus(destination: Path) -> Path:
    shutil.copytree(ROOT / "knowledge/case_memory", destination,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return destination


def refresh_corpus(corpus: Path) -> None:
    """Rebind intentionally changed fixture inputs and write only its temp index."""
    sources = read_json(corpus / "sources.json")
    cases = read_json(corpus / "cases.json")
    source_by_id = {row["id"]: row for row in sources["sources"]}
    for case in cases["cases"]:
        case["source"]["sha256"] = memory.source_sha256(source_by_id[case["source"]["id"]])
    write_json(corpus / "sources.json", sources)
    write_json(corpus / "cases.json", cases)
    features_path = corpus / "retrieval_features.json"
    if features_path.exists():
        features = read_json(features_path)
        case_by_id = {row["id"]: row for row in cases["cases"]}
        for feature in features["features"]:
            case = case_by_id[feature["case_id"]]
            feature.update(case_version=case["version"], case_sha256=canonical_sha(case),
                           source_sha256=case["source"]["sha256"])
        write_json(features_path, features)
    write_json(corpus / "index.json", memory.build_index(corpus))


def query_for(corpus: Path, number: int = 3) -> dict:
    """A seed-derived development query; it is deliberately not a held-out task."""
    case_id = f"CM-SYN-{number:03d}"
    case = next(row for row in read_json(corpus / "cases.json")["cases"] if row["id"] == case_id)
    feature = next(row for row in read_json(corpus / "retrieval_features.json")["features"]
                   if row["case_id"] == case_id)
    traits = {key: row["value"] for key, row in feature["traits"].items()}
    traits["conditions"] = {row["condition"]: "satisfied" for row in feature["required_conditions"]}
    return {"protocol_version": "1.0.0", "objective": case["structure"]["objective"],
            "structures": deepcopy(case["structure"]["structures"]),
            "capabilities": deepcopy(case["structure"]["capabilities"]),
            "summary": TITLES[number], "traits": traits}


def write_state(root: Path, state: dict) -> None:
    (root / "state").mkdir(exist_ok=True)
    (root / "state/project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def make_project(root: Path) -> dict:
    root.mkdir()
    state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
    state["project"].update(problem="independently authored synthetic D2 control-plane fixture", state_generation=0)
    state["requirements"].update(total=1, completed=["Q1"], pending=[])
    state["decisions"]["Q1"].update(selected_model="synthetic resource model", key_reason="Synthetic reference fixture.")
    question = state["subproblems"]["Q1"]
    question.update(selected_model="synthetic resource model", framework_section="### Q1：合成资源分配",
                    model_challenge_status="pending", human_model_approval_status="pending")
    question["classification"] = {"objective": "optimization", "structures": []}
    question["capabilities"] = {key: key in ("has_explicit_constraints", "requires_feasibility_check")
                                for key in question["capabilities"]}
    text = (
        "# 模型论文框架\n\n### Q1：合成资源分配\n#### 当前模型口径\n"
        "**题意口径（Problem Contract）**\n"
        "本题是独立合成结构：同一计划期内，已知需求、消耗和效益；"
        "允许连续分配且关系为线性。输出满足共享资源限制的方案。\n"
        "**变量、假设与模型**\n"
        "仅声明模型设计条件；未执行求解、数值验收或独立审查。\n"
        "#### 结果摘要\n未执行计算。\n"
    )
    (root / "模型论文框架.md").write_text(text, encoding="utf-8")
    write_state(root, state)
    return state


def add_synthetic_sib(root: Path, state: dict, *, declared_approved: bool = False) -> None:
    """Synthetic control fields for preservation tests, not actual approval evidence."""
    sib = {
        "schema_version": "1.0.0", "question": "Q1", "research_object": "合成资源分配",
        "data_scope": [{"id": "D1", "source": "synthetic definitions", "role": "输入"}],
        "variables": [{"id": "V1", "symbol": "x_i", "role": "decision", "domain": "continuous"}],
        "parameters": [{"id": "P1", "symbol": "c_i", "unit": "synthetic resource"}],
        "assumptions": [{"id": "A1", "statement": "允许连续分配且关系为线性"}],
        "objective": {"sense": "maximize", "expression": "B(x)"},
        "constraints": [{"id": "C1", "expression": "sum(x_i) <= capacity"}],
        "preprocessing_decision": "not_needed",
        "algorithm_semantics": {"model_family": "LP", "solver_role": "exact_or_gap_bounded"},
        "dependencies": [],
    }
    path = root / "模型论文框架.md"
    text = path.read_text(encoding="utf-8")
    marker = "<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->\n```yaml\n"
    marker += yaml.safe_dump(sib, allow_unicode=True, sort_keys=False)
    marker += "```\n<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->\n"
    text = text.replace("#### 结果摘要", marker + "\n#### 结果摘要")
    path.write_text(text, encoding="utf-8")
    inspected = semantic.inspect_question_semantics(semantic.question_sections(text)["Q1"], "Q1")
    digest = semantic.semantic_identity_hash(sib)
    question = state["subproblems"]["Q1"]
    question.update(semantic_identity_schema_version="1.0.0", semantic_identity_hash=digest,
                    semantic_text_hash=inspected["semantic_text_hash"])
    if declared_approved:
        question.update(model_challenge_status="passed", human_model_approval_status="approved",
                        validated_semantic_identity_hash=digest, approved_semantic_identity_hash=digest,
                        approved_semantic_revision=question["semantic_revision"],
                        validated_semantic_revision=question["semantic_revision"])
    write_state(root, state)
