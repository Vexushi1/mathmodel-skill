"""A2 integration of A1 observations; no model, numerical or review authority.

Only the existing delivery/receipt coordinators persist the returned bindings.
Inspection does not execute task source, recover journals, or write project state.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'implementation_conformance_policy'
STAGES = ('primary', 'analysis')
DELIVERY = 'conformance_delivery'
ACCEPTANCE = 'conformance_acceptance'
FIELDS = (DELIVERY, ACCEPTANCE)
EXTRA_SOURCES = ('scripts/conformance_gate.py', 'core/state_transition_contract.yaml',
                 'core/runtime_assurance_contract.yaml', 'scripts/stage_inputs.py',
                 'scripts/artifact_fingerprint.py')


def digest(domain: str, value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256((domain + '\0' + encoded).encode('utf-8')).hexdigest()


def present(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, Mapping):
        return False
    if POLICY in entry:
        return True
    stages = entry.get('solver_execution')
    return isinstance(stages, Mapping) and any(
        isinstance(value, Mapping) and any(field in value for field in FIELDS)
        for value in stages.values())


def _shape(schema: dict, name: str, value: Any) -> list[str]:
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator({'$ref': '#/$defs/' + name, '$defs': schema['$defs']})
    return [f'conformance {name}: ' + '/'.join(map(str, error.path)) + ': ' + error.message
            for error in list(validator.iter_errors(value))[:12]]


def _schema() -> dict:
    import yaml
    return yaml.safe_load((ROOT / 'core/project_state.schema.yaml').read_text(encoding='utf-8'))


def policy_issues(entry: Mapping[str, Any], schema: dict | None = None) -> list[str]:
    if not present(entry):
        return []
    schema = _schema() if schema is None else schema
    issues = _shape(schema, 'implementation_conformance_policy', entry.get(POLICY))
    policy = entry.get(POLICY)
    required = policy.get('required_stages', []) if isinstance(policy, Mapping) else []
    required = required if isinstance(required, list) else []
    selections = entry.get('solver_execution')
    for stage, slot in (selections.items() if isinstance(selections, Mapping) else ()):
        if not isinstance(slot, Mapping):
            continue
        for field in FIELDS:
            if field in slot:
                issues.extend(_shape(schema, field, slot[field]))
                if stage not in required:
                    issues.append(f'conformance {stage}: orphan {field} without required stage policy')
    return issues


def required_stages(entry: Mapping[str, Any]) -> tuple[str, ...]:
    """Policy errors are handled separately; never interpret null as legacy off."""
    value = entry.get(POLICY)
    stages = value.get('required_stages', []) if isinstance(value, Mapping) else []
    return tuple(stage for stage in STAGES if isinstance(stages, list) and stage in stages)


def question_for(state: Mapping[str, Any], entry: Mapping[str, Any]) -> str:
    entries = state.get('subproblems') or {}
    exact = [str(key) for key, value in entries.items() if value is entry]
    matches = exact or [str(key) for key, value in entries.items() if value == entry]
    if len(matches) != 1:
        raise ValueError('conformance: question scope is missing or ambiguous')
    return matches[0]


def merge_read_sets(target: dict, observed: Mapping[str, Any]) -> None:
    for scope in ('project', 'skill'):
        into = target.setdefault(scope, {})
        for path, value in observed.get(scope, {}).items():
            if path in into and into[path] != value:
                raise ValueError(f'conformance {scope} source changed between checks: {path}')
            into[path] = value


def _context(state: Mapping[str, Any], question: str) -> dict:
    entry = state.get('subproblems', {}).get(question, {})
    keys = (POLICY, 'implementation_conformance', 'code', 'result_analysis_code',
            'semantic_revision', 'approved_semantic_revision', 'validated_semantic_revision',
            'semantic_identity_hash', 'validated_semantic_identity_hash', 'approved_semantic_identity_hash',
            'semantic_identity_schema_version', 'model_challenge_status', 'human_model_approval_status')
    execution = state.get('execution') or {}
    return {'entry': {key: entry[key] for key in keys if key in entry},
            'backend': {key: execution[key] for key in ('solver_backend', 'solver_backend_selection_reason') if key in execution}}


def inspect_gate(root: Path, state: Mapping[str, Any], question: str, stage: str, *,
                 boundary: str = 'delivery', receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return only this opt-in prerequisite, never whole-stage acceptance."""
    result: dict[str, Any] = {'enabled': False, 'status': 'not_enabled', 'issues': [],
        'observed_sources': {'project': {}, 'skill': {}}, 'execution_authorized': False,
        'mathematical_equivalence': 'not_established', 'numerical_acceptance': 'not_assessed'}
    root = Path(root).resolve()
    entry = (state.get('subproblems') or {}).get(question, {})
    if not present(entry):
        return result
    result.update(enabled=True, status='blocked')
    try:
        if stage not in STAGES or boundary not in ('delivery', 'receipt', 'current'):
            raise ValueError('conformance: unsupported stage/boundary')
        issues = policy_issues(entry)
        if issues:
            result['issues'].extend(issues)
            return result
        if stage not in required_stages(entry):
            result.update(enabled=False, status='not_enabled')
            return result
        # Lazy import avoids the existing runtime -> prerequisite -> inspector cycle.
        import model_code_conformance as audit
        observed = result['observed_sources']
        raw = audit._read(root, 'state/project_state.yaml', 2 * 1024 * 1024, observed['project'])
        original = audit._yaml(raw.decode('utf-8'), 32)
        if digest('A2-context', _context(original, question)) != digest('A2-context', _context(state, question)):
            raise ValueError('conformance: candidate model/source/declaration differs from captured state')
        report = audit.inspect_project(root, question, stage)
        result['structure_status'] = report['status']
        merge_read_sets(observed, report['observed_sources'])
        for path in EXTRA_SOURCES:
            audit._read(ROOT, path, 8 * 1024 * 1024, observed['skill'])
        if report['status'] != 'structure_verified':
            details = report.get('errors', []) + report.get('review_required', [])
            result['issues'].append(f'conformance {question}.{stage}: {report["status"]}; '
                                    + '; '.join(details or [report.get('reason', 'structure not assessed')]))
            return result
        actual_config = observe_execution_sources(root, state, question, report['binding'], observed)
        result['observed_config_sha256'] = digest('HSK-conformance-config-v1', actual_config)
        record = entry['implementation_conformance'][stage]
        binding = {'protocol_version': '1.0.0', 'question': question, 'stage': stage,
            **report['binding'], 'declaration_sha256': digest('HSK-conformance-declaration-v1', record),
            'authority_sha256': digest('HSK-conformance-authorities-v1', observed['skill']),
            'structure_status': 'structure_verified', 'applicability': 'current'}
        result['delivery_candidate'] = binding
        slot = (entry.get('solver_execution') or {}).get(stage, {})
        if boundary != 'delivery' and slot.get(DELIVERY) != binding:
            raise ValueError(f'conformance {question}.{stage}: missing/stale delivery binding; redeliver explicitly')
        if receipt is not None and str(receipt.get('code_bundle_sha256', '')).lower() != binding['source_bundle_sha256']:
            raise ValueError(f'conformance {question}.{stage}: receipt source bundle differs from checked delivery')
        if boundary == 'current':
            layer = 'solution_workbook' if stage == 'primary' else 'result_analysis_workbook'
            expected = str((entry.get('validated_artifact_hashes') or {}).get(layer, '')).lower()
            accepted = slot.get(ACCEPTANCE)
            wanted = acceptance_binding(binding, str(expected).lower())
            if accepted != wanted:
                raise ValueError(f'conformance {question}.{stage}: missing/stale acceptance binding')
            path = entry.get(layer)
            if not isinstance(path, str) or not path:
                raise ValueError('conformance: accepted workbook path is missing')
            from stage_code import _relative_path
            from artifact_fingerprint import sha256_file
            actual = sha256_file(_relative_path(root, path))
            if actual != expected or (path in observed['project'] and observed['project'][path] != actual):
                raise ValueError('conformance: accepted workbook changed')
            observed['project'][path] = actual
        result['status'] = 'satisfied'
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        result['issues'].append(f'conformance {question}.{stage}: {exc}')
        result['status'] = 'blocked'
    finally:
        try:
            assert_observed(root, result['observed_sources'])
        except (OSError, ValueError, RuntimeError) as exc:
            result['issues'].append(f'conformance read-set conflict: {exc}')
            result['status'] = 'blocked'
    return result


