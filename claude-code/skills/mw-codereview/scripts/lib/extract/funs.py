#!/usr/bin/env python3
"""Public methods with their full signature, for a whole directory of files at once.

    python3 funs.py $(rg -l '@Service' --glob '**/*.kt')

A signature runs over several lines as readily as a constructor does, and a Kotlin
expression body (`fun x() = repo.findAll()`) would drag half the method into the
signature, so both are cut. Indentation is not assumed to be two spaces - ktfmt and
ktlint disagree about that, and a wrong guess silently finds nothing.

What is left out: everything private, protected or internal, `equals` / `hashCode` /
`toString`, Java's generated accessors, and anything nested deeper than a direct
member. What is kept: every method of an interface, whether or not it says public -
on a Spring Data repository the derived query name *is* the documentation.

**Kotlin `getX()` / `isX()` methods are kept.** They are ordinary method names on a
service, not accessors - a real Kotlin accessor is `val x get() = ...` and carries no
`fun` at all. Dropping them cost `AdminRaceService` four of its six methods once, and
nothing said so.

Every file is measured twice, and the second measurement does not share a line of
logic with the first: the parser works off indentation, the check works off brace
depth and counts the `fun` that sit directly in a class body. A mismatch goes to
stderr - **fewer signatures than declarations means the extraction failed**, not that
the class has few methods. Nothing else in the toolchain can notice that: the model
has no idea how many methods the file had.

The `doc` line in the model is yours to write. This only saves you the typing of the
signature.
"""
import re
import sys
import pathlib

KT_FUN = re.compile(
    r'^(\s+)(?:(?:override|open|suspend|inline|operator|abstract|final|external|tailrec|infix)\s+)*'
    # an extension function declared as a member carries a receiver before the name
    r'fun\s+(?:<[^>]+>\s*)?(?:\w+(?:<[^>]+>)?\.)?(\w+)\s*\(')
KT_HIDDEN = re.compile(r'^\s*(?:private|protected|internal)\b')
KT_ANY_FUN = re.compile(r'(?:^|[^\w.])fun\s+(?:<[^>]+>\s*)?[\w.<>]*\w\s*\(')
PARAMS_END = re.compile(r'\)')

JAVA_METHOD = re.compile(
    r'^(\s+)(?:@\w+(?:\([^)]*\))?\s+)*'
    r'(?:public\s+|default\s+)?(?:static\s+|final\s+|abstract\s+|synchronized\s+)*'
    r'(?:<[^>]+>\s*)?[\w<>\[\], ?.]+\s+(\w+)\s*\(')
JAVA_HIDDEN = re.compile(r'^\s*(?:private|protected)\b')

NOISE = {'equals', 'hashCode', 'toString', 'copy', 'component1', 'main'}
NOISE_LINE = re.compile(r'\b(?:' + '|'.join(NOISE) + r')\s*\(')
# a Java bean accessor is generated boilerplate; in Kotlin the same name is a
# hand-written service method, so this only ever applies to .java files
JAVA_ACCESSOR = re.compile(r'^(get|set|is)[A-Z]')
JAVA_ACCESSOR_LINE = re.compile(r'\b(?:get|set|is)[A-Z]\w*\s*\(')
LINE_COMMENT = re.compile(r'//.*$')
STRINGS = re.compile(r'"(?:[^"\\]|\\.)*"')
RAW_STRING = '"""' 


def decommented(lines):
    """The same lines with comments and string literals blanked out at equal length.

    A `fun` inside a `/* ... */` block is not a method, but it matches like one - and
    because the shallowest indent decides where the class body sits, a single
    commented-out method one space to the left throws every real member away. The
    braces inside a raw-string `@Query` count just as wrongly. Blanking keeps the line
    numbers and the indentation intact."""
    out, in_block, in_raw = [], False, False
    for line in lines:
        if in_raw:
            end = line.find(RAW_STRING)
            if end < 0:
                out.append(' ' * len(line))
                continue
            line, in_raw = ' ' * (end + 3) + line[end + 3:], False
        pos = 0
        while not in_raw:
            start = line.find(RAW_STRING, pos)
            if start < 0:
                break
            end = line.find(RAW_STRING, start + 3)
            if end < 0:
                line, in_raw = line[:start + 3] + ' ' * (len(line) - start - 3), True
            else:
                line = line[:start + 3] + ' ' * (end - start - 3) + line[end:]
                pos = end + 3
        buf, i = [], 0
        while i < len(line):
            if in_block:
                end = line.find('*/', i)
                if end < 0:
                    buf.append(' ' * (len(line) - i))
                    i = len(line)
                else:
                    buf.append(' ' * (end + 2 - i))
                    i, in_block = end + 2, False
            else:
                start = line.find('/*', i)
                if start < 0:
                    buf.append(line[i:])
                    i = len(line)
                else:
                    buf.append(line[i:start])
                    i, in_block = start, True
        clean = ''.join(buf)
        out.append(LINE_COMMENT.sub(lambda m: ' ' * len(m.group(0)),
                                    STRINGS.sub(lambda m: '"' + ' ' * (len(m.group(0)) - 2) + '"', clean)))
    return out


