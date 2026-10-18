#!/usr/bin/env python3
"""Table, columns, PK/FK and supertypes of every @Entity, as json.

    python3 entity.py $(rg -l '^@Entity\b' --glob '**/*.kt') > /tmp/entities.json

Forty entities with eight columns each is not something you type by hand, and it is
not something a single regex gets right either: columns live in the primary
constructor *or* in the class body, `lateinit var` and `@Type` properties look
different from the rest, and the audit columns are not in the file at all - they come
from the `@MappedSuperclass` base.

So this reads both places and reports what it saw:

    "supertypes": ["BaseEntityWithUpdateAudit"]   <- resolve it, prepend its columns
    "inheritance": true                           <- @Inheritance(JOINED): the child
                                                     table carries only its own
                                                     columns plus the inherited id

Two things go to stderr, and both mean the model is not finished:

**Zero columns means the extraction failed**, never that the table is empty. Open
that file.

**A type printed as `? IracingTeam`** could not be mapped to a db type. That is an
`@Converter(autoApply = true)`, an `@Embeddable` or an enum with no `@Enumerated` -
read the converter and fill the real type in. Lowercasing the Kotlin type instead
(`iracingteam`) is what this used to do, and it reads like a column type to everyone
who opens the picture.
"""
import json
import re
import sys
import pathlib

SQL = {
    'UUID': 'uuid', 'String': 'text', 'StringValue': 'text', 'DateValue': 'date',
    'Instant': 'timestamptz', 'OffsetDateTime': 'timestamptz', 'ZonedDateTime': 'timestamptz',
    'LocalDate': 'date', 'LocalDateTime': 'timestamp', 'LocalTime': 'time',
    'Boolean': 'boolean', 'boolean': 'boolean', 'Int': 'integer', 'Integer': 'integer',
    'int': 'integer', 'Long': 'bigint', 'long': 'bigint', 'Short': 'smallint',
    'BigDecimal': 'numeric', 'BigInteger': 'numeric', 'Double': 'double precision',
    'double': 'double precision', 'Float': 'real', 'ByteArray': 'bytea', 'byte[]': 'bytea',
    'Char': 'char', 'char': 'char', 'Date': 'timestamp', 'URI': 'text', 'URL': 'text',
    'Locale': 'text', 'Currency': 'text',
}
# a type that is not in that table is not a db type, and lowercasing it does not make
# it one: `IracingTeam` printed as `iracingteam` looks like a column type and passes
# every eye. It is marked instead, and the marker has to be gone before the model is
# written - see the stderr note at the bottom.
UNKNOWN = '? '  
COLLECTION = {'ElementCollection', 'OneToMany', 'ManyToMany'}
REFERENCE = {'ManyToOne', 'OneToOne'}
KT_PROP = re.compile(
    r'\b(?:lateinit\s+)?(?:var|val)\s+(\w+)\s*:\s*([\w<>?, .\[\]]+)')
JAVA_FIELD = re.compile(
    r'\b(?:private|protected|public)\s+(?:final\s+)?([\w<>\[\], ?.]+?)\s+(\w+)\s*[;=]')
STRINGS = re.compile(r'"(?:[^"\\]|\\.)*"')
# `val displayName: String get() = ...` and `val x: T by lazy { }` have no backing
# field, so they are not columns - they used to come out as a column named after the
# property with the Kotlin type as its type, which reads exactly like a real one
COMPUTED = re.compile(r'\bget\s*\(\s*\)|\bby\s+\w')
# @EntityScan sits on the bootstrap class, @EntityGraph and @EntityListeners on
# things that are not entities either - so the name has to end right there
ENTITY = re.compile(r'^[ \t]*@Entity(?![A-Za-z])', re.M)


def blanked(line):
    """Braces and slashes inside a string literal are text, not code - but the column
    names in there are the ones we are after, so the literals are blanked at the same
    length instead of being removed."""
    return STRINGS.sub(lambda m: '"' + ' ' * (len(m.group(0)) - 2) + '"', line)


def supertypes_of(header):
    """Everything after the top level colon of a Kotlin class header."""
    depth = 0
    for i, ch in enumerate(header):
        if ch in '([<':
            depth += 1
        elif ch in ')]>':
            depth -= 1
        elif ch == ':' and depth == 0:
            return [s.strip().split('(')[0].split('<')[0]
                    for s in top_level_parts(header[i + 1:]) if s.strip()]
    return []


def snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def column(chunk, prop_name, prop_type, java=False):
    """One property plus the annotations above it, turned into a column."""
    anns = set(re.findall(r'@(\w+)', chunk))
    bare = prop_type.replace('?', '').strip()
    if 'Transient' in anns:
        return None
    if COLLECTION & anns:
        return {'name': '-- ' + prop_name, 'type': 'collection (' + bare.replace('Mutable', '') + ')'}
    if 'Embedded' in anns or 'EmbeddedId' in anns:
        return {'name': '-- ' + prop_name, 'type': 'embedded ' + bare}
    join = re.search(r'@JoinColumn\s*\(\s*(?:name\s*=\s*)?"(\w+)"', chunk)
    if join or REFERENCE & anns:
        return {'name': join.group(1) if join else snake(prop_name) + '_id',
                'type': 'uuid', 'fk': True, 'ref': bare}
    named = re.search(r'@Column\s*\([^)]*name\s*=\s*"(\w+)"', chunk)
    # columnDefinition is the ddl itself, so it beats every guess made from the type
    ddl = re.search(r'columnDefinition\s*=\s*"([^"]+)"', chunk)
    col = {'name': named.group(1) if named else snake(prop_name),
           'type': ddl.group(1) if ddl else
                   'text (enum)' if 'Enumerated' in anns else
                   SQL.get(bare) or UNKNOWN + bare}
    if 'Id' in anns or 'EmbeddedId' in anns:
        col['pk'] = True
    return col