def observe_execution_sources(root: Path, state: Mapping[str, Any], question: str,
                              binding: Mapping[str, Any], observed: dict) -> dict:
    """Capture the real execution read set; reuse the existing input identity verifier.

    Data bytes participate in optimistic transaction validation, not in a second
    numerical database or the structural declaration digest.
    """
    import model_code_conformance as audit
    import run_config_parser
    from stage_inputs import input_files, observe_inputs
    from execution_protocol import declared_input_paths
    from artifact_fingerprint import sha256_file
    from stage_code import _relative_path
    raw = audit._read(root, binding['entrypoint'], 2 * 1024 * 1024, observed['project'])
    _, config = run_config_parser.parse_embedded_config(
        raw.decode('utf-8-sig'), messages=run_config_parser.DELIVERY_MESSAGES,
        backend=binding['solver_backend'])
    # Capture before qualification, recheck afterward and again at commit.
    for path in input_files(root, declared_input_paths(config)):
        merge_read_sets(observed, {'project': {path.relative_to(root).as_posix(): sha256_file(path)}})
    issues = observe_inputs(root, config, state)['issues']
    if issues:
        raise ValueError('; '.join(issues))
    if config.get('stage') == 'analysis':
        entry = (state.get('subproblems') or {}).get(question, {})
        relative = entry.get('solution_workbook')
        if not isinstance(relative, str) or not relative:
            raise ValueError('conformance: analysis has no registered primary workbook')
        actual = sha256_file(_relative_path(root, relative))
        expected = str(config.get('primary_workbook_sha256', '')).lower()
        if actual != expected:
            raise ValueError('conformance: analysis primary workbook differs from delivered config')
        merge_read_sets(observed, {'project': {relative: actual}})
    assert_observed(root, observed)
    return config


