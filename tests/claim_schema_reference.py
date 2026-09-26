"""Exact predecessor protection used only by regression tests, never runtime."""
from copy import deepcopy
import hashlib
import json

B1_DEFINITIONS = (
    'claim_selector_unit', 'claim_selector', 'claim_source', 'claim_derivation',
    'claim_assertion', 'claim_record', 'claim_evidence',
)
A2_SCHEMA_SHA256 = '657a554b78a93e7de4bde75cf898bf595fe00b9531883b2b804b83e4c0899385'
B1_SCHEMA_SHA256 = 'fe2ddcef208dc712ed86150e0633e0acacd18e2b3b13c8f13c0c8b7729534034'
B2A_SCHEMA_SHA256 = '481127098bc09f620c3ee9d64ae368860734808f07fbbce04543310a65f41fb4'
B2B_SCHEMA_SHA256 = '3822af68490cc12a699ada8aeee272c439a6af5f0d685b3def7b160d201f7075'

def _digest(schema):
    encoded = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()

def previous_b2b_schema(schema):
    schema = deepcopy(schema)
    assert schema['version'] == '8.6.0'
    schema['version'] = '8.5.0'
    policy = schema['$defs']['claim_consumption_policy']
    assert policy['oneOf'].pop() == {
        'properties': {'protocol_version': {'const': '1.2.0'}, 'mode': {'const': 'enforce_latex_text'}}
    }
    assert policy['description'] == 'B2显式消费观察、陈旧传播或模块化LaTeX文本有限门与覆盖义务；实际消费边仍为paper_fragments.depends_on。'
    policy['description'] = 'B2显式消费观察或陈旧传播与覆盖义务；实际消费边仍为paper_fragments.depends_on。'
    assert policy['properties']['protocol_version'] == {'enum': ['1.0.0', '1.1.0', '1.2.0']}
    assert policy['properties']['mode'] == {'enum': ['observe', 'propagate', 'enforce_latex_text']}
    policy['properties']['protocol_version'] = {'enum': ['1.0.0', '1.1.0']}
    policy['properties']['mode'] = {'enum': ['observe', 'propagate']}
    assert _digest(schema) == B2B_SCHEMA_SHA256
    return schema

def previous_b2a_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] == '8.6.0':
        schema = previous_b2b_schema(schema)
    assert schema['version'] == '8.5.0'
    schema['version'] = '8.4.0'
    policy = schema['$defs']['claim_consumption_policy']
    assert policy.pop('oneOf') == [
        {'properties': {'protocol_version': {'const': '1.0.0'}, 'mode': {'const': 'observe'}}},
        {'properties': {'protocol_version': {'const': '1.1.0'}, 'mode': {'const': 'propagate'}}},
    ]
    assert policy['description'] == 'B2显式消费观察或陈旧传播与覆盖义务；实际消费边仍为paper_fragments.depends_on。'
    policy['description'] = 'B2显式只读消费观察与覆盖义务；实际消费边仍为paper_fragments.depends_on。'
    assert policy['properties']['protocol_version'] == {'enum': ['1.0.0', '1.1.0']}
    assert policy['properties']['mode'] == {'enum': ['observe', 'propagate']}
    policy['properties']['protocol_version'] = {'const': '1.0.0'}
    policy['properties']['mode'] = {'const': 'observe'}
    assert _digest(schema) == B2A_SCHEMA_SHA256
    return schema

def previous_b1_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.5.0', '8.6.0'):
        schema = previous_b2a_schema(schema)
    assert schema['version'] == '8.4.0'
    schema['version'] = '8.3.0'
    assert schema['properties']['paper_framework']['properties'].pop('claim_consumption_policy') == {
        '$ref': '#/$defs/claim_consumption_policy'
    }
    assert schema['$defs'].pop('claim_consumption_policy')['properties']['mode'] == {'const': 'observe'}
    fragment_id = schema['$defs']['paper_fragment_entry']['properties']['id']
    assert fragment_id == {'type': 'string', 'pattern': r'^paper\.[A-Za-z0-9_.-]+$'}
    fragment_id['pattern'] = r'^paper\\.[A-Za-z0-9_.-]+$'
    source_file = schema['$defs']['paper_fragment_entry']['properties']['source_file']
    assert source_file['pattern'] == r'^final_latex/.+\.tex$'
    source_file['pattern'] = r'^final_latex/.+\\.tex$'
    assert _digest(schema) == B1_SCHEMA_SHA256
    return schema

def previous_a2_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.5.0', '8.6.0'):
        schema = previous_b2a_schema(schema)
    if schema['version'] == '8.4.0':
        schema = previous_b1_schema(schema)
    assert schema['version'] == '8.3.0'
    schema['version'] = '8.2.0'
    for name in B1_DEFINITIONS:
        schema['$defs'].pop(name)
    assert schema['properties']['paper_framework']['properties'].pop('claim_evidence') == {'$ref': '#/$defs/claim_evidence'}
    assert _digest(schema) == A2_SCHEMA_SHA256
    return schema
