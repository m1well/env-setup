"""Database design: how the entities relate to each other and to the migrated schema."""
from __future__ import annotations

import re
import sys

from .core import Repo, balanced, define, is_test_path, profile_kind
from .extract import entity as entity_x

define('DB-CASCADE-TO-PARENT', 'cascade REMOVE/ALL towards a parent or a shared row', 'high', 'persistence',
       'Deleting the child deletes the parent - or, on ManyToMany, rows other owners still point to.')
define('DB-TWO-OWNERS', 'Both sides of one relation own it', 'high', 'persistence',
       'Two mappings for one relationship: Hibernate writes a join table and a foreign key, or two foreign '
       'keys, and they drift apart. One side gets mappedBy.')
define('DB-ONETOMANY-JOINTABLE', 'Unidirectional @OneToMany without @JoinColumn', 'medium', 'persistence',
       'Hibernate maps it through a join table nobody planned. mappedBy on a @ManyToOne back reference, or '
       '@JoinColumn on this side.')
define('DB-MANYTOMANY', '@ManyToMany relation', 'low', 'persistence',
       'A join table cannot carry data (since when, by whom, which role) - the first such requirement turns it '
       'into an entity. As a List it is a bag: every change deletes and reinserts all rows; use a Set.')
define('DB-MONEY-FLOAT', 'Money stored as floating point', 'high', 'persistence',
       'double cannot represent 0.10 - sums drift by cents. BigDecimal plus a currency.', rule='MODEL-9')
define('DB-NO-VERSION', 'Entities without @Version', 'low', 'persistence',
       'Two users saving the same row: the second save silently wins. Only rows that concurrent requests write '
       'need one.', rule='MODEL-10')
define('DB-NO-UNIQUE-KEY', 'Business key without a unique constraint', 'medium', 'persistence',
       'An email, number or slug that must be unique is only checked in code - two parallel requests create '
       'the duplicate. A unique constraint (per tenant, if scoped) in the migration.')
define('DB-TIMESTAMP-NO-TZ', 'Point in time stored without time zone', 'low', 'persistence',
       'LocalDateTime/Date map to timestamp without time zone - the value changes meaning when a server or '
       'a user sits in another zone. Instant or OffsetDateTime.')
define('DB-FK-NO-INDEX', 'Foreign key column without an index (PostgreSQL)', 'medium', 'persistence',
       'PostgreSQL does not index foreign keys. Every delete on the parent scans the child table, every join '
       'by that column too. A small lookup table is fine.', rule='MIG-7')
define('DB-ENTITY-NO-TABLE', 'Entity whose table no migration creates', 'medium', 'persistence',
       'The entity maps to a table that only ddl-auto would create - or the name differs from the migration.',
       rule='MIG-1')
define('DB-COLUMN-DRIFT', 'Entity columns the migrations do not create', 'medium', 'persistence',
       'Without ddl-auto validate this shows up as an SQL error on the first query that touches the column.',
       rule='MIG-10')
define('DB-NO-VALIDATE', 'Migrations without ddl-auto validate', 'low', 'persistence',
       'validate is the free check that entities and migrated schema agree - at startup instead of at the '
       'first query.', rule='MIG-10')

RELATIONS = ('OneToMany', 'ManyToOne', 'OneToOne', 'ManyToMany', 'ElementCollection')
MONEY = re.compile(r'(?i)(price|preis|amount|betrag|summe|sum$|total|cost|kosten|gebuehr|gebühr|fee|salary|gehalt|'
                   r'lohn|netto|brutto|net$|gross|steuer|tax|discount|rabatt|balance|saldo|honorar|umsatz|revenue)')