def acceptance_binding(delivered: Mapping[str, Any], workbook_sha256: str) -> dict[str, str]:
    return {'protocol_version': '1.0.0', 'delivery_sha256': digest('HSK-conformance-delivery-v1', delivered),
            'workbook_sha256': workbook_sha256.lower(), 'applicability': 'current'}


def assert_observed(root: Path, observed: Mapping[str, Any]) -> None:
    from project_transaction import _check_read_set
    for scope, base in (('project', root), ('skill', ROOT)):
        if observed.get(scope):
            _check_read_set(base, observed[scope])


def skill_validator(observed: Mapping[str, Any]):
    """Use the existing staged-validator hook; no alternative transaction engine."""
    expected = deepcopy(observed.get('skill', {}))
    def validate(staged):
        from project_transaction import _check_read_set, STATE_RELATIVE_PATH
        if expected:
            _check_read_set(ROOT, expected)
        if expected and STATE_RELATIVE_PATH in staged:
            import yaml
            candidate = yaml.safe_load(staged[STATE_RELATIVE_PATH].read_text(encoding='utf-8'))
            errors = [issue for question, entry in (candidate.get('subproblems') or {}).items()
                      for issue in stored_issues(entry, str(question))]
            if errors:
                raise ValueError('; '.join(errors))
    return validate


def read_issues(root: Path, state: Mapping[str, Any], entry: Mapping[str, Any], stage: str, *,
                boundary: str = 'current') -> list[str]:
    if not present(entry):
        return []
    try:
        question = question_for(state, entry)
        return inspect_gate(root, state, question, stage, boundary=boundary)['issues']
    except (ValueError, TypeError, AttributeError) as exc:
        return [f'conformance: {exc}']


