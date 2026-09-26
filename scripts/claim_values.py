"""Finite Decimal operations on already-selected observations, not source acceptance."""
from __future__ import annotations
from dataclasses import dataclass, replace
from decimal import Decimal, DecimalException, Inexact, localcontext
import re
from typing import Any, Mapping

class EvidenceError(ValueError):
    """A deterministic record, arithmetic or source conflict."""

class NeedsReview(EvidenceError):
    """An unsupported/unknown case; it must not be coerced to a verified value."""

@dataclass(frozen=True)
class Value:
    kind: str
    value: Any
    unit: str
    identity: Mapping[str, Any]
    origins: frozenset[str]

_DECIMAL = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')

def number(value: Any, contract: Mapping[str, Any]) -> Decimal:
    """Parse a number/explicit decimal literal, never an expression or bool."""
    limits = contract['limits']
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise EvidenceError('numeric type is unsupported')
    text = str(value)
    if len(text) > limits['decimal_digits'] + 16 or not _DECIMAL.fullmatch(text):
        raise EvidenceError('not a finite decimal literal')
    try:
        result = Decimal(text)
    except DecimalException as exc:
        raise EvidenceError('invalid decimal') from exc
    if (not result.is_finite() or len(result.as_tuple().digits) > limits['decimal_digits']
            or abs(result.adjusted()) > limits['decimal_exponent']
            or abs(result.as_tuple().exponent) > limits['decimal_exponent'] + limits['decimal_digits']):
        raise EvidenceError('finite numeric precision/exponent budget exceeded')
    return result

def unit_info(unit: str, contract: Mapping[str, Any]) -> tuple[str, Decimal, str]:
    if not isinstance(unit, str) or not unit.strip() or unit == 'not_applicable':
        raise NeedsReview('unit_unknown or not applicable to numeric arithmetic')
    known = contract['units'].get(unit)
    if known:
        return known['dimension'], Decimal(known['scale']), known['kind']
    return 'custom:' + unit, Decimal(1), 'custom'

def converted(value: Value, target: str, contract: Mapping[str, Any]) -> Value:
    if value.kind != 'scalar':
        raise NeedsReview('only identity is implemented for interval/categorical values')
    old_dim, old_scale, old_kind = unit_info(value.unit, contract)
    new_dim, new_scale, new_kind = unit_info(target, contract)
    if old_dim != new_dim:
        raise NeedsReview('unit conversion is unknown or crosses dimensions')
    if (old_kind == 'points') != (new_kind == 'points'):
        raise EvidenceError('percent/ratio and percentage points are distinct quantities')
    if old_scale == new_scale:
        return replace(value, unit=target)
    try:
        with localcontext() as ctx:
            ctx.prec = contract['limits']['decimal_precision']
            ctx.traps[Inexact] = True
            out = number(value.value * old_scale / new_scale, contract)
    except Inexact as exc:
        raise NeedsReview('unit conversion exceeds the exact decimal precision budget') from exc
    return replace(value, value=out, unit=target)

def _comparable(items: list[Value], axis: str) -> None:
    if axis == 'metric' or not axis or any(axis not in x.identity for x in items):
        raise EvidenceError('comparison axis must be observed and cannot be the metric')
    base = {k:v for k,v in items[0].identity.items() if k != axis}
    if any({k:v for k,v in x.identity.items() if k != axis} != base for x in items):
        raise EvidenceError('metric or noncomparison identity axes conflict')
    axes = [x.identity[axis] for x in items]
    if any(axes[i] == axes[j] for i in range(len(axes)) for j in range(i)):
        raise EvidenceError('comparison/aggregation observations must differ on the declared axis')
    seen: set[str] = set()
    for item in items:
        if seen.intersection(item.origins):
            raise EvidenceError('duplicate physical observations cannot count as independent evidence')
        seen.update(item.origins)

def derive(node: Mapping[str, Any], args: Mapping[str, Any], contract: Mapping[str, Any]) -> Value:
    """Dispatch finite named operations. No executable expression language exists."""
    try:
        with localcontext() as ctx:
            ctx.prec = contract['limits']['decimal_precision']
            ctx.traps[Inexact] = True
            return _derive(node, args, contract)
    except Inexact as exc:
        raise NeedsReview('arithmetic requires rounding beyond the exact decimal precision budget') from exc
    except DecimalException as exc:
        raise EvidenceError('finite decimal arithmetic failed') from exc

def _derive(node: Mapping[str, Any], args: Mapping[str, Any], contract: Mapping[str, Any]) -> Value:
    op = node['op']
    if op in ('identity', 'convert_unit', 'percent_to_ratio', 'ratio_to_percent'):
        value = args['value']
        if op == 'identity':
            return value
        if op == 'convert_unit':
            return converted(value, node['to_unit'], contract)
        expected, target = ('percent','ratio') if op == 'percent_to_ratio' else ('ratio','%')
        if unit_info(value.unit, contract)[2] != expected:
            raise EvidenceError('percentage conversion does not match the input type')
        return converted(value, target, contract)
    if op == 'aggregate':
        items, axis = args['items'], node['axis']
    elif op in ('difference','ratio','relative_change','improvement','percentage_points'):
        items, axis = [args['baseline'],args['candidate']], node['comparison_axis']
    else:
        raise EvidenceError('operation is not in the finite whitelist')
    if any(x.kind != 'scalar' for x in items):
        raise NeedsReview('only identity is implemented for interval/categorical values')
    _comparable(items, axis)
    first = items[0]
    aligned = [converted(x, first.unit, contract).value for x in items]
    unit = first.unit
    if op == 'aggregate':
        reducer = node['reducer']
        functions = {'sum':lambda:sum(aligned,Decimal(0)), 'mean':lambda:sum(aligned,Decimal(0))/len(aligned),
                     'min':lambda:min(aligned), 'max':lambda:max(aligned)}
        if reducer not in functions:
            raise EvidenceError('unknown aggregate reducer')
        output = functions[reducer]()
    else:
        baseline, candidate = aligned
        if op in ('relative_change','improvement') and baseline <= 0:
            raise EvidenceError('relative change/improvement requires a strictly positive baseline')
        if op == 'difference':
            output = candidate - baseline
            if unit_info(unit, contract)[2] == 'percent':
                # Express differences between percentage-valued observations as points.
                output = (candidate-baseline)*unit_info(unit,contract)[1]/Decimal('.01')
                unit = '百分点'
        elif op == 'percentage_points':
            if unit_info(first.unit,contract)[2] != 'percent':
                raise EvidenceError('percentage_points requires percent inputs')
            output = (candidate-baseline)*unit_info(unit,contract)[1]/Decimal('.01')
            unit = '百分点'
        elif op == 'ratio':
            if baseline == 0:
                raise EvidenceError('division by zero baseline')
            output, unit = candidate / baseline, 'ratio'
        else:
            output, unit = (candidate-baseline)/baseline, 'ratio'
            if op == 'improvement':
                if node['direction'] not in ('higher','lower'):
                    raise EvidenceError('unknown improvement direction')
                if node['direction'] == 'lower':
                    output = -output
    identity = dict(first.identity)
    identity[axis] = {'operation':op, 'observations':[x.identity[axis] for x in items]}
    origins = frozenset().union(*(x.origins for x in items))
    return Value('scalar',number(output,contract),unit,identity,origins)

def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {k:json_value(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [json_value(v) for v in value]
    return value

def describe(value: Value) -> dict[str, Any]:
    return {'value_type':value.kind,'value':json_value(value.value),'unit':value.unit,
            'identity':json_value(value.identity),'physical_sources':sorted(value.origins)}
