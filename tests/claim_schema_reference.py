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
B2B2_SCHEMA_SHA256 = '62d1fbe7c5694929685f9ca6634143ea38043c8ae3759d238c1b1594e9bc1785'
B2B3A_SCHEMA_SHA256 = '99e7df6a9fe3872698a1d126d0d678b5b91f3a08371be3353b18389b5fabb625'
B2B3B_SCHEMA_SHA256 = '2a06f7b6ac281f65a1dc520ecec8ac24981f0bba602e49d89a4320d18e1633b7'
B2B3C_SCHEMA_SHA256 = '4d1d84c298529f6ac0014621a0d54245974f0e29e249451ba2b22d8f4bf244cc'
B2B4_SCHEMA_SHA256 = '5025ba4a659feba51d217ab60461e7a71a4e8292199c87f3f373e3682ac21bc4'
B2B6_DISPOSITION_RULES_SHA256 = '9e9e2edaa80c0ca6060930a953ee67e2d4611d95ba24533f84ad33f3c08e516e'

def _digest(schema):
    encoded = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()

def previous_b2b6_schema(schema):
    schema = deepcopy(schema)
    assert schema['version'] == '8.11.0'
    schema['version'] = '8.10.0'
    policy = schema['$defs']['claim_consumption_policy']
    assert policy['properties']['protocol_version'] == {
        'enum': ['1.0.0', '1.1.0', '1.2.0', '1.3.0', '1.4.0']}
    policy['properties']['protocol_version'] = {
        'enum': ['1.0.0', '1.1.0', '1.2.0', '1.3.0']}
    assert policy['oneOf'].pop() == {
        'required': ['figure_bindings'],
        'properties': {
            'protocol_version': {'const': '1.4.0'},
            'mode': {'const': 'enforce_latex_text_and_figure_chain'},
            'figure_bindings': {'minItems': 1, 'items': {'required': ['source_bindings']}},
        },
    }
    evidence = schema['$defs']['analysis_evidence_entry']
    assert evidence['properties'].pop('impact_scope') == {
        'type': 'string', 'enum': ['auxiliary_wording', 'core_answer', 'model_validity']}
    assert evidence['properties'].pop('return_stage') == {
        'type': 'string', 'enum': ['solve_validate', 'model_design']}
    assert _digest(evidence.pop('allOf')) == B2B6_DISPOSITION_RULES_SHA256
    assert _digest(schema) == B2B4_SCHEMA_SHA256
    return schema

def previous_b2b4_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] == '8.11.0':
        schema = previous_b2b6_schema(schema)
    assert schema['version'] == '8.10.0'
    schema['version'] = '8.9.0'
    policy = schema['$defs']['claim_consumption_policy']
    assert policy['description'] == ('B2显式消费观察、陈旧传播或模块化LaTeX文本与Figure链有限门；'
                                     '实际消费边仍为paper_fragments.depends_on。')
    policy['description'] = ('B2显式消费观察、陈旧传播或模块化LaTeX文本有限门与覆盖义务；'
                             '可选Figure绑定只登记身份，实际消费边仍为paper_fragments.depends_on。')
    assert policy['properties']['protocol_version'] == {'enum': ['1.0.0', '1.1.0', '1.2.0', '1.3.0']}
    assert policy['properties']['mode'] == {
        'enum': ['observe', 'propagate', 'enforce_latex_text', 'enforce_latex_text_and_figure_chain']}
    policy['properties']['protocol_version'] = {'enum': ['1.0.0', '1.1.0', '1.2.0']}
    policy['properties']['mode'] = {'enum': ['observe', 'propagate', 'enforce_latex_text']}
    assert policy['oneOf'].pop() == {
        'required': ['figure_bindings'],
        'properties': {
            'protocol_version': {'const': '1.3.0'},
            'mode': {'const': 'enforce_latex_text_and_figure_chain'},
            'figure_bindings': {'minItems': 1, 'items': {'required': ['source_bindings']}},
        },
    }
    assert _digest(schema) == B2B3C_SCHEMA_SHA256
    return schema

def previous_b2b3c_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.10.0', '8.11.0'):
        schema = previous_b2b4_schema(schema)
    assert schema['version'] == '8.9.0'
    schema['version'] = '8.8.0'
    profile = schema['$defs']['numeric_metric_entry']['properties']
    assert profile.pop('figure_caption_decimals') == {'type': 'integer', 'minimum': 0, 'maximum': 30}
    assert _digest(schema) == B2B3B_SCHEMA_SHA256
    return schema


