from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import io
from pathlib import Path
import sys
import unittest
import zipfile
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from claim_workbook import Workbook
from claim_values import EvidenceError,NeedsReview
from tests.claim_fixture import workbook,source

class ClaimWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.contract=yaml.safe_load((ROOT/'core/claim_evidence_contract.yaml').read_text())
        self.selector=source()['selector']
    def selected(self,raw=None,selector=None,profiles=None):
        return Workbook(raw or workbook(),self.contract).select(selector or self.selector,profiles or [])
    def rewrite(self,raw,path,transform):
        out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(raw)) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as w:
            for name in z.namelist():w.writestr(name,transform(z.read(name)) if name==path else z.read(name))
        return out.getvalue()
    def test_exact_scalar_and_address(self):
        v,location=self.selected();self.assertEqual(v.value,Decimal(100));self.assertEqual(location['cells'],['D2'])
    def test_row_order_does_not_select_wrong_scenario(self):
        v,l=self.selected(workbook([['cost','candidate','S1',80,'kg'],['cost','baseline','S1',100,'kg']]))
        self.assertEqual(v.value,Decimal(100));self.assertEqual(l['row'],3)
    def test_duplicate_headers_and_duplicate_keys_rejected(self):
        for raw in (workbook(headers=['metric','scenario','sample','value','value']),
          workbook([['cost','baseline','S1',100,'kg'],['cost','baseline','S1',80,'kg']])):
            with self.subTest(raw=len(raw)),self.assertRaises(EvidenceError):self.selected(raw)
    def test_no_match_and_missing_sheet_rejected(self):
        s=deepcopy(self.selector);s['row_key']['scenario']='unknown'
        with self.assertRaises(EvidenceError):self.selected(selector=s)
        s['sheet']='missing'
        with self.assertRaises(EvidenceError):self.selected(selector=s)
    def test_formula_never_uses_cached_value(self):
        raw=workbook(mutate=lambda b:setattr(b.active['D2'],'value','=1+99'))
        raw=self.rewrite(raw,'xl/worksheets/sheet1.xml',lambda x:x.replace(b'<v></v>',b'<v>100</v>'))
        with self.assertRaises(NeedsReview):self.selected(raw)
    def test_numeric_strings_booleans_dates_errors_not_coerced(self):
        for value in ('100',True,datetime(2026,1,1),'#DIV/0!'):
            with self.subTest(value=value),self.assertRaises(NeedsReview):
                self.selected(workbook([['cost','baseline','S1',value,'kg']]))
    def test_missing_unit_is_not_dimensionless(self):
        s=deepcopy(self.selector);s.pop('unit')
        with self.assertRaises(NeedsReview):self.selected(selector=s)
    def test_profile_cannot_override_actual_units(self):
        s=deepcopy(self.selector);s['unit']={'kind':'numeric_profile','profile_id':'N1'}
        profile={'id':'N1','metric':'cost','unit':'h','status':'current','display_form':'decimal'}
        with self.assertRaises(EvidenceError):self.selected(selector=s,profiles=[profile])
        profile['unit']='kg';profile['status']='stale'
        with self.assertRaises(EvidenceError):self.selected(selector=s,profiles=[profile])
    def test_real_header_unit_not_fallback_to_unit_column(self):
        s=deepcopy(self.selector);s['unit']={'kind':'header'}
        with self.assertRaises(NeedsReview):self.selected(selector=s)
    def test_header_unit_and_profile_alias(self):
        s=deepcopy(self.selector);s['value_column']='value (kg)';s['unit']={'kind':'header'}
        raw=workbook(headers=['metric','scenario','sample','value (kg)','unit'])
        self.assertEqual(self.selected(raw,s)[0].unit,'kg')
    def test_intervals_and_categorical(self):
        s=deepcopy(self.selector);s.update(value_type='interval',lower_column='value',upper_column='upper');s.pop('value_column')
        raw=workbook([['cost','baseline','S1',1,'kg',2]],headers=['metric','scenario','sample','value','unit','upper'])
        self.assertEqual(self.selected(raw,s)[0].value,(Decimal(1),Decimal(2)))
        s=deepcopy(self.selector);s.update(value_type='categorical',unit={'kind':'not_applicable'})
        self.assertEqual(self.selected(workbook([['cost','baseline','S1','good','kg']]),s)[0].value,'good')
    def test_compressed_budget_and_real_coordinates(self):
        small=deepcopy(self.contract);small['limits']['uncompressed_bytes']=100
        with self.assertRaises(EvidenceError):Workbook(workbook(),small)
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',lambda x:x.replace(b'r="D2"',b'r="ZZ2"'))
        with self.assertRaises(EvidenceError):Workbook(raw,self.contract)
    def test_fake_dimension_cannot_hide_real_cells(self):
        small=deepcopy(self.contract);small['limits']['workbook_cells']=2
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',lambda x:x.replace(b'ref="A1:E3"',b'ref="A1:A1"'))
        with self.assertRaises(EvidenceError):Workbook(raw,small)
    def test_external_relationships_rejected(self):
        raw=workbook(mutate=lambda b:setattr(b.active['A2'],'hyperlink','https://example.invalid/source'))
        with self.assertRaises(EvidenceError):Workbook(raw,self.contract)
    def test_dtd_and_non_utf8_rejected(self):
        raw=self.rewrite(workbook(),'xl/workbook.xml',lambda x:b'<!DOCTYPE workbook [<!ENTITY x "x">]>'+x)
        with self.assertRaises(EvidenceError):Workbook(raw,self.contract)
        raw=self.rewrite(workbook(),'xl/workbook.xml',lambda x:x.decode().encode('utf-16'))
        with self.assertRaises(EvidenceError):Workbook(raw,self.contract)
    def test_duplicate_zip_members_rejected(self):
        raw=io.BytesIO(workbook())
        with zipfile.ZipFile(raw,'a') as z:z.writestr('../escape.xml','<x/>')
        with self.assertRaises(EvidenceError):Workbook(raw.getvalue(),self.contract)
    def test_merged_value_needs_review(self):
        raw=workbook(mutate=lambda b:b.active.merge_cells('D2:E2'))
        with self.assertRaises(NeedsReview):self.selected(raw)
    def test_fake_row_outside_sheet_data_rejected(self):
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',lambda x:x.replace(b'</sheetData>',b'</sheetData><extLst><row r="7"><c r="A7" t="n"><v>1</v></c></row></extLst>'))
        with self.assertRaises(EvidenceError):self.selected(raw)
    def test_selected_interval_reversed_and_conflicting_unit_headers(self):
        s=deepcopy(self.selector);s.update(value_type='interval',lower_column='value',upper_column='upper');s.pop('value_column')
        raw=workbook([['cost','baseline','S1',2,'kg',1]],headers=['metric','scenario','sample','value','unit','upper'])
        with self.assertRaises(EvidenceError):self.selected(raw,s)
    def test_xml_node_depth_and_member_count_budgets(self):
        for name,value in [('xml_depth',2),('xml_nodes',3),('zip_members',1),('table_rows',1),('table_columns',2)]:
            c=deepcopy(self.contract);c['limits'][name]=value
            with self.subTest(name=name),self.assertRaises(EvidenceError):Workbook(workbook(),c)
    def test_plain_numbers_read_without_float_precision_loss(self):
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',lambda x:x.replace(b'<v>100</v>',b'<v>1.234567890123456789</v>'))
        self.assertEqual(self.selected(raw)[0].value,Decimal('1.234567890123456789'))
    def test_decimal_row_key_is_explicit_and_exact(self):
        s=deepcopy(self.selector);s['row_key']['value']={'decimal':'100.0000000000000001'}
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',
                         lambda x:x.replace(b'<v>100</v>',b'<v>100.0000000000000001</v>'))
        self.assertEqual(self.selected(raw,s)[0].value,Decimal('100.0000000000000001'))
        with self.assertRaises(EvidenceError):self.selected(selector=s)
        s['row_key']['value']=100
        self.assertEqual(self.selected(selector=s)[0].value,Decimal(100))
        s['row_key']['value']={'decimal':'1e2'}
        self.assertEqual(self.selected(selector=s)[0].value,Decimal(100))
        s['row_key']['value']=100.0
        with self.assertRaises(EvidenceError):self.selected(selector=s)

    def test_duplicate_cell_value_payload_is_ambiguous(self):
        raw=self.rewrite(workbook(),'xl/worksheets/sheet1.xml',
                         lambda x:x.replace(b'<v>100</v>',b'<v>100</v><v>80</v>'))
        with self.assertRaises(EvidenceError):self.selected(raw)
    def test_two_sheet_names_cannot_disguise_one_physical_sheet(self):
        def alias(data):
            import xml.etree.ElementTree as ET
            namespace='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            tree=ET.fromstring(data);sheets=tree.find(namespace+'sheets')
            copied=deepcopy(sheets[0]);copied.set('name','alias');copied.set('sheetId','2')
            sheets.append(copied)
            return ET.tostring(tree,encoding='utf-8')
        raw=self.rewrite(workbook(),'xl/workbook.xml',alias)
        with self.assertRaises(EvidenceError):self.selected(raw)
    def test_sheet_and_relationship_tags_must_have_ooxml_meaning(self):
        mutations=(
            ('sheet child','xl/workbook.xml',lambda x:x.replace(b'<sheet xmlns:r=',b'<notSheet xmlns:r=',1)),
            ('workbook root','xl/workbook.xml',lambda x:x.replace(b'<workbook xmlns=',b'<notWorkbook xmlns=',1)
             .replace(b'</workbook>',b'</notWorkbook>',1)),
            ('relationship child','xl/_rels/workbook.xml.rels',
             lambda x:x.replace(b'<Relationship Type=',b'<notRelationship Type=',1)),
            ('relationships root','xl/_rels/workbook.xml.rels',
             lambda x:x.replace(b'<Relationships xmlns=',b'<notRelationships xmlns=',1)
             .replace(b'</Relationships>',b'</notRelationships>',1)),
            ('relationship type','xl/_rels/workbook.xml.rels',
             lambda x:x.replace(b'/relationships/worksheet" Target=',b'/relationships/styles" Target=',1)),
        )
        for label,path,change in mutations:
            with self.subTest(label=label),self.assertRaises(EvidenceError):
                self.selected(self.rewrite(workbook(),path,change))
    def test_percentage_display_requires_explicit_value_semantics(self):
        raw=workbook([['cost','baseline','S1',0.4,'%']],
                     mutate=lambda b:setattr(b.active['D2'],'number_format','0%'))
        with self.assertRaises(NeedsReview):self.selected(raw)
    def test_escaped_percent_is_literal_not_percentage_scaling(self):
        for fmt in ('0\\%', '0"%"'):
            raw=workbook(mutate=lambda b:setattr(b.active['D2'],'number_format',fmt))
            self.assertEqual(self.selected(raw)[0].value,Decimal(100))
    def test_ambiguous_workbook_sheet_collections_rejected(self):
        raw=self.rewrite(workbook(),'xl/workbook.xml',
                         lambda x:x.replace(b'</sheets>',b'</sheets><sheets/>'))
        with self.assertRaises(EvidenceError):self.selected(raw)

if __name__=='__main__':unittest.main()