OWN_KEY = re.compile(r'(?i)^(slug|nummer|number|kennung|external_?id|keycloak_?id|subject|token)$')
LOGIN_KEY = re.compile(r'(?i)^(e_?mail|username|benutzername|login)$')
RANDOM_INIT = re.compile(r'randomUUID\s*\(|SecureRandom|RandomStringUtils|nanoid|random\w*Token|generate\w*Token')
IDENTITY = re.compile(r'(?i)(user|benutzer|account|konto|member|mitglied|mitarbeiter|employee|person|kunde|customer)$')
TWO_SIDED = {frozenset(('OneToMany', 'ManyToOne')), frozenset(('ManyToMany',)), frozenset(('OneToOne',))}
COLLECTION_LIST = re.compile(r'^(Mutable)?(List|Collection|ArrayList|Iterable)\b')
COLLECTION_SET = re.compile(r'^(Mutable)?(Set|HashSet|LinkedHashSet|SortedSet|TreeSet)\b')


def _business_key(entity: str, prop: str) -> bool:
    col = entity_x.snake(prop)
    if OWN_KEY.match(col):
        return True
    if LOGIN_KEY.match(col):
        return bool(IDENTITY.search(re.sub(r'(Entity|Jpa|Persistence|Record|Row|Data)$', '', entity)[-12:]))
    own = re.match(r'(?i)([a-z]+?)(nummer|_number|number)$', prop)
    return bool(own) and entity.lower().startswith(own.group(1).lower().rstrip('s'))


def _anno_args(anno_code: str, name: str) -> str | None:
    m = re.search(r'@(?:\w+:)?' + name + r'\b', anno_code)
    if not m:
        return None
    k = m.end()
    while k < len(anno_code) and anno_code[k] in ' \t':
        k += 1
    if anno_code[k:k + 1] != '(':
        return ''
    close = balanced(anno_code, k)
    return anno_code[k + 1:close if close > 0 else len(anno_code)]


def _props(j, cls) -> list[dict]:
    out = []
    for p in cls.params if j.kotlin else []:
        at = j.src.text.find(p.code, cls.offset)
        out.append({'name': p.name, 'type': p.type, 'annos': p.annos, 'anno_code': p.code,
                    'line': j.src.line_at(at) if at >= 0 else cls.line})
    for m in j.members:
        if m.kind == 'field' and m.owner is cls and not re.search(r'\b(static|const|companion)\b', m.sig):
            line_text = j.src.line(m.line)
            if j.kotlin and re.search(r'\bget\s*\(\s*\)|\bby\s+\w', line_text):
                continue
            out.append({'name': m.name, 'type': m.returns, 'annos': m.annos, 'anno_code': m.anno_code + m.sig_code,
                        'line': m.line})
    return out


def _column(p: dict) -> str | None:
    if {'Transient', 'OneToMany', 'ManyToMany', 'ElementCollection', 'Embedded', 'EmbeddedId'} & set(p['annos']) or \
            re.search(r'mappedBy\s*=', p['anno_code']):
        return None
    named = re.search(r'name\s*=\s*"(\w+)"', _anno_args(p['anno_code'], 'Column') or
                      _anno_args(p['anno_code'], 'JoinColumn') or '')
    if named:
        return named.group(1).lower()
    return entity_x.snake(p['name']) + ('_id' if {'ManyToOne', 'OneToOne'} & set(p['annos']) else '')


def _looked_up(ctx, entity: str, table: str, prop: str, col: str) -> bool:
    finder = re.compile(r'By\w*' + prop[0].upper() + prop[1:] + r'(?![a-z])')
    query = re.compile(r'(?i)\b(?:from|update|join)\s+(?:' + entity + '|' + table + r')\b[^"]*?\b(?:\w+\.)?(?:'
                       + prop + '|' + col + r')\s*=\s*[:?]')
    return any(query.search(j.src.code) or any(
        c.body and re.search(r'Repository\s*<\s*' + entity + r'\b', c.header) and
        finder.search(j.src.code[c.body[0]:c.body[1]]) for c in j.classes) for j in ctx.main)


def _target(prop: dict) -> str:
    explicit = re.search(r'targetEntity\s*=\s*(\w+)(?:::class|\.class)', prop['anno_code'])
    if explicit:
        return explicit.group(1)
    t = prop['type'].replace('?', '')
    generic = re.search(r'<\s*(?:out\s+)?([\w.]+)\s*>', t)
    return (generic.group(1) if generic else t.strip()).split('.')[-1]


