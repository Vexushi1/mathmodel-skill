"""Synthetic B1 record helpers, not user claims or approvals."""
from copy import deepcopy
from pathlib import Path
import io
import sys
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

def source(identifier='baseline',scenario='baseline',**kwargs):
    item={'id':identifier,'question':'Q1','stage':'primary','artifact_role':'solution_workbook',
       'selector':{'sheet':'measurements','header_row':1,'row_key':{'metric':'cost','scenario':scenario},
       'expected_cardinality':1,'value_type':'scalar','value_column':'value',
       'identity_columns':{'metric':'metric','scenario':'scenario','sample':'sample'},'unit':{'kind':'column','column':'unit'}}}
    item.update(kwargs);return item

def record():
    return {'protocol_version':'1.0.0','sources':[source(),source('candidate','candidate')],
      'derivations':[{'id':'gain','op':'improvement','direction':'lower','comparison_axis':'scenario',
        'inputs':{'baseline':'source:baseline','candidate':'source:candidate'}}],
      'claims':[{'id':'gain_claim','scope':'Q1','kind':'comparative','text':'Synthetic relative decrease is 0.2.',
        'evidence':[{'ref':'derivation:gain','relation':'supports'}],
        'assertion':{'evidence_ref':'derivation:gain','value':'0.2','unit':'ratio'}}]}

def workbook(rows=None,headers=None,mutate=None):
    book=openpyxl.Workbook();sheet=book.active;sheet.title='measurements'
    sheet.append(headers or ['metric','scenario','sample','value','unit'])
    for row in (rows if rows is not None else [['cost','baseline','S1',100,'kg'],['cost','candidate','S1',80,'kg']]):sheet.append(row)
    if mutate:mutate(book)
    output=io.BytesIO();book.save(output);book.close();return output.getvalue()

def answer_record(stage='primary'):
    # Actual original fixture outputs. The metric/unit profile is explicit test metadata.
    selector={'sheet':'核心指标','header_row':1,'row_key':{'指标':'解'},'expected_cardinality':1,
      'value_type':'scalar','value_column':'数值','identity_columns':{'metric':'指标'},
      'unit':{'kind':'numeric_profile','profile_id':'N99'}}
    if stage=='analysis':
        selector={'sheet':'参数敏感性','header_row':1,'row_key':{'变化值':2},'expected_cardinality':1,
          'value_type':'scalar','value_column':'结果指标','identity_columns':{'metric':'参数','scenario':'变化值','sample':'基准值'},
          'unit':{'kind':'numeric_profile','profile_id':'N98'}}
    return {'protocol_version':'1.0.0','sources':[{'id':'answer','question':'Q1','stage':stage,
        'artifact_role':'solution_workbook' if stage=='primary' else 'result_analysis_workbook','selector':selector}],
      'derivations':[],'claims':[{'id':'answer_claim','scope':'Q1','kind':'computational','text':'Synthetic scalar equation result.',
      'evidence':[{'ref':'source:answer','relation':'supports'}],'assertion':{'evidence_ref':'source:answer','value':'4','unit':'ratio'}}]}

def install_record(state,stage='primary'):
    state.setdefault('paper_framework',{})['numeric_profile']=[
       {'id':'N99','metric':'解','unit':'ratio','display_form':'decimal','status':'current'},
       {'id':'N98','metric':'a','unit':'ratio','display_form':'decimal','status':'current'}]
    state['paper_framework']['claim_evidence']=answer_record(stage)
    return state