def previous_b2b3b_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.9.0', '8.10.0', '8.11.0'):
        schema = previous_b2b3c_schema(schema)
    assert schema['version'] == '8.8.0'
    schema['version'] = '8.7.0'
    figure = schema['$defs']['claim_consumption_policy']['properties']['figure_bindings']['items']
    assert figure['properties'].pop('source_bindings') == {
        'description': '可选B1来源声明；需要现场核验对应工作簿工作表及精确表头。',
        'type': 'array', 'minItems': 1, 'maxItems': 8,
        'items': {
            'type': 'object', 'additionalProperties': False,
            'required': ['source_id', 'sheet', 'required_headers'],
            'properties': {
                'source_id': {'type': 'string', 'pattern': r'^[A-Za-z][A-Za-z0-9_-]{0,63}$'},
                'sheet': {'type': 'string', 'minLength': 1, 'maxLength': 4096,
                          'pattern': r'^[^\s\x00-\x1f\x7f-\x9f](?:[^\x00-\x1f\x7f-\x9f]*[^\s\x00-\x1f\x7f-\x9f])?$'},
                'required_headers': {
                    'type': 'array', 'minItems': 1, 'maxItems': 64, 'uniqueItems': True,
                    'items': {'type': 'string', 'minLength': 1, 'maxLength': 4096,
                              'pattern': r'^(?=.*\S)[^\x00-\x1f\x7f-\x9f]+$'},
                },
            },
        },
    }
    assert _digest(schema) == B2B3A_SCHEMA_SHA256
    return schema

def previous_b2b3a_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.8.0', '8.9.0', '8.10.0', '8.11.0'):
        schema = previous_b2b3b_schema(schema)
    assert schema['version'] == '8.7.0'
    schema['version'] = '8.6.0'
    policy = schema['$defs']['claim_consumption_policy']
    assert policy['description'] == 'B2显式消费观察、陈旧传播或模块化LaTeX文本有限门与覆盖义务；可选Figure绑定只登记身份，实际消费边仍为paper_fragments.depends_on。'
    policy['description'] = 'B2显式消费观察、陈旧传播或模块化LaTeX文本有限门与覆盖义务；实际消费边仍为paper_fragments.depends_on。'
    assert policy['properties'].pop('figure_bindings') == {
        'description': '可选Figure身份绑定；本字段不表示图片、来源或caption已获批准。',
        'type': 'array', 'maxItems': 128,
        'items': {
            'type': 'object', 'additionalProperties': False,
            'required': ['figure_id', 'fragment_id', 'latex_label', 'image_path'],
            'properties': {
                'figure_id': {'type': 'string', 'minLength': 1, 'maxLength': 128,
                              'pattern': r'^(?=.*\S)[^|`\r\n]{1,128}$'},
                'fragment_id': {'type': 'string', 'pattern': r'^paper\.[A-Za-z0-9_.-]+$'},
                'latex_label': {'type': 'string', 'minLength': 1, 'maxLength': 128,
                                'pattern': r'^[A-Za-z][A-Za-z0-9:._-]*$'},
                'image_path': {'type': 'string', 'maxLength': 512,
                               'pattern': r'^(?!\.{1,2}(?:/|$))[^/\\:\x00-\x1f\x7f-\x9f]+(?:/(?!\.{1,2}(?:/|$))[^/\\:\x00-\x1f\x7f-\x9f]+)*\.(?:pdf|png|svg)$'},
            },
        },
    }
    assert _digest(schema) == B2B2_SCHEMA_SHA256
    return schema

def previous_b2b_schema(schema):
    schema = deepcopy(schema)
    if schema['version'] in ('8.7.0', '8.8.0', '8.9.0', '8.10.0', '8.11.0'):
        schema = previous_b2b3a_schema(schema)
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
    if schema['version'] in ('8.6.0', '8.7.0', '8.8.0', '8.9.0', '8.10.0', '8.11.0'):
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
    if schema['version'] in ('8.5.0', '8.6.0', '8.7.0', '8.8.0', '8.9.0', '8.10.0', '8.11.0'):
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
    if schema['version'] in ('8.5.0', '8.6.0', '8.7.0', '8.8.0', '8.9.0', '8.10.0', '8.11.0'):
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