def relations(j, cls) -> list[dict]:
    out = []
    for p in _props(j, cls):
        kind = next((r for r in RELATIONS if r in p['annos']), None)
        if not kind:
            continue
        args = _anno_args(p['anno_code'], kind) or ''
        cascade = re.search(r'cascade\s*=\s*[\[{(]?([^\])}]*)', args)
        mapped = re.search(r'mappedBy\s*=\s*"(\w+)"', args)
        coll = 'list' if COLLECTION_LIST.match(p['type'].strip()) else 'set' if COLLECTION_SET.match(p['type'].strip()) \
            else None
        out.append({'prop': p['name'], 'kind': kind, 'target': _target(p), 'mapped_by': mapped.group(1) if mapped else None,
                    'cascade': re.findall(r'\b(ALL|REMOVE|PERSIST|MERGE|DETACH|REFRESH)\b', cascade.group(1)) if cascade else [],
                    'orphan': bool(re.search(r'orphanRemoval\s*=\s*true', args)),
                    'join_column': 'JoinColumn' in p['annos'] or 'JoinColumns' in p['annos'],
                    'join_table': 'JoinTable' in p['annos'], 'coll': coll, 'line': p['line']})
    return out


def _entity(j, cls) -> tuple[list[dict], str | None, list[str]]:
    """Columns, explicit table and supertypes of one entity class - entity_x only reads the first one of a file."""
    text = j.src.text
    table = re.search(r'@Table\s*\(\s*(?:name\s*=\s*)?"([^"]+)"', cls.anno_code)
    if j.kotlin:
        supertypes = [s for s in entity_x.supertypes_of(cls.header.split('{')[0]) if s]
    else:
        ext = re.search(r'\bextends\s+(\w+)', cls.header)
        supertypes = [ext.group(1)] if ext else []
    cols = []
    if j.kotlin:
        for part in entity_x.top_level_parts(entity_x.primary_constructor(text, cls.offset)):
            flat = re.sub(r'\s+', ' ', part).strip()
            m = entity_x.KT_PROP.search(flat)
            col = entity_x.column(flat, m.group(1), m.group(2)) if m else None
            if col:
                cols.append(col)
    if cls.body:
        cols += entity_x.body_columns(text.splitlines(), text.count('\n', 0, cls.offset), not j.kotlin)
    return cols, table.group(1) if table else None, supertypes


