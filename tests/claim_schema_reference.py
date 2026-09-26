"""Exact predecessor protection used only by regression tests, never runtime."""
from copy import deepcopy
import hashlib
import json

B1_DEFINITIONS = (
    'claim_selector_unit', 'claim_selector', 'claim_source', 'claim_derivation',
    'claim_assertion', 'claim_record', 'claim_evidence',
)
A2_SCHEMA_SHA256 = '657a554b78a93e7de4bde75cf898bf595fe00b9531883b2b804b83e4c0899385'

def previous_a2_schema(schema):
    schema = deepcopy(schema)
    assert schema['version'] == '8.3.0'
    schema['version'] = '8.2.0'
    for name in B1_DEFINITIONS:
        schema['$defs'].pop(name)
    assert schema['properties']['paper_framework']['properties'].pop('claim_evidence') == {'$ref': '#/$defs/claim_evidence'}
    encoded = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == A2_SCHEMA_SHA256
    return schema
