#!/usr/bin/env python3
"""Explicit read-only B1 claim-source/selection/arithmetic inspection.

An evidence_checked result concerns declared records only. It does not establish
mathematical truth, significance, causality, optimality or independent review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from typing import Any, Mapping
import yaml
from jsonschema import Draft202012Validator, validators
import model_code_conformance as bounded
from claim_values import EvidenceError, NeedsReview, Value, number, converted, derive, describe, unit_info
from claim_workbook import Workbook, current_profile
from claim_sources import Sources, QualificationError, CONTRACT, ROOT
from project_transaction import JOURNAL_RELATIVE_PATH

SCHEMA='core/project_state.schema.yaml'
EXIT_CODES={'evidence_checked':0,'blocked':1,'needs_review':2,'not_assessed':2}
RecordValidator=validators.extend(Draft202012Validator,type_checker=
    Draft202012Validator.TYPE_CHECKER.redefine('integer',lambda _checker,value:type(value) is int))

def validate_record(record: Any, schema: dict, contract: dict) -> list[dict]:
    limits=contract['limits']
    if type(record) is dict and sum(len(record[key]) for key in ('sources','derivations','claims')
                                     if type(record.get(key)) is list)>limits['graph_nodes']:
        raise EvidenceError('total graph node budget exceeded')
    validator=RecordValidator({'$ref':'#/$defs/claim_evidence','$defs':schema['$defs']})
    error=next(validator.iter_errors(record),None)
    if error is not None:
        raise EvidenceError('record schema: '+ '/'.join(map(str,error.absolute_path)) + ': '+error.message[:4096])
    namespaces={kind:{item['id']:item for item in record[kind]} for kind in ('sources','derivations','claims')}
    if any(len(namespaces[k])!=len(record[k]) for k in namespaces):
        raise EvidenceError('duplicate stable ID within a namespace')
    for source in record['sources']:
        select=source['selector']
        if type(select['header_row']) is not int or type(select['expected_cardinality']) is not int:
            raise EvidenceError('selector indexes require strict integers')
    refs={**{'source:'+k:v for k,v in namespaces['sources'].items()},
          **{'derivation:'+k:v for k,v in namespaces['derivations'].items()}}
    edges:dict[str,list[str]]={};count=0
    for key,node in namespaces['derivations'].items():
        inputs=node['inputs'];values=inputs.get('items',list(inputs.values()))
        if len(values)!=len(set(values)):raise EvidenceError('duplicate derivation input reference')
        if any(x not in refs for x in values):raise EvidenceError('unknown derivation reference')
        edges['derivation:'+key]=values;count+=len(values)
    for claim in record['claims']:
        names=[edge['ref'] for edge in claim['evidence']]
        if len(names)!=len(set(names)) or any(x not in refs for x in names):
            raise EvidenceError('duplicate or unknown claim evidence')
        if 'assertion' in claim and claim['assertion']['evidence_ref'] not in names:
            raise EvidenceError('assertion is not linked to the claim evidence list')
        count+=len(names)
    if count>limits['graph_edges']:raise EvidenceError('graph edge budget exceeded')
    order=[];visiting=set();complete=set();depths={}
    def visit(ref: str) -> int:
        if ref.startswith('source:'):return 0
        if ref in visiting:raise EvidenceError('cyclic derivation graph')
        if ref in complete:return depths[ref]
        if len(visiting)>=limits['derivation_depth']:raise EvidenceError('derivation depth budget exceeded')
        visiting.add(ref)
        depth=1+max((visit(x) for x in edges[ref]),default=0)
        if depth>limits['derivation_depth']:raise EvidenceError('derivation depth budget exceeded')
        visiting.remove(ref);complete.add(ref);depths[ref]=depth;order.append(refs[ref]);return depth
    for ref in edges:visit(ref)
    return order

def _assertion(claim: dict, value: Value, profiles: list, contract: dict) -> dict:
    asserted=claim['assertion'];profile=None
    if claim.get('numeric_profile_id'):
        profile=current_profile(profiles,claim['numeric_profile_id'],value.identity['metric'])
    if 'display_location' in asserted:
        if profile is None:raise EvidenceError('display comparison requires a current linked Numeric Profile')
        form=profile['display_form']
        if ((value.kind=='scalar' and form not in ('decimal','percent','scientific','integer'))
                or (value.kind!='scalar' and form!=value.kind)):
            raise EvidenceError('Numeric Profile display form conflicts with the selected value type')
        if profile.get('unit')!=asserted['unit']:
            raise EvidenceError('assertion unit differs from Numeric Profile')
        if form=='percent' and unit_info(asserted['unit'],contract)[2]!='percent':
            raise EvidenceError('percent display requires an explicit percent quantity, not a ratio or points')
    if value.kind=='categorical':
        if asserted['unit']!='not_applicable' or not isinstance(asserted['value'],str):
            raise EvidenceError('categorical assertions require text and a not-applicable unit')
        if asserted['value']!=value.value:raise EvidenceError('categorical assertion conflicts with selected value')
        return {'status':'matched','comparison':'exact_categorical'}
    if value.kind=='interval':
        if not isinstance(asserted['value'],list) or len(asserted['value'])!=2:
            raise EvidenceError('interval assertions require two explicit endpoints')
        if asserted['unit']!=value.unit:raise NeedsReview('interval unit conversion is not implemented')
        expected=list(value.value)
        actual=[number(x,contract) for x in asserted['value']]
    else:
        checked=converted(value,asserted['unit'],contract)
        expected=[checked.value];actual=[number(asserted['value'],contract)]
    mode='raw_decimal'
    if 'display_location' in asserted:
        if profile is None:raise EvidenceError('display comparison requires a current linked Numeric Profile')
        if profile.get('unit')!=asserted['unit']:raise EvidenceError('assertion unit differs from Numeric Profile')
        places=profile.get(asserted['display_location']+'_decimals')
        if type(places) is not int or not 0<=places<=contract['limits']['profile_decimals']:
            raise EvidenceError('profile decimal precision is absent, noninteger or exceeds budget')
        if profile['display_form']=='integer' and places!=0:
            raise EvidenceError('integer display requires zero decimal places')
        with localcontext() as ctx:
            ctx.prec=contract['limits']['decimal_precision']
            expected=[x.quantize(Decimal(1).scaleb((x.adjusted() if x else 0)-places
                      if profile.get('display_form')=='scientific' else -places),rounding=ROUND_HALF_EVEN) for x in expected]
        mode='declared_'+asserted['display_location']+'_profile'
    if actual!=expected:raise EvidenceError('asserted value conflicts with observed/derived evidence under '+mode)
    return {'status':'matched','comparison':mode,'compared_values':[str(x) for x in expected],'unit':asserted['unit']}

def evaluate(record: dict,order: list,selected: Mapping[str,Value],profiles: list,titles: list,
             contract: dict,source_scopes: Mapping[str,set[str]]) -> tuple[list,list]:
    values=dict(selected);scopes=dict(source_scopes);derivations=[];claims=[]
    for node in order:
        key='derivation:'+node['id'];row={'id':node['id'],'arithmetic_status':'not_assessed'}
        try:
            inputs=node['inputs']
            args=({'items':[values[x] for x in inputs['items']]} if 'items' in inputs else {k:values[v] for k,v in inputs.items()})
            values[key]=derive(node,args,contract)
            input_refs=inputs.get('items',list(inputs.values()))
            scopes[key]=set().union(*(scopes[x] for x in input_refs))
            row.update(arithmetic_status='checked',**describe(values[key]))
        except KeyError:
            row.update(arithmetic_status='needs_review',reason='input evidence is unavailable or unqualified')
        except NeedsReview as exc:
            row.update(arithmetic_status='needs_review',reason=str(exc))
        except (EvidenceError,DecimalException) as exc:
            row.update(arithmetic_status='blocked',reason=str(exc))
        derivations.append(row)
    for claim in record['claims']:
        row={'id':claim['id'],'scope':claim['scope'],'kind':claim['kind'],'semantic_support':'not_established',
             'evidence_relations':'author_declared_not_proved','arithmetic_status':'not_requested'}
        try:
            names=[x['ref'] for x in claim['evidence']]
            if any(x not in values for x in names):raise NeedsReview('some declared evidence is not available')
            scope=set().union(*(scopes[x] for x in names))
            if claim['scope']!='project' and scope!={claim['scope']}:
                raise EvidenceError('claim scope differs from evidence question scope')
            if claim.get('title_claim_id'):
                matches=[x for x in titles if isinstance(x,dict) and x.get('id')==claim['title_claim_id']]
                if len(matches)!=1 or matches[0].get('status')!='current':
                    raise EvidenceError('title claim reference is missing, duplicate or not current')
            if claim.get('numeric_profile_id'):
                for name in names:current_profile(profiles,claim['numeric_profile_id'],values[name].identity['metric'])
            if 'assertion' in claim:
                row['assertion_check']=_assertion(claim,values[claim['assertion']['evidence_ref']],profiles,contract)
                row['arithmetic_status']='checked'
            row['evidence_status']='linked'
        except NeedsReview as exc:
            row.update(arithmetic_status='needs_review',reason=str(exc))
        except (EvidenceError,DecimalException) as exc:
            row.update(arithmetic_status='blocked',reason=str(exc))
        claims.append(row)
    return derivations,claims

def inspect_project(project_root: str|Path) -> dict:
    root=Path(project_root).expanduser().resolve()
    report={'status':'not_assessed','source_qualification':'not_assessed','selection_status':'not_assessed',
            'arithmetic_status':'not_assessed','semantic_support':'not_established','independent_review':'not_run',
            'execution_authorized':False,'coverage':'declared_records_only_not_all_paper_claims',
            'sources':[],'derivations':[],'claims':[],'errors':[],'revalidation_guidance':[]}
    observation={'project':{},'skill':{}};adapter=None
    try:
        journal=root/JOURNAL_RELATIVE_PATH
        if journal.exists() or journal.is_symlink():raise EvidenceError('pending transaction requires explicit recovery')
        raw=bounded._read(root,'state/project_state.yaml',2*1024*1024,observation['project'])
        state=bounded._yaml(raw.decode('utf-8'),32)
        if not isinstance(state,dict):raise EvidenceError('project state must be a mapping')
        framework=state.get('paper_framework',{})
        if not isinstance(framework,dict):raise EvidenceError('paper_framework must be a mapping')
        if 'claim_evidence' not in framework:
            report['reason']='No B1 record. No workbook or Claim Authority was loaded.'
            return report
        contract=bounded._yaml(bounded._read(ROOT,CONTRACT,2*1024*1024,observation['skill']).decode('utf-8'),32)
        schema=yaml.safe_load(bounded._read(ROOT,SCHEMA,2*1024*1024,observation['skill']).decode('utf-8'))
        if contract.get('version')!='1.0.0':raise EvidenceError('unsupported Claim Authority version')
        record=framework['claim_evidence'];order=validate_record(record,schema,contract)
        adapter=Sources(root,raw,state,contract)
        # Preserve the exact authority bytes used for schema/operation decisions.
        from conformance_gate import merge_read_sets
        merge_read_sets(adapter.read_set,observation)
        values={};source_scopes={};readers={};guidance_seen=set()
        profiles=framework.get('numeric_profile',[]);titles=framework.get('title_claims',[])
        for source in record['sources']:
            key='source:'+source['id'];row={'id':source['id'],'source_qualification':'not_assessed','selection_status':'not_assessed'}
            try:
                data,qualified=adapter.qualify(source);row.update(qualified)
            except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
                row.update(source_qualification='blocked',selection_status='blocked',reason=str(exc))
                scope=(source['question'],source['stage'])
                if isinstance(exc, QualificationError) and scope not in guidance_seen:
                    report['revalidation_guidance'].extend(adapter.revalidation_guidance(*scope));guidance_seen.add(scope)
                report['sources'].append(row);continue
            try:
                digest=qualified['sha256']
                if digest not in readers:readers[digest]=Workbook(data,contract)
                value,location=readers[digest].select(source['selector'],profiles)
                values[key]=value;source_scopes[key]={source['question']}
                row.update(selection_status='selected',**describe(value),**location)
            except NeedsReview as exc:
                row.update(selection_status='needs_review',reason=str(exc))
            except (EvidenceError,ValueError,TypeError,KeyError,OverflowError) as exc:
                row.update(selection_status='blocked',reason=str(exc))
            report['sources'].append(row)
        report['derivations'],report['claims']=evaluate(record,order,values,profiles,titles,contract,source_scopes)
        selections=[x['selection_status'] for x in report['sources']]
        arithmetic=[x['arithmetic_status'] for x in report['derivations']+report['claims']]
        report['source_qualification']='verified' if all(x['source_qualification']=='verified' for x in report['sources']) else 'blocked'
        report['selection_status']='selected' if all(x=='selected' for x in selections) else ('blocked' if 'blocked' in selections else 'needs_review')
        report['arithmetic_status']=('blocked' if 'blocked' in arithmetic else 'needs_review' if 'needs_review' in arithmetic
                                     else 'checked' if 'checked' in arithmetic else 'not_requested')
        report['status']=('blocked' if 'blocked' in (*selections,*arithmetic) else
                          'needs_review' if 'needs_review' in (*selections,*arithmetic) else 'evidence_checked')
        report['decimal_precision']=contract['limits']['decimal_precision']
        report['observed_sources']=adapter.read_set
    except (OSError,ValueError,TypeError,KeyError,AttributeError,RecursionError,yaml.YAMLError) as exc:
        report['status']='blocked';report['errors'].append(str(exc)[:4096])
    finally:
        try:
            if adapter is not None:adapter.assert_current()
            else:
                bounded._recheck(root,observation['project']);bounded._recheck(ROOT,observation['skill'])
        except (OSError,ValueError,RuntimeError) as exc:
            report['status']='blocked';report['errors'].append('read-set conflict: '+str(exc)[:4096])
    return report

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_root',type=Path)
    args=parser.parse_args()
    report=inspect_project(args.project_root)
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    return EXIT_CODES[report['status']]

if __name__=='__main__':raise SystemExit(main())
