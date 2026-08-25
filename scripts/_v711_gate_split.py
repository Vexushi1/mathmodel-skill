#!/usr/bin/env python3
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'scripts/resolve_workflow.py'
s = p.read_text(encoding='utf-8')
old = 'SEMANTIC_CODE_GATES = ["semantic_governance", "model_approval", "code_delivery"]\n'
new = 'PRIMARY_CODE_GATES = ["semantic_governance", "model_approval", "code_delivery"]\nANALYSIS_CODE_GATES = ["semantic_governance", "code_delivery"]\n'
assert old in s
s = s.replace(old, new, 1)
# preprocessing and primary-code branches need approval
s = s.replace('PREPROCESSING_OUTPUTS.copy(), ["code"], SEMANTIC_CODE_GATES.copy(), False, True', 'PREPROCESSING_OUTPUTS.copy(), ["code"], PRIMARY_CODE_GATES.copy(), False, True')
s = s.replace('PRIMARY_CODE_OUTPUTS.copy(), ["code"], SEMANTIC_CODE_GATES.copy(), False, True', 'PRIMARY_CODE_OUTPUTS.copy(), ["code"], PRIMARY_CODE_GATES.copy(), False, True')
# result-analysis code is downstream of an already accepted primary result and does not retroactively require model approval
s = s.replace('ANALYSIS_CODE_OUTPUTS.copy(), ["code"], SEMANTIC_CODE_GATES.copy(), False, True', 'ANALYSIS_CODE_OUTPUTS.copy(), ["code"], ANALYSIS_CODE_GATES.copy(), False, True')
assert 'SEMANTIC_CODE_GATES' not in s
p.write_text(s, encoding='utf-8')
print('gate split applied')