def declarations(lines, java):
    """The methods that sit directly in a class body, found by brace depth alone.

    This is the count check, and it shares nothing with the indentation logic above on
    purpose - two measurements that fail the same way are one measurement. A `fun` in a
    companion object, a nested class or a lambda sits deeper than the class body and is
    not counted, which is exactly what the parser skips too."""
    depth, out = 0, []
    for i, line in enumerate(lines):
        if depth == 1 and (JAVA_METHOD.match(line) if java else KT_ANY_FUN.search(line)):
            out.append(i)
        depth += line.count('{') - line.count('}')
    return out


def signature(lines, i):
    buf, depth, j = lines[i].strip(), lines[i].count('(') - lines[i].count(')'), i
    while depth > 0 and j + 1 < len(lines):
        j += 1
        buf += ' ' + lines[j].strip()
        depth += lines[j].count('(') - lines[j].count(')')
    buf = re.sub(r'\s+', ' ', buf)
    # An expression body or a block body is not part of the signature - but a default
    # value is, and `filter: RaceFilter = RaceFilter.EMPTY` carries both a `=` and no
    # end of signature. So only what follows the closing parenthesis may be cut, which
    # is where the return type lives and where a body can start.
    depth, close = 0, len(buf)
    for pos, ch in enumerate(buf):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                close = pos + 1
                break
    head, tail = buf[:close], buf[close:]
    for cut in ('{', ' ='):
        part, _, _ = tail.partition(cut)
        tail = part
    # the signature goes into the model as it is, so a trailing comma and the spaces
    # a line break left behind are cleaned up here rather than by hand later
    out = re.sub(r'\(\s+', '(', head + tail)
    return re.sub(r',?\s+\)', ')', out).strip()


def members(path):
    """(signatures, lines they came from, declarations, the ones dropped on purpose)."""
    raw = path.read_text(encoding='utf-8').splitlines()
    lines = decommented(raw)
    java = path.suffix == '.java'
    pattern, hidden = (JAVA_METHOD, JAVA_HIDDEN) if java else (KT_FUN, KT_HIDDEN)
    hits = [(i, pattern.match(line)) for i, line in enumerate(lines) if pattern.match(line)]

    declared = declarations(lines, java)
    not_public = [i for i in declared
                  if hidden.match(lines[i]) or NOISE_LINE.search(lines[i])
                  or (java and JAVA_ACCESSOR_LINE.search(lines[i]))]

    if not hits:
        return [], [], declared, not_public
    # the shallowest indent is the one the top level class declares its members at,
    # whatever the formatter chose - anything deeper sits in a companion, a nested
    # class or a lambda and is not part of the public surface
    member_indent = min(len(m.group(1)) for _, m in hits)
    out, at = [], []
    for i, m in hits:
        line = lines[i]
        if hidden.match(line) or len(m.group(1)) != member_indent:
            continue
        name = m.group(2)
        if name in NOISE or (java and JAVA_ACCESSOR.match(name)):
            continue
        if java and re.match(r'^\s*(?:public\s+)?(?:record\s+|class\s+|new\s+|return\s+|if\s*\(|for\s*\(|while\s*\()', line):
            continue
        out.append(signature(raw, i))
        at.append(i)
    return out, at, declared, not_public


def main(paths):
    short = []
    for p in paths:
        path = pathlib.Path(p)
        print(f'##### {path.stem}   ({p})')
        found, at, declared, not_public = members(path)
        print('\n'.join('   ' + f for f in found) if found else '   (none)')
        # every declaration in the class body that neither made it into the output nor
        # was dropped on purpose was lost silently - that is the failure worth catching
        missing = [i for i in declared if i not in set(at) | set(not_public)]
        if missing:
            short.append(f'{path.name}: {len(found)} printed, {len(missing)} lost '
                         f'- line(s) {", ".join(str(i + 1) for i in missing[:12])}'
                         + (' ...' if len(missing) > 12 else ''))
    if short:
        print('\n!! fewer signatures than declarations - the extraction lost methods here, '
              'read these files by hand before writing their members:', file=sys.stderr)
        for s in short:
            print('   ' + s, file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