def _strip_sql(text: str) -> str:
    text = re.sub(r'\$(\w*)\$[\s\S]*?\$\1\$', lambda m: re.sub(r'[^\n]', ' ', m.group()), text)
    text = re.sub(r'/\*[\s\S]*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group()), text)
    return re.sub(r'--[^\n]*', lambda m: ' ' * len(m.group()), text)


def _name(raw: str) -> str:
    return raw.strip().strip('"`[]').split('.')[-1].strip('"`[]').lower()


def _split(text: str) -> list[tuple[int, str]]:
    parts, depth, start, quoted = [], 0, 0, False
    for i, ch in enumerate(text):
        if ch == "'":
            quoted = not quoted
        elif quoted:
            continue
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append((start, text[start:i]))
            start = i + 1
    parts.append((start, text[start:]))
    return [(s, p) for s, p in parts if p.strip()]


def _cols(raw: str) -> tuple[str, ...]:
    return tuple(_name(c.split()[0]) for c in raw.split(',') if c.strip())


CHECK_IN = re.compile(r'\bcheck\s*\(\s*\(?\s*([\w"`]+)\s*\)?\s+in\s*\(([^)]*)\)')
ON_DELETE = re.compile(r'\bon\s+delete\s+(cascade|set\s+null|set\s+default|restrict|no\s+action)')


def migrations(repo: Repo) -> dict:
    files = sorted(f for f in repo.files if f.endswith('.sql') and not is_test_path(f) and
                   re.search(r'(^|/)(db/migration|db/changelog|migrations?|flyway|liquibase)/', f))
    tables: dict[str, dict] = {}

    def table(name):
        return tables.setdefault(name, {'columns': set(), 'fks': [], 'indexed': set(), 'unique': [], 'file': None,
                                        'types': {}, 'where': {}, 'checks': [], 'ondelete': [], 'pk': set(),
                                        'notnull': set(), 'rls': None, 'force': False})

    def details(t, item, rel, line, name=None, ref=None, cols=None):
        for col, values in CHECK_IN.findall(item):
            t['checks'].append((_name(col), re.findall(r"'([^']*)'", values), rel, line))
        action = ON_DELETE.search(item)
        if ref and action:
            t['ondelete'].append((cols or (name,), ref, re.sub(r'\s+', ' ', action.group(1))))
        typ = re.match(r'[\w"`]+\s+(\w+)', item) if name else None
        if typ:
            t['types'][name] = typ.group(1)
            t['where'][name] = (rel, line)

    for rel in files:
        src = repo.source(rel)
        text = _strip_sql(src.text)
        low = text.lower()
        pos = 0
        for stmt in low.split(';'):
            start = pos
            pos += len(stmt) + 1
            s = stmt.strip()
            s_at = start + len(stmt) - len(stmt.lstrip())
            line = src.line_at(s_at)
            ct = re.match(r'create\s+(?:unlogged\s+|temp\w*\s+)?table\s+(?:if\s+not\s+exists\s+)?([\w."`]+)\s*\(', s)
            if ct:
                t = table(_name(ct.group(1)))
                t['file'] = t['file'] or f'{rel}:{line}'
                body_start = ct.end() - 1
                close = balanced(s, body_start)
                for istart, raw in _split(s[body_start + 1:close if close > 0 else len(s)]):
                    item = raw.strip()
                    item_line = src.line_at(s_at + body_start + 1 + istart + len(raw) - len(raw.lstrip()))
                    con = re.match(r'(?:constraint\s+\S+\s+)?(primary\s+key|unique|foreign\s+key)\s*'
                                   r'(?:nulls\s+(?:not\s+)?distinct\s*)?\(([^)]*)\)(?:\s*references\s+([\w."`]+))?', item)
                    if con:
                        cols = _cols(con.group(2))
                        if con.group(1).startswith('primary'):
                            t['pk'] |= set(cols)
                            t['notnull'] |= set(cols)
                        if con.group(1).startswith('primary') or con.group(1) == 'unique':
                            t['indexed'].add(cols[0])
                            t['unique'].append(cols)
                        else:
                            t['fks'].append((cols, _name(con.group(3) or '?'), rel, item_line))
                            details(t, item, rel, item_line, ref=_name(con.group(3) or '?'), cols=cols)
                        continue
                    if re.match(r'(check|exclude|constraint)\b', item):
                        details(t, item, rel, item_line)
                        continue
                    col = re.match(r'([\w"`]+)\s+\w', item)
                    if not col:
                        continue
                    name = _name(col.group(1))
                    t['columns'].add(name)
                    pk = re.search(r'\bprimary\s+key\b', item)
                    if pk:
                        t['pk'].add(name)
                    if pk or re.search(r'\bnot\s+null\b', item):
                        t['notnull'].add(name)
                    if pk or re.search(r'\bunique\b', item):
                        t['indexed'].add(name)
                        t['unique'].append((name,))
                    ref = re.search(r'\breferences\s+([\w."`]+)', item)
                    if ref:
                        t['fks'].append(((name,), _name(ref.group(1)), rel, item_line))
                    details(t, item, rel, item_line, name=name, ref=_name(ref.group(1)) if ref else None)
                continue
            at = re.match(r'alter\s+table\s+(?:only\s+)?(?:if\s+exists\s+)?([\w."`]+)\s+([\s\S]*)', s)
            if at:
                t = table(_name(at.group(1)))
                for _, action in _split(at.group(2)):
                    action = action.strip()
                    ren = re.match(r'rename\s+to\s+([\w."`]+)', action)
                    if ren:
                        tables[_name(ren.group(1))] = tables.pop(_name(at.group(1)))
                        break
                    rc = re.match(r'rename\s+column\s+([\w"`]+)\s+to\s+([\w"`]+)', action)
                    if rc:
                        t['columns'].discard(_name(rc.group(1)))
                        t['columns'].add(_name(rc.group(2)))
                        for key in ('types', 'where'):
                            if _name(rc.group(1)) in t[key]:
                                t[key][_name(rc.group(2))] = t[key].pop(_name(rc.group(1)))
                        continue
                    dc = re.match(r'drop\s+column\s+(?:if\s+exists\s+)?([\w"`]+)', action)
                    if dc:
                        t['columns'].discard(_name(dc.group(1)))
                        continue
                    rls = re.match(r'(enable|disable|force|no\s+force)\s+row\s+level\s+security', action)
                    if rls:
                        verb = rls.group(1)
                        if verb in ('enable', 'disable'):
                            t['rls'] = f'{rel}:{line}' if verb == 'enable' else None
                        else:
                            t['force'] = verb == 'force'
                        continue
                    nn = re.match(r'alter\s+(?:column\s+)?([\w"`]+)\s+set\s+not\s+null', action)
                    if nn:
                        t['notnull'].add(_name(nn.group(1)))
                        continue
                    con = re.match(r'add\s+(?:constraint\s+\S+\s+)?(primary\s+key|unique|foreign\s+key)\s*'
                                   r'(?:nulls\s+(?:not\s+)?distinct\s*)?\(([^)]*)\)(?:\s*references\s+([\w."`]+))?', action)
                    if con:
                        cols = _cols(con.group(2))
                        if con.group(1).startswith('foreign'):
                            t['fks'].append((cols, _name(con.group(3) or '?'), rel, line))
                            details(t, action, rel, line, ref=_name(con.group(3) or '?'), cols=cols)
                        else:
                            if con.group(1).startswith('primary'):
                                t['pk'] |= set(cols)
                            t['indexed'].add(cols[0])
                            t['unique'].append(cols)
                        continue
                    add = re.match(r'add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?([\w"`]+)\s+\w', action)
                    if add and _name(add.group(1)) not in ('constraint', 'primary', 'unique', 'foreign'):
                        name = _name(add.group(1))
                        t['columns'].add(name)
                        ref = re.search(r'\breferences\s+([\w."`]+)', action)
                        if ref:
                            t['fks'].append(((name,), _name(ref.group(1)), rel, line))
                        pk = re.search(r'\bprimary\s+key\b', action)
                        if pk or re.search(r'\bunique\b', action):
                            t['indexed'].add(name)
                            t['unique'].append((name,))
                        if pk:
                            t['pk'].add(name)
                        if pk or re.search(r'\bnot\s+null\b', action):
                            t['notnull'].add(name)
                        details(t, re.sub(r'^add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?', '', action), rel, line,
                                name=name, ref=_name(ref.group(1)) if ref else None)
                        continue
                    if re.match(r'add\s+(?:constraint\s+\S+\s+)?check\b', action):
                        details(t, action, rel, line)
                continue
            ix = re.match(r'create\s+(unique\s+)?index\s+(?:concurrently\s+)?(?:if\s+not\s+exists\s+)?(?:[\w"`]+\s+)?'
                          r'on\s+(?:only\s+)?([\w."`]+)\s*(?:using\s+\w+\s*)?\(([^)]*)\)', s)
            if ix:
                t = table(_name(ix.group(2)))
                cols = tuple(_name(re.sub(r'\s+(asc|desc|nulls\s+\w+)$', '', c.strip())) for c in ix.group(3).split(',')
                             if c.strip())
                if cols:
                    t['indexed'].add(cols[0])
                    if ix.group(1):
                        t['unique'].append(cols)
                continue
            dt = re.match(r'drop\s+table\s+(?:if\s+exists\s+)?([\w."`, ]+)', s)
            if dt:
                for name in dt.group(1).split(','):
                    tables.pop(_name(name), None)
    return {'files': files, 'tables': tables}


def run(ctx) -> dict:
    hits, repo = ctx.hits, ctx.repo
    entities = [(j, c) for j in ctx.main for c in j.classes if c.has('Entity')]
    if not entities:
        return {}
    postgres = bool(re.search(r'postgresql|org\.postgresql|r2dbc-postgres', ctx.build, re.I))
    mig = migrations(repo)
    ctx.migrations = mig
    tables = mig['tables']
    validate = any(e.norm.endswith('hibernate.ddlauto') and e.value.lower() == 'validate'
                   for src, entries in ctx.configs if not is_test_path(src.rel) for e in entries
                   if profile_kind(e.profile) != 'dev')
    if tables and not validate:
        rel = next((s.rel for s, _ in ctx.configs if not is_test_path(s.rel)), None)
        hits.add('DB-NO-VALIDATE', rel, None, f'{len(entities)} entities, {len(mig["files"])} migration files, '
                                              'spring.jpa.hibernate.ddl-auto is not validate')

    by_name = {c.name for _, c in entities}
    rels = {c.name: relations(j, c) for j, c in entities}
    no_version, inventory, no_tz, owned_twice = [], [], {}, set()
    for j, cls in entities:
        name = cls.name
        try:
            cols, table, supertypes = _entity(j, cls)
        except Exception as exc:  # the vendored extractor must never stop a scan
            print(f'  entity extractor failed on {j.rel}: {exc}', file=sys.stderr)
            cols, table, supertypes = [], None, []
        table_name = (table or entity_x.snake(name)).lower()
        props = _props(j, cls)
        for r in rels[name]:
            if r['kind'] in ('ManyToOne', 'ManyToMany') and {'ALL', 'REMOVE'} & set(r['cascade']):
                hits.add('DB-CASCADE-TO-PARENT', j.rel, r['line'],
                         f'{name}.{r["prop"]}: @{r["kind"]}(cascade = {", ".join(r["cascade"])}) -> {r["target"]}')
            if r['kind'] == 'OneToMany' and not r['mapped_by'] and not r['join_column'] and not r['join_table']:
                hits.add('DB-ONETOMANY-JOINTABLE', j.rel, r['line'], f'{name}.{r["prop"]}: @OneToMany -> {r["target"]}, '
                                                                     'no mappedBy, no @JoinColumn')
            if r['kind'] == 'ManyToMany':
                hits.add('DB-MANYTOMANY', j.rel, r['line'], f'{name}.{r["prop"]}: @ManyToMany -> {r["target"]}'
                         + (' as a List' if r['coll'] == 'list' else ''),
                         severity='medium' if r['coll'] == 'list' else None)
            if r['mapped_by'] or r['target'] == name:
                continue
            for o in rels.get(r['target'], []):
                key = frozenset((f'{name}.{r["prop"]}', f'{r["target"]}.{o["prop"]}'))
                if o['target'] != name or o['mapped_by'] or key in owned_twice or \
                        frozenset((r['kind'], o['kind'])) not in TWO_SIDED or \
                        any(x['kind'] == 'OneToMany' and x['join_column'] for x in (r, o)):
                    continue
                owned_twice.add(key)
                hits.add('DB-TWO-OWNERS', j.rel, r['line'],
                         f'{name}.{r["prop"]} (@{r["kind"]}) and {r["target"]}.{o["prop"]} (@{o["kind"]}) - '
                         'neither side has mappedBy')
        for p in props:
            if re.fullmatch(r'(Double|Float|double|float|kotlin\.Double)\??', p['type'].strip()) and MONEY.search(p['name']):
                hits.add('DB-MONEY-FLOAT', j.rel, p['line'], f'{name}.{p["name"]}: {p["type"]}')
        if not any('Version' in p['annos'] for p in props) and not re.search(r'@Version\b', j.src.bare):
            no_version.append((j.rel, name))
        stamps = [c['name'] for c in cols if c['type'] == 'timestamp']
        if stamps:
            no_tz[(j.rel, name)] = stamps
        t = tables.get(table_name)
        keys = [p for p in props if _business_key(name, p['name']) and
                not {'Id', 'OneToMany', 'ManyToMany', 'Transient', 'NaturalId'} & set(p['annos'])]
        unique_text = _anno_args(cls.anno_code, 'Table') or ''
        missing = []
        for p in keys:
            col = _column(p) or entity_x.snake(p['name'])
            if re.search(r'unique\s*=\s*true', _anno_args(p['anno_code'], 'Column') or ''):
                continue
            if 'uniqueConstraints' in unique_text and re.search(r'"' + col + r'"', unique_text):
                continue
            if t and any(col in u for u in t['unique']):
                continue
            if RANDOM_INIT.search(p['anno_code']) and not _looked_up(ctx, name, table_name, p['name'], col):
                continue
            if tables and not t:
                continue
            missing.append((p, col))
        if missing:
            hits.add('DB-NO-UNIQUE-KEY', j.rel, missing[0][0]['line'],
                     f'{name}: {", ".join(c for _, c in missing)} not unique in code or migrations')
        if tables:
            subclass = any(s in by_name for s in supertypes)
            if not t and not subclass and not re.search(r'@SecondaryTable|@Subselect|@Immutable', j.src.bare):
                hits.add('DB-ENTITY-NO-TABLE', j.rel, cls.line,
                         f'{name} -> table {table_name}, created in none of {len(mig["files"])} migration files')
            elif t and not validate and not re.search(r'@SecondaryTable|@Formula|@AttributeOverride', j.src.bare):
                drift = [c['name'] for c in cols if not c['name'].startswith('-- ') and c['name'].lower() not in t['columns']]
                if drift:
                    hits.add('DB-COLUMN-DRIFT', j.rel, cls.line,
                             f'{name} ({table_name}): {", ".join(drift[:8])} not in the migrated table')
        inventory.append({'entity': name, 'table': table_name, 'file': j.rel, 'columns': len(cols),
                          'relations': [{k: r[k] for k in ('prop', 'kind', 'target', 'mapped_by', 'cascade', 'coll')}
                                        for r in rels[name]],
                          'version': (j.rel, name) not in no_version, 'in_migrations': bool(t),
                          'props': {p['name']: c for p in props for c in [_column(p)] if c},
                          'version_prop': next((p['name'] for p in props if 'Version' in p['annos']), None),
                          'mutable': [p['name'] for p in props if re.search(r'\bvar\b', p['anno_code']) or
                                      not j.kotlin and not re.search(r'\bfinal\b', p['anno_code'])],
                          'not_updatable': [p['name'] for p in props if re.search(
                              r'updatable\s*=\s*false', _anno_args(p['anno_code'], 'Column') or '')],
                          'dynamic_update': 'DynamicUpdate' in cls.annos})
    if no_version and len(entities) >= 3:
        hits.add('DB-NO-VERSION', no_version[0][0], None,
                 f'{len(no_version)} of {len(entities)} entities without @Version: '
                 + ', '.join(n for _, n in no_version[:10]), files=sorted({f for f, _ in no_version})[:40])
    if no_tz:
        top = sorted(no_tz.items(), key=lambda kv: -len(kv[1]))
        hits.add('DB-TIMESTAMP-NO-TZ', top[0][0][0], None,
                 f'{sum(len(v) for v in no_tz.values())} columns in {len(no_tz)} of {len(entities)} entities: '
                 + '; '.join(f'{n} ({", ".join(v[:3])})' for (_, n), v in top[:5]),
                 files=sorted({f for f, _ in no_tz})[:40])
    if postgres:
        for name, t in tables.items():
            for cols, ref, rel, line in t['fks']:
                if cols and cols[0] not in t['indexed']:
                    hits.add('DB-FK-NO-INDEX', rel, line, f'{name}.{", ".join(cols)} -> {ref}')
    return {'entities': inventory, 'migrations': {'files': len(mig['files']), 'tables': len(tables),
                                                  'foreign_keys': sum(len(t['fks']) for t in tables.values()),
                                                  'engine': 'postgresql' if postgres else None, 'validate': validate}}