def top_level_parts(text):
    """Split a parameter list on the commas that are not inside brackets."""
    parts, depth, cur = [], 0, ''
    for ch in text:
        if ch in '([<{':
            depth += 1
        elif ch in ')]>}':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return parts


def primary_constructor(text, start):
    """The text between the parentheses of the primary constructor, or ''."""
    open_paren = text.find('(', start)
    brace = text.find('{', start)
    if open_paren < 0 or (0 <= brace < open_paren):
        return ''
    depth, i = 0, open_paren
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
        i += 1
    return ''


def body_columns(lines, header_index, java=False):
    """Properties declared in the class body - the ones a constructor regex misses."""
    cols, anns, depth, started = [], [], 0, False
    for line in lines[header_index:]:
        masked = blanked(line)
        comment = masked.find('//')
        code = line[:comment] if comment >= 0 else line
        clean = masked[:comment] if comment >= 0 else masked
        opened = depth
        depth += clean.count('{') - clean.count('}')
        if not started:
            started = depth >= 1
            continue
        if depth <= 0:
            break
        if opened != 1:                       # inside a function, a companion, an init block
            continue
        stripped = code.strip()
        masked_strip = clean.strip()
        if stripped.startswith('@'):
            anns.append(stripped)
            # `@Version var version: Long = 0` is one line, and reading it as an
            # annotation and nothing else loses the column without a word - which is
            # how @Version went missing while the @ManyToOne two lines below it, whose
            # annotation sat on its own line, came through fine
            if not (JAVA_FIELD if java else KT_PROP).search(masked_strip):
                continue
        if re.search(r'\bfun\s+\w+\s*\(', stripped):
            anns = []
            continue
        if not java and COMPUTED.search(masked_strip):
            anns = []
            continue
        m = JAVA_FIELD.search(masked_strip) if java else KT_PROP.search(masked_strip)
        if m:
            name, ptype = (m.group(2), m.group(1)) if java else (m.group(1), m.group(2))
            col = column(' '.join(anns) + ' ' + stripped, name, ptype, java)
            if col:
                cols.append(col)
            anns = []
        elif stripped and not stripped.startswith('@'):
            anns = []
    return cols


def entity(path):
    text = path.read_text(encoding='utf-8')
    found = ENTITY.search(text)
    if not found:
        return None
    java = path.suffix == '.java'
    at = found.start()
    decl = re.search(r'\b(?:class|record)\s+(\w+)', text[at:])
    if not decl:
        return None
    name = decl.group(1)
    header_at = at + decl.start()
    header_line = text[:header_at].count('\n')

    table = re.search(r'@Table\s*\(\s*(?:\n\s*)?name\s*=\s*"([^"]+)"', text[:header_at]) \
        or re.search(r'@Table\s*\(\s*"([^"]+)"', text[:header_at])
    if java:
        extends = re.search(r'\bextends\s+(\w+)', text[header_at:header_at + 400])
        supertypes = [extends.group(1)] if extends else []
    else:
        header = text[header_at:].split('{')[0]
        supertypes = supertypes_of(header)

    cols = []
    if not java:
        for part in top_level_parts(primary_constructor(text, header_at)):
            flat = re.sub(r'\s+', ' ', part).strip()
            m = KT_PROP.search(flat)
            if m:
                col = column(flat, m.group(1), m.group(2))
                if col:
                    cols.append(col)
    cols += body_columns(text.splitlines(), header_line, java)

    return name, {
        'file': str(path),
        'table': table.group(1) if table else None,
        'supertypes': [s for s in supertypes if s],
        'inheritance': bool(re.search(r'@Inheritance', text)),
        'columns': cols,
    }


def main(paths):
    out, empty, unmapped = {}, [], []
    for p in paths:
        found = entity(pathlib.Path(p))
        if not found:
            continue
        name, data = found
        out[name] = data
        if not data['columns']:
            empty.append(f'{name} ({p})')
        for col in data['columns']:
            if col['type'].startswith(UNKNOWN):
                unmapped.append(f'{name}.{col["name"]}: {col["type"][len(UNKNOWN):]}')
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if empty:
        print('\n!! zero columns - the extraction failed, open these files:', file=sys.stderr)
        for e in empty:
            print('   ' + e, file=sys.stderr)
    if unmapped:
        print(f'\n!! {len(unmapped)} column(s) carry a Kotlin/Java type, not a db type - '
              'marked with "? " and it has to be gone before the model is written:', file=sys.stderr)
        for u in unmapped:
            print('   ' + u, file=sys.stderr)
        print('   usually an @Converter (read the converter for the target type), an '
              '@Embeddable, or an enum with no @Enumerated - and that last one is a '
              'finding, not just a gap.', file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
