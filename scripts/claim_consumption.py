#!/usr/bin/env python3
"""B2 opt-in, read-only claim consumption inspection of static LaTeX sources.

Locations and number comparisons are observations, never semantic proof, a
formal paper gate, a stale-state writer, or permission to requalify workbooks.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator

import claim_evidence
from claim_sources import ROOT
from claim_tex import scan_static_latex, source_location
from claim_values import EvidenceError, NeedsReview, Value, converted
from claim_workbook import current_profile
from conformance_gate import merge_read_sets
import model_code_conformance as bounded
from project_transaction import JOURNAL_RELATIVE_PATH
from validate_project_state import _validate_claim_consumption_policy, _validate_paper_fragments


STATE = 'state/project_state.yaml'
FRAMEWORK = '模型论文框架.md'
CONTRACT = 'core/claim_consumption_contract.yaml'
SCHEMA = 'core/project_state.schema.yaml'
CLAIM_CONTRACT = 'core/claim_evidence_contract.yaml'
FRAGMENT_HEADER = '### Paper Fragment Dependency Map'
NUMBER = re.compile(r'(?<![\w.])[-+−]?(?:\d+(?:[.,]\d+)?|\.\d+)(?:[eE][-+−]?\d+)?(?!\w|\.\d)')
GLOBAL_OPTIMAL = re.compile(r'全局最优|global(?:ly)?\s+optimal|global\s+optimum', re.I)
BROAD_ROBUST = re.compile(r'广泛稳健|全面稳健|(?:robust|stable)\s+(?:under|across)\s+all', re.I)
EXIT = {'observed': 0, 'blocked': 1, 'needs_review': 2, 'not_assessed': 2}


def _report() -> dict:
    return {'status': 'not_assessed', 'mode': None, 'policy_protocol_version': None,
            'execution_authorized': False,
            'semantic_support': 'not_established', 'human_semantic_coverage': 'not_assessed',
            'formal_delivery_gate': 'not_run', 'b1_status': 'not_assessed',
            'fragment_locations': [], 'registered_location_gaps': [], 'required_coverage': [], 'numeric_checks': [],
            'unregistered_candidates': [], 'wording_findings': [],
            'suggested_stale_fragment_ids': [], 'stale_reason_paths': [],
            'errors': [], 'issues': [], 'observed_sources': {'project': {}, 'skill': {}}}


def _read_yaml(root: Path, relative: str, limit: int, target: dict) -> tuple[bytes, Any]:
    raw = bounded._read(root, relative, limit, target)
    return raw, bounded._yaml(raw.decode('utf-8-sig'), 32)


def _clean_cell(value: str) -> str:
    value = value.strip()
    return value[1:-1].strip() if len(value) >= 2 and value.startswith('`') and value.endswith('`') else value


def _framework_rows(text: str) -> list[dict]:
    if text.count(FRAGMENT_HEADER) != 1:
        raise EvidenceError('framework requires exactly one Paper Fragment Dependency Map')
    section = text.split(FRAGMENT_HEADER, 1)[1]
    section = re.split(r'(?m)^#{1,4}\s+', section, maxsplit=1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith('|'):
            continue
        cells = [part.strip() if index == 3 else _clean_cell(part)
                 for index, part in enumerate(line.strip().strip('|').split('|'))]
        if not cells or cells[0] in ('Fragment ID', '') or re.fullmatch(r'-+', cells[0]):
            continue
        if len(cells) != 7:
            raise EvidenceError('framework fragment row must have seven columns')
        cells[3] = ','.join(_clean_cell(part) for part in re.split(r'[,，;；]', cells[3]) if part.strip())
        rows.append(dict(zip(('id', 'kind', 'scope', 'depends_on', 'anchor', 'source_file', 'status'), cells)))
    if len({row['id'] for row in rows}) != len(rows):
        raise EvidenceError('duplicate framework fragment ID')
    return rows


def _check_projection(framework: Mapping[str, Any], text: str) -> None:
    state_rows = framework.get('paper_fragments', [])
    if not isinstance(state_rows, list):
        raise EvidenceError('paper_fragments must be a list')
    by_id = {row.get('id'): row for row in state_rows if isinstance(row, dict)}
    if len(by_id) != len(state_rows):
        raise EvidenceError('duplicate or malformed State fragment ID')
    rows = _framework_rows(text)
    if set(by_id) != {row['id'] for row in rows}:
        raise EvidenceError('State and Framework fragment ID sets differ')
    for row in rows:
        state = by_id[row['id']]
        expected = {key: _clean_cell(str(state.get(key, '')))
                    for key in ('id', 'kind', 'scope', 'anchor', 'source_file', 'status')}
        if any(row[key] != expected[key] for key in expected):
            raise EvidenceError(f"State and Framework fragment row differ: {row['id']}")
        raw_deps = [item.strip() for item in re.split(r'[,，;；]', row['depends_on']) if item.strip()]
        state_deps = state.get('depends_on', [])
        if len(raw_deps) != len(set(raw_deps)) or set(raw_deps) != set(state_deps):
            raise EvidenceError(f"State and Framework fragment dependencies differ: {row['id']}")


def _locations(fragments: list[dict], scan: dict) -> list[dict]:
    body = [item for item in scan['segments'] if item['in_document']]
    located = []
    for fragment in fragments:
        row = {'id': fragment['id'], 'kind': fragment['kind'], 'scope': fragment['scope'],
               'status': 'not_assessed', 'source_file': fragment.get('source_file'),
               'fragment_status': fragment['status']}
        path, anchor = fragment.get('source_file'), fragment.get('anchor')
        if not path or not anchor:
            row['reason'] = 'source_file and nonempty anchor are required for static location'
        elif path not in scan['files'] or path not in scan['active_files']:
            row['reason'] = 'source_file is not in the proven active include graph'
        else:
            masked = scan['files'][path]['masked']
            hits = [match.start() for match in re.finditer(re.escape(anchor), masked)
                    if any(segment['path'] == path and segment['start'] <= match.start()
                           and match.end() <= segment['end'] for segment in body)]
            if len(hits) != 1:
                row['reason'] = 'anchor is absent or ambiguous in active document text'
            else:
                offset = hits[0]
                segment = next(item for item in body if item['path'] == path
                               and item['start'] <= offset < item['end'])
                row.update(status='located', offset=offset, segment_end=segment['end'],
                           **source_location(scan['files'], path, offset))
        located.append(row)
    positions: dict[tuple[str, int], list[dict]] = {}
    for row in located:
        if row['status'] == 'located':
            positions.setdefault((row['source_file'], row['offset']), []).append(row)
    for group in positions.values():
        if len(group) > 1:
            for row in group:
                row.update(status='not_assessed', reason='multiple fragments share one source anchor position')
    for row in located:
        if row['status'] != 'located':
            continue
        later = [other['offset'] for other in located if other['status'] == 'located'
                 and other['source_file'] == row['source_file']
                 and row['offset'] < other['offset'] < row['segment_end']]
        row['end_offset'] = min(later, default=row['segment_end'])
    return located


def _fragment_text(scan: dict, row: dict) -> str:
    return scan['files'][row['source_file']]['masked'][row['offset']:row['end_offset']]


def _numeric_tokens(text: str) -> list[tuple[Decimal, str, str]]:
    tokens = []
    for match in NUMBER.finditer(text):
        literal = match.group().replace(',', '').replace('−', '-')
        try:
            number = Decimal(literal)
        except DecimalException:
            continue
        after = text[match.end():match.end() + 40]
        if after.startswith('\\%') or after.startswith('%'):
            unit = 'percent'
        elif (re.match(r'^\s*\\[,;:!]\s*\\%', after)
              or re.match(r'^}\s*{\s*\\percent\b', after)
              or re.match(r'^\s*(?:percent|百分比)\b', after, re.I)):
            unit = 'ambiguous_percent_notation'
        else:
            unit = 'plain'
        tokens.append((number, unit, literal))
    return tokens


def _expected_number(claim: dict, b1: dict, state: dict, claim_contract: dict,
                     location: str) -> tuple[Decimal, str, str, int | None]:
    asserted = claim['assertion']
    ref = asserted['evidence_ref']
    kind, identifier = ref.split(':', 1)
    rows = b1['sources'] if kind == 'source' else b1['derivations']
    matches = [row for row in rows if row.get('id') == identifier]
    if len(matches) != 1 or matches[0].get('value_type') != 'scalar':
        raise NeedsReview('scalar original evidence is unavailable for this location')
    item = matches[0]
    value = Value('scalar', Decimal(str(item['value'])), item['unit'], item['identity'],
                  frozenset(item.get('physical_sources', [])))
    profile_id = claim.get('numeric_profile_id')
    if not profile_id:
        return converted(value, asserted['unit'], claim_contract).value, 'plain', 'raw', None
    profile = current_profile(state['paper_framework'].get('numeric_profile', []),
                              profile_id, item['identity']['metric'])
    target = converted(value, profile['unit'], claim_contract)
    places = profile.get(location + '_decimals')
    if type(places) is not int or not 0 <= places <= claim_contract['limits']['profile_decimals']:
        raise NeedsReview('location-specific Numeric Profile precision is missing')
    if profile['display_form'] not in ('decimal', 'integer', 'scientific', 'percent'):
        raise NeedsReview('non-scalar display form is outside this text scanner')
    with localcontext() as context:
        context.prec = claim_contract['limits']['decimal_precision']
        exponent = ((target.value.adjusted() if target.value else 0) - places
                    if profile['display_form'] == 'scientific' else -places)
        expected = target.value.quantize(Decimal(1).scaleb(exponent), rounding=ROUND_HALF_EVEN)
    return expected, 'percent' if profile['display_form'] == 'percent' else 'plain', profile['display_form'], places


def _literal_matches_profile(literal: str, form: str, places: int | None) -> bool:
    if ',' in literal:
        return False  # Thousands/decimal comma is locale dependent without an explicit format protocol.
    mantissa, separator, _ = literal.lower().partition('e')
    decimals = len(mantissa.partition('.')[2]) if '.' in mantissa else 0
    if form == 'raw':
        return True
    if form == 'scientific':
        return bool(separator) and decimals == places
    if separator:
        return False
    if form == 'integer':
        return '.' not in mantissa and places == 0
    return decimals == places


def _suggested_stale(state: dict, fragments: list[dict], claims: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    by_id = {row['id']: row for row in fragments}
    claim_by_id = {row['id']: row for row in claims}
    text_to_ids: dict[str, list[str]] = {}
    for row in claims:
        text_to_ids.setdefault(row['text'], []).append(row['id'])
    suggestions, paths, issues = set(), [], []
    for question, entry in state.get('subproblems', {}).items():
        for disposition in entry.get('analysis_evidence_dispositions', []) or []:
            if disposition.get('status', 'current') != 'current' or disposition.get('disposition') not in ('modify', 'reject'):
                continue
            target = disposition.get('target_claim', '')
            claim_ids = ([target] if target in claim_by_id else text_to_ids.get(target, []))
            if len(claim_ids) != 1:
                issues.append(f"{question}/{disposition.get('id')}: disposition target cannot be linked to one B1 claim")
                continue
            queue = [(row['id'], ['claim:' + claim_ids[0], row['id']]) for row in fragments
                     if 'claim:' + claim_ids[0] in row.get('depends_on', [])]
            seen = set()
            while queue:
                fragment_id, path = queue.pop(0)
                if fragment_id in seen:
                    continue
                seen.add(fragment_id)
                suggestions.add(fragment_id)
                paths.append({'disposition_id': disposition['id'], 'question': question,
                              'disposition': disposition['disposition'], 'path': path})
                queue.extend((row['id'], path + [row['id']]) for row in fragments
                             if row['id'] not in seen and fragment_id in row.get('depends_on', []))
    return sorted(suggestions), paths, issues


def inspect_project(project_root: str | Path, *, tex_main: str | Path = 'final_latex/main.tex') -> dict:
    root = Path(project_root).expanduser().resolve()
    report = _report()
    observed = report['observed_sources']
    try:
        if (root / JOURNAL_RELATIVE_PATH).exists() or (root / JOURNAL_RELATIVE_PATH).is_symlink():
            raise EvidenceError('pending project transaction requires recovery')
        _, state = _read_yaml(root, STATE, 2 * 1024 * 1024, observed['project'])
        if not isinstance(state, dict) or not isinstance(state.get('paper_framework'), dict):
            raise EvidenceError('project state or paper framework is malformed')
        framework = state['paper_framework']
        if 'claim_consumption_policy' not in framework:
            report['reason'] = 'No B2 opt-in policy; original routes remain unchanged.'
            return report
        _, contract = _read_yaml(ROOT, CONTRACT, 2 * 1024 * 1024, observed['skill'])
        schema = yaml.safe_load(bounded._read(ROOT, SCHEMA, 2 * 1024 * 1024, observed['skill']).decode('utf-8'))
        _, claim_contract = _read_yaml(ROOT, CLAIM_CONTRACT, 2 * 1024 * 1024, observed['skill'])
        for path in ('scripts/claim_consumption.py', 'scripts/claim_tex.py',
                     'scripts/validate_project_state.py'):
            bounded._read(ROOT, path, 2 * 1024 * 1024, observed['skill'])
        if contract.get('version') != '1.1.0':
            raise EvidenceError('unsupported B2 contract version')
        policy = framework['claim_consumption_policy']
        if isinstance(policy, Mapping):
            report['mode'] = policy.get('mode') if isinstance(policy.get('mode'), str) else None
            report['policy_protocol_version'] = (policy.get('protocol_version')
                                                 if isinstance(policy.get('protocol_version'), str) else None)
        validator = Draft202012Validator({'$ref': '#/$defs/claim_consumption_policy', '$defs': schema['$defs']})
        error = next(validator.iter_errors(policy), None)
        if error:
            raise EvidenceError('B2 policy schema: ' + error.message[:4096])
        issues = _validate_claim_consumption_policy(framework)
        fragment_issues, _ = _validate_paper_fragments(framework)
        issues.extend(fragment_issues)
        if issues:
            raise EvidenceError('B2 policy relations: ' + '; '.join(issues[:8]))
        if 'claim_evidence' not in framework:
            raise EvidenceError('B2 policy requires an explicit B1 claim record')
        fragment_validator = Draft202012Validator({'$ref': '#/$defs/paper_fragment_entry', '$defs': schema['$defs']})
        for index, fragment in enumerate(framework.get('paper_fragments', [])):
            error = next(fragment_validator.iter_errors(fragment), None)
            if error:
                raise EvidenceError(f'paper fragment {index} schema: ' + error.message[:4096])
        raw = bounded._read(root, FRAMEWORK, 2 * 1024 * 1024, observed['project'])
        framework_text = raw.decode('utf-8-sig')
        normalized = framework_text.replace('\r\n', '\n').replace('\r', '\n')
        expected_hash = framework.get('sha256')
        if expected_hash and expected_hash.lower() != hashlib.sha256(normalized.encode('utf-8')).hexdigest():
            raise EvidenceError('paper_framework.sha256 does not match current Framework bytes')
        _check_projection(framework, framework_text)
        b1 = claim_evidence.inspect_project(root)
        report['b1_status'] = b1['status']
        if 'observed_sources' in b1:
            merge_read_sets(observed, b1['observed_sources'])
        if b1['status'] != 'evidence_checked':
            report['status'] = 'blocked' if b1['status'] == 'blocked' else 'needs_review'
            report['issues'].append('live B1 source qualification or assertion check is not evidence_checked')
            report['b1_errors'] = b1.get('errors', [])
            return report
        scan = scan_static_latex(root, Path(tex_main))
        for path, entry in scan['files'].items():
            merge_read_sets(observed, {'project': {path: entry['sha256']}})
        report['tex_scan'] = {'status': scan['status'], 'active_files': scan['active_files'],
                              'issues': scan['issues'],
                              'scope': 'literal_static_include_source_only_no_macro_expansion_or_pdf'}
        if scan['status'] != 'scanned':
            report['status'] = scan['status']
            return report
        fragments = framework.get('paper_fragments', [])
        locations = _locations(fragments, scan)
        report['fragment_locations'] = [{key: value for key, value in row.items()
                                         if key not in ('offset', 'end_offset', 'segment_end')}
                                        for row in locations]
        by_id = {row['id']: row for row in locations}
        report['registered_location_gaps'] = [item['id'] for item in fragments
            if any(dep.startswith('claim:') for dep in item['depends_on'])
            and by_id[item['id']]['status'] != 'located']
        claims = framework['claim_evidence']['claims']
        claim_by_id = {row['id']: row for row in claims}
        gaps = False
        for obligation in policy['required_consumptions']:
            for kind in obligation['fragment_kinds']:
                linked = [item for item in fragments if item['kind'] == kind
                          and 'claim:' + obligation['claim_id'] in item['depends_on']]
                located = [item['id'] for item in linked if by_id[item['id']]['status'] == 'located'
                           and item['status'] == 'current']
                status = 'located' if located else 'gap'
                gaps |= status == 'gap'
                report['required_coverage'].append({'claim_id': obligation['claim_id'],
                    'fragment_kind': kind, 'status': status, 'fragment_ids': located,
                    'registered_fragment_ids': [item['id'] for item in linked]})
        for fragment in fragments:
            location = by_id[fragment['id']]
            if location['status'] != 'located':
                continue
            prose = _fragment_text(scan, location)
            linked_ids = [dep.split(':', 1)[1] for dep in fragment['depends_on'] if dep.startswith('claim:')]
            scopes = ({fragment['scope']} if fragment['scope'] in state.get('subproblems', {}) else
                      {claim_by_id[claim_id]['scope'] for claim_id in linked_ids
                       if claim_by_id[claim_id]['scope'] in state.get('subproblems', {})})
            for scope in sorted(scopes):
                subproblem = state['subproblems'][scope]
                if subproblem.get('optimality_claim') in ('heuristic', 'local', 'bounded', 'none') and GLOBAL_OPTIMAL.search(prose):
                    report['wording_findings'].append({'fragment_id': fragment['id'], 'question': scope,
                        'code': 'global_optimality_exceeds_registered_status', 'status': 'needs_review'})
                if subproblem.get('result_analysis_status') == 'not_required' and BROAD_ROBUST.search(prose):
                    report['wording_findings'].append({'fragment_id': fragment['id'], 'question': scope,
                        'code': 'broad_robustness_without_required_analysis', 'status': 'needs_review'})
            if len(linked_ids) > 1:
                report['numeric_checks'].append({'fragment_id': fragment['id'], 'status': 'not_assessed',
                    'reason': 'multiple linked claims need explicit numeric attribution'})
                continue
            if not linked_ids:
                continue
            claim = claim_by_id[linked_ids[0]]
            if 'assertion' not in claim:
                continue
            if fragment['kind'] == 'figure_or_table_claim':
                report['numeric_checks'].append({'claim_id': claim['id'], 'fragment_id': fragment['id'],
                    'status': 'not_assessed', 'reason': 'figure/table caption location and display profile need a later protocol'})
                continue
            location_kind = 'abstract' if fragment['kind'] == 'abstract_claim' else 'body'
            check = {'claim_id': claim['id'], 'fragment_id': fragment['id'],
                     'source_file': location['source_file'], 'line': location['line'],
                     'status': 'not_assessed'}
            try:
                expected, expected_unit, form, places = _expected_number(
                    claim, b1, state, claim_contract, location_kind)
                tokens = _numeric_tokens(prose)
                if len(tokens) == 1:
                    observed_value, observed_unit, literal = tokens[0]
                    if ',' in literal:
                        check.update(status='needs_review', reason='comma numeric notation has no declared locale')
                    elif observed_unit != expected_unit:
                        check.update(status='needs_review', reason='literal unit notation needs human attribution')
                    elif observed_value != expected:
                        check['status'] = 'conflict'
                    elif _literal_matches_profile(literal, form, places):
                        check['status'] = 'matched'
                    else:
                        check.update(status='needs_review', reason='literal form or precision differs from Numeric Profile')
                    check.update(observed_value=str(observed_value), expected_value=str(expected),
                                 display_form=form, display_places=places)
                elif len(tokens) == 0:
                    check.update(status='needs_review', reason='no scalar literal located in fragment span')
                else:
                    check.update(status='needs_review', reason='multiple numeric literals require human attribution')
            except (EvidenceError, DecimalException, KeyError, ValueError) as exc:
                check.update(status='needs_review', reason=str(exc)[:512])
            report['numeric_checks'].append(check)
        suggestions, paths, unresolved = _suggested_stale(state, fragments, claims)
        report['suggested_stale_fragment_ids'] = suggestions
        report['stale_reason_paths'] = paths
        report['issues'].extend(unresolved)
        matched_ids = {row['fragment_id'] for row in report['numeric_checks'] if row['status'] == 'matched'}
        checked_spans = [(row['source_file'], row['offset'], row['end_offset']) for row in locations
                         if row['status'] == 'located' and row['id'] in matched_ids]
        for segment in scan['segments']:
            if not segment['in_document']:
                continue
            path = segment['path']
            masked = scan['files'][path]['masked']
            for match in NUMBER.finditer(masked, segment['start'], segment['end']):
                if any(p == path and start <= match.start() < end for p, start, end in checked_spans):
                    continue
                if len(report['unregistered_candidates']) >= 100:
                    break
                report['unregistered_candidates'].append({'source_file': path,
                    **source_location(scan['files'], path, match.start()),
                    'literal': match.group(), 'status': 'candidate_needs_review'})
        if any(row['status'] == 'conflict' for row in report['numeric_checks']):
            report['status'] = 'blocked'
        elif (gaps or report['registered_location_gaps'] or suggestions or
              report['wording_findings'] or report['issues'] or
              any(row['status'] in ('needs_review', 'not_assessed') for row in report['numeric_checks']) or
              report['unregistered_candidates']):
            report['status'] = 'needs_review'
        else:
            report['status'] = 'observed'
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
        report['status'] = 'blocked'
        report['errors'].append(str(exc)[:4096])
    finally:
        try:
            if (root / JOURNAL_RELATIVE_PATH).exists() or (root / JOURNAL_RELATIVE_PATH).is_symlink():
                raise EvidenceError('pending project transaction appeared during inspection')
            bounded._recheck(root, observed['project'])
            bounded._recheck(ROOT, observed['skill'])
        except (OSError, ValueError, RuntimeError) as exc:
            report['status'] = 'blocked'
            report['errors'].append('read-set conflict: ' + str(exc)[:4096])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_root', type=Path)
    parser.add_argument('--tex-main', type=Path, default=Path('final_latex/main.tex'))
    args = parser.parse_args()
    result = inspect_project(args.project_root, tex_main=args.tex_main)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return EXIT[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
