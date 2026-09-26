"""Bounded OOXML selection from captured bytes. Never execute formulas or fetch links."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import io
from pathlib import PurePosixPath
import posixpath
import re
from typing import Any, Mapping
import xml.etree.ElementTree as ET
import zipfile
from openpyxl.styles.numbers import BUILTIN_FORMATS, is_date_format
from claim_values import EvidenceError, NeedsReview, Value, number, unit_info

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
M = '{' + NS + '}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
_ADDRESS = re.compile(r'([A-Z]{1,3})([1-9][0-9]*)\Z')

@dataclass(frozen=True)
class Cell:
    address: str
    kind: str
    value: Any
    formula: bool = False

def current_profile(profiles: list, profile_id: str, metric: Any) -> dict:
    matched = [x for x in profiles if isinstance(x, Mapping) and x.get('id') == profile_id]
    if len(matched) != 1 or matched[0].get('status') != 'current':
        raise EvidenceError('Numeric Profile must be current and uniquely identified')
    if matched[0].get('metric') != metric:
        raise EvidenceError('Numeric Profile metric conflicts with the actual selected metric')
    return matched[0]

def _column(address: str) -> tuple[int, int]:
    match = _ADDRESS.fullmatch(address)
    if not match:
        raise EvidenceError('malformed cell coordinate')
    col = 0
    for ch in match[1]:
        col = col * 26 + ord(ch) - 64
    return col, int(match[2])

def _text(element: ET.Element) -> str:
    # Plain and rich text only; phonetic annotations do not alter the cell text.
    return ''.join(x.text or '' for x in element.findall(M+'t')) + ''.join(
        x.text or '' for run in element.findall(M+'r') for x in run.findall(M+'t'))

class Workbook:
    def __init__(self, raw: bytes, contract: Mapping[str, Any]):
        self.contract, self.limits = contract, contract['limits']
        if len(raw) > self.limits['workbook_bytes']:
            raise EvidenceError('workbook byte budget exceeded')
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.parts: dict[str, bytes] = {}
        self._rows: dict[str, dict[int, dict[int, Cell]]] = {}
        self._merges: dict[str, list[tuple[int,int,int,int]]] = {}
        self._preflight(raw)
        self.strings = self._shared_strings()
        self.date_styles, self.percent_styles = self._number_styles()
        self.sheets = self._sheets()

    def _preflight(self, raw: bytes) -> None:
        total = nodes = cells = 0
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                infos = archive.infolist()
                if len(infos) > self.limits['zip_members']:
                    raise EvidenceError('XLSX member budget exceeded')
                names: set[str] = set()
                for item in infos:
                    name = item.filename
                    path = PurePosixPath(name)
                    if (name in names or not name or '\\' in name or path.is_absolute()
                            or '..' in path.parts or ':' in name or item.flag_bits & 1
                            or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                        raise EvidenceError('unsafe/duplicate/encrypted XLSX member')
                    names.add(name)
                    if 'vbaproject' in name.lower() or 'externallinks/' in name.lower():
                        raise EvidenceError('macros or external workbook links are not supported')
                    total += item.file_size
                    if total > self.limits['uncompressed_bytes']:
                        raise EvidenceError('XLSX uncompressed byte budget exceeded')
                    with archive.open(item) as handle:
                        data = handle.read(min(item.file_size,self.limits['uncompressed_bytes'])+1)
                    if len(data) != item.file_size:
                        raise EvidenceError('XLSX actual length differs from declared length')
                    if not (name.endswith('.xml') or name.endswith('.rels')):
                        continue
                    if b'\0' in data or re.search(br'<!\s*(DOCTYPE|ENTITY)',data,re.I):
                        raise EvidenceError('DTD/entities/non-UTF8 XML are forbidden')
                    text = data.decode('utf-8-sig')
                    encoding = re.match(r'\s*<\?xml[^>]*encoding=[\"\']([^\"\']+)',text)
                    if encoding and encoding[1].lower() not in ('utf-8','utf8','us-ascii'):
                        raise EvidenceError('only UTF8 OOXML is supported')
                    depth = rows = 0
                    for event, el in ET.iterparse(io.BytesIO(data),events=('start','end')):
                        if event == 'start':
                            depth += 1; nodes += 1
                            if depth > self.limits['xml_depth'] or nodes > self.limits['xml_nodes']:
                                raise EvidenceError('OOXML node/depth budget exceeded')
                            tag = el.tag.rsplit('}',1)[-1]
                            if tag == 'Relationship' and (el.get('TargetMode','').lower()=='external'
                                    or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',el.get('Target',''))):
                                raise EvidenceError('external relationships are forbidden')
                            if tag in ('Override','Default') and any(x in el.get('ContentType','').lower()
                                    for x in ('macroenabled','vbaproject','macrosheet')):
                                raise EvidenceError('macro-enabled content is forbidden')
                            if el.tag == M+'row':
                                rows += 1
                                index = el.get('r','')
                                if not index.isdecimal() or not 1 <= int(index) <= self.limits['table_rows'] or rows > self.limits['table_rows']:
                                    raise EvidenceError('actual worksheet row budget exceeded')
                            if el.tag == M+'c':
                                cells += 1
                                col,row = _column(el.get('r',''))
                                if cells > self.limits['workbook_cells'] or col > self.limits['table_columns'] or row > self.limits['table_rows']:
                                    raise EvidenceError('actual worksheet cell/column budget exceeded')
                        else:
                            depth -= 1
                            el.clear()
                    self.parts[name] = data
        except (zipfile.BadZipFile, ET.ParseError, UnicodeError, RuntimeError, OverflowError) as exc:
            raise EvidenceError('invalid or unsafe XLSX archive/XML') from exc
        if '[Content_Types].xml' not in self.parts:
            raise EvidenceError('missing OOXML content types')

    def _tree(self, path: str) -> ET.Element:
        if path not in self.parts:
            raise EvidenceError('missing OOXML part: '+path)
        return ET.fromstring(self.parts[path])

    def _shared_strings(self) -> list[str]:
        if 'xl/sharedStrings.xml' not in self.parts:
            return []
        values = [_text(x) for x in self._tree('xl/sharedStrings.xml').findall(M+'si')]
        if len(values)>self.limits['workbook_cells'] or any(len(x)>self.limits['text_length'] for x in values):
            raise EvidenceError('shared string budget exceeded')
        return values

    def _number_styles(self) -> tuple[list[bool],list[bool]]:
        if 'xl/styles.xml' not in self.parts:
            return [False], [False]
        root = self._tree('xl/styles.xml')
        formats = dict(BUILTIN_FORMATS)
        custom = root.find(M+'numFmts')
        if custom is not None:
            for item in custom:
                key = int(item.get('numFmtId','-1'))
                if key in formats and formats[key] != item.get('formatCode'):
                    raise EvidenceError('duplicate/conflicting number formats')
                formats[key] = item.get('formatCode','')
        xfs = root.find(M+'cellXfs')
        codes = [formats.get(int(x.get('numFmtId','0')),'') for x in xfs] if xfs is not None else ['']
        # Quoted/escaped percent signs are literal; an active percent format changes display scale.
        stripped = [re.sub(r'"[^"\n]*"|\\.|\[[^\]]*\]', '', code) for code in codes]
        return [is_date_format(code) for code in codes], ['%' in code for code in stripped]

    def _sheets(self) -> dict[str,str]:
        relationships: dict[str,str] = {}
        for item in self._tree('xl/_rels/workbook.xml.rels'):
            rid, target = item.get('Id'), item.get('Target','')
            if not rid or rid in relationships:
                raise EvidenceError('duplicate or missing workbook relationship ID')
            path = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
            if path.startswith('../') or '\\' in path or ':' in path:
                raise EvidenceError('unsafe internal workbook relationship')
            relationships[rid] = path
        result = {}
        root = self._tree('xl/workbook.xml')
        sheets = root.find(M+'sheets')
        if sheets is None or len(root.findall(M+'sheets')) != 1:
            raise EvidenceError('unsupported or ambiguous workbook sheet collection')
        for sheet in sheets:
            name, rid = sheet.get('name'), sheet.get(R+'id')
            if not name or name in result or rid not in relationships:
                raise EvidenceError('ambiguous sheet name or relationship')
            if relationships[rid] in result.values():
                raise EvidenceError('multiple sheet names refer to the same physical worksheet')
            result[name] = relationships[rid]
        return result

    def _cell(self, element: ET.Element) -> Cell:
        address, typ = element.get('r',''), element.get('t','n')
        if any(len(element.findall(M+tag)) > 1 for tag in ('v','f','is')):
            raise EvidenceError('ambiguous duplicate cell payload')
        formula = element.find(M+'f') is not None
        value = element.find(M+'v')
        text = value.text if value is not None else None
        style = int(element.get('s','0'))
        if style<0 or style>=len(self.date_styles):
            raise EvidenceError('cell style index is invalid')
        if formula:
            return Cell(address,'formula',None,True)
        if typ in ('s','inlineStr','str'):
            if typ == 's':
                index = int(text) if text is not None else -1
                if index<0 or index>=len(self.strings):
                    raise EvidenceError('shared string index is invalid')
                result = self.strings[index]
            elif typ == 'inlineStr':
                inline = element.find(M+'is')
                result = _text(inline) if inline is not None else ''
            else:
                result = text or ''
            if len(result)>self.limits['text_length']:
                raise EvidenceError('cell text budget exceeded')
            return Cell(address,'text',result)
        if typ in ('b','d','e'):
            return Cell(address,{'b':'boolean','d':'date','e':'error'}[typ],text)
        if typ != 'n':
            raise NeedsReview('unsupported OOXML cell type')
        if self.date_styles[style]:
            return Cell(address,'date',text)
        if self.percent_styles[style]:
            return Cell(address,'percent_formatted_number',text)
        return Cell(address,'number',number(text,self.contract)) if text is not None else Cell(address,'missing',None)

    def rows(self, sheet: str) -> dict[int,dict[int,Cell]]:
        if sheet not in self.sheets:
            raise EvidenceError('requested sheet is missing')
        if sheet in self._rows:
            return self._rows[sheet]
        path = self.sheets[sheet]
        if path not in self.parts:
            raise EvidenceError('sheet XML is missing')
        rows, merges = {}, []
        root = self._tree(path)
        if root.tag != M+'worksheet' or len(root.findall(M+'sheetData')) != 1:
            raise EvidenceError('unsupported or ambiguous worksheet structure')
        stack = []
        for event,el in ET.iterparse(io.BytesIO(self.parts[path]),events=('start','end')):
            if event == 'start':
                stack.append(el.tag)
                continue
            if el.tag == M+'row':
                if len(stack) != 3 or stack[-2] != M+'sheetData':
                    raise EvidenceError('worksheet row is outside its unique sheetData')
                row = int(el.get('r','0'))
                if row in rows:
                    raise EvidenceError('duplicate physical row index')
                items = {}
                for child in el.findall(M+'c'):
                    col, own_row = _column(child.get('r',''))
                    if col in items or own_row != row:
                        raise EvidenceError('duplicate/misaligned cell coordinates')
                    items[col] = self._cell(child)
                rows[row] = items
                el.clear()
            elif el.tag == M+'mergeCell':
                endpoints = el.get('ref','').split(':')
                if len(endpoints)!=2:
                    raise EvidenceError('malformed merged range')
                c1,r1 = _column(endpoints[0]);c2,r2 = _column(endpoints[1])
                if c1>c2 or r1>r2:raise EvidenceError('reversed merged range')
                merges.append((c1,r1,c2,r2));el.clear()
            stack.pop()
        self._rows[sheet],self._merges[sheet] = rows,merges
        return rows

    def select(self, selector: Mapping[str,Any], profiles: list) -> tuple[Value,dict[str,Any]]:
        sheet, header_row = selector['sheet'], selector['header_row']
        if type(header_row) is not int or type(selector['expected_cardinality']) is not int:
            raise EvidenceError('header/cardinality require strict integers')
        rows = self.rows(sheet)
        if header_row not in rows:
            raise EvidenceError('header row is missing')
        headers: dict[str,int] = {}
        for col,cell in rows[header_row].items():
            if cell.formula:
                raise NeedsReview('formula header cannot establish a column name')
            if cell.kind=='missing' or cell.value=='':
                continue
            if cell.kind!='text' or cell.value in headers:
                raise EvidenceError('nontext or duplicate header')
            headers[cell.value] = col
        wanted = [*selector['row_key'],*selector['identity_columns'].values()]
        value_names = [selector['value_column']] if selector['value_type']!='interval' else [selector['lower_column'],selector['upper_column']]
        wanted += value_names
        if selector.get('unit',{}).get('kind')=='column':wanted.append(selector['unit']['column'])
        if any(name not in headers for name in wanted):
            raise EvidenceError('required exact column header is missing')
        if any(c1 <= headers[name] <= c2 and r1 <= header_row <= r2
               for name in wanted for c1,r1,c2,r2 in self._merges[sheet]):
            raise NeedsReview('required header occupies an ambiguous merged range')
        def observed(row: int,name: str) -> Cell:
            col = headers[name]
            if any(c1<=col<=c2 and r1<=row<=r2 for c1,r1,c2,r2 in self._merges[sheet]):
                raise NeedsReview('selected/header merged cells are ambiguous')
            cell = rows[row].get(col,Cell('', 'missing', None))
            if cell.formula:raise NeedsReview('selected formula has no verified computation evidence')
            return cell
        matches = []
        for row in sorted(rows):
            if row<=header_row:continue
            ok = True
            for key,expected in selector['row_key'].items():
                cell = observed(row,key)
                if isinstance(expected,str):same=cell.kind=='text' and cell.value==expected
                else:same=cell.kind=='number' and cell.value==number(expected,self.contract)
                ok = ok and same
            if ok:matches.append(row)
        if len(matches)!=1:
            raise EvidenceError(f'row selector cardinality is {len(matches)}, expected exactly 1')
        row=matches[0]; identity={}
        for axis,name in selector['identity_columns'].items():
            cell=observed(row,name)
            if cell.kind not in ('text','number') or cell.value in ('',None):
                raise NeedsReview('identity axis has unknown or unsupported cell value')
            identity[axis]=cell.value
        if not isinstance(identity['metric'],str):raise EvidenceError('metric identity must be text')
        cells=[observed(row,name) for name in value_names];kind=selector['value_type']
        if kind=='categorical':
            if cells[0].kind!='text':raise NeedsReview('categorical selection requires text')
            value=cells[0].value
        else:
            if any(c.kind!='number' for c in cells):raise NeedsReview('numeric selection cannot coerce string/bool/date/error/missing or ambiguous percent display scale')
            value=cells[0].value if kind=='scalar' else tuple(c.value for c in cells)
            if kind=='interval' and value[0]>value[1]:raise EvidenceError('interval lower bound exceeds upper bound')
        unit=self._unit(selector,identity,observed,row,value_names,headers,profiles)
        addresses=[x.address for x in cells]
        origin=self.sha256+'|'+sheet+'|'+','.join(addresses)
        return Value(kind,value,unit,identity,frozenset({origin})),{'sheet':sheet,'row':row,'cells':addresses,
            'observed_axes':list(identity),'unverified_axes':[x for x in ('scenario','sample','statistic','time') if x not in identity]}

    def _unit(self, selector, identity, observed, row, names, headers, profiles) -> str:
        spec=selector.get('unit',{});kind=spec.get('kind')
        if kind=='not_applicable' and selector['value_type']=='categorical':return 'not_applicable'
        candidates=[]
        for name in names:
            match=re.search(r'(?:\[([^\[\]]+)\]|\(([^()]+)\)|（([^（）]+)）)$',name)
            if match:candidates.append(next(x for x in match.groups() if x is not None).strip())
        header_units = list(candidates)
        for name in ('unit','单位'):
            if name in headers:
                cell=observed(row,name)
                if cell.kind=='text' and cell.value.strip():candidates.append(cell.value)
        if kind=='column':
            cell=observed(row,spec['column'])
            if cell.kind!='text' or not cell.value.strip():raise NeedsReview('unit column is unknown')
            unit=cell.value
        elif kind=='header':
            if len(header_units)!=len(names):raise NeedsReview('unit is not explicit in numeric header')
            unit=header_units[0]
        elif kind=='numeric_profile':
            unit=current_profile(profiles,spec['profile_id'],identity['metric']).get('unit')
        else:
            raise NeedsReview('unit_unknown: no supported explicit unit source')
        unit_info(unit,self.contract)
        if any(unit_info(c,self.contract)!=unit_info(unit,self.contract) for c in candidates):
            raise EvidenceError('profile/header/unit column conflict')
        return unit