def stored_issues(entry: Mapping[str, Any], question: str) -> list[str]:
    """Shape/scope checks for candidate states; live qualification remains separate."""
    errors = policy_issues(entry)
    if errors or not present(entry):
        return errors
    selections = entry.get('solver_execution') or {}
    for stage in required_stages(entry):
        slot = selections.get(stage, {})
        certificate = slot.get(DELIVERY)
        accepted = slot.get(ACCEPTANCE)
        stale = set(entry.get('stale_layers') or [])
        relevant = {'data', 'primary_code', 'solution_workbook'}
        if stage == 'analysis':
            relevant |= {'analysis_code', 'result_analysis_workbook'}
        lifecycle = entry.get(f'{stage}_execution_status')
        if not stale.intersection(relevant):
            if lifecycle in {'code_delivered', 'awaiting_user_execution', 'workbook_received', 'accepted'} and not certificate:
                errors.append(f'conformance {question}.{stage}: active execution state has no delivery binding')
            quality = entry.get('result_quality_status' if stage == 'primary' else 'result_analysis_status')
            if lifecycle == 'accepted' and quality == 'passed' and (
                    not accepted or accepted.get('applicability') != 'current'):
                errors.append(f'conformance {question}.{stage}: accepted current result has no current acceptance binding')
        if certificate is None and accepted is not None:
            errors.append(f'conformance {question}.{stage}: acceptance has no delivery binding')
        if certificate is not None:
            if certificate.get('question') != question or certificate.get('stage') != stage:
                errors.append(f'conformance {question}.{stage}: cross-question/stage delivery binding')
            if certificate.get('applicability') == 'current':
                record = (entry.get('implementation_conformance') or {}).get(stage)
                field = 'code' if stage == 'primary' else 'result_analysis_code'
                identities = {'entrypoint': entry.get(field), 'source_bundle_sha256': str(slot.get('bundle_sha256', '')).lower(),
                              'semantic_revision': entry.get('semantic_revision'),
                              'semantic_identity_hash': entry.get('semantic_identity_hash')}
                if any(certificate.get(key) != value for key, value in identities.items()):
                    errors.append(f'conformance {question}.{stage}: current delivery identity differs from stage state')
                if certificate.get('declaration_sha256') != digest('HSK-conformance-declaration-v1', record):
                    errors.append(f'conformance {question}.{stage}: current declaration differs from delivery')
        if accepted is not None and accepted.get('applicability') == 'current':
            if not certificate or certificate.get('applicability') != 'current':
                errors.append(f'conformance {question}.{stage}: current acceptance has no current delivery')
            elif accepted.get('delivery_sha256') != digest('HSK-conformance-delivery-v1', certificate):
                errors.append(f'conformance {question}.{stage}: acceptance belongs to a different delivery')
            layer = 'solution_workbook' if stage == 'primary' else 'result_analysis_workbook'
            expected = str((entry.get('validated_artifact_hashes') or {}).get(layer, '')).lower()
            if accepted.get('workbook_sha256') != expected:
                errors.append(f'conformance {question}.{stage}: acceptance workbook differs from validated state')
            if certificate and str(slot.get('validated_bundle_sha256', '')).lower() != certificate.get('source_bundle_sha256'):
                errors.append(f'conformance {question}.{stage}: acceptance bundle differs from validated source')
    return errors


def add_runtime_resources(plan: dict, state: Mapping[str, Any], question: str | None) -> None:
    """Expose only the opted-in consumers' Authority, not a parallel gate chain."""
    entries = state.get('subproblems') or {}
    scopes = {str(key): required_stages(entry) for key, entry in entries.items()
              if (question is None or question == str(key)) and present(entry)}
    if not scopes:
        return
    import yaml
    contract_path = 'core/model_code_conformance_contract.yaml'
    contract = yaml.safe_load((ROOT / contract_path).read_text(encoding='utf-8'))
    settings = contract['activation']['integration']
    consumers = [row['name'] for row in plan.get('pre_delivery_gates', [])
                 if row['name'] in settings['consumer_gates']]
    if not consumers:
        return
    for path in settings['resources']:
        if path not in plan['load_order']:
            plan['load_order'].append(path)
        if path.startswith('core/') and path not in plan['contracts']:
            plan['contracts'].append(path)
    plan['conformance_integration'] = {
        'mode': 'opt_in_existing_consumers', 'scopes': {key:list(stages) for key,stages in scopes.items()},
        'consumer_gates': consumers, 'resources': list(settings['resources']),
        'mathematical_equivalence': 'not_established', 'execution_authorized': False,
    }
