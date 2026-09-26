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

def _digest(schema):
    encoded = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()

def previous_b1_schema(schema):
    schema = deepcopy(schema)
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
    if schema['version'] == '8.4.0':
        schema = previous_b1_schema(schema)
    assert schema['version'] == '8.3.0'
    schema['version'] = '8.2.0'
    for name in B1_DEFINITIONS:
        schema['$defs'].pop(name)
    assert schema['properties']['paper_framework']['properties'].pop('claim_evidence') == {'$ref': '#/$defs/claim_evidence'}
    assert _digest(schema) == A2_SCHEMA_SHA256
    return schema
