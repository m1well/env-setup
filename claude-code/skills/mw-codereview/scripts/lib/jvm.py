"""Declarations of a Kotlin or Java file with their annotations - a bracket scan of the masked text, no parser."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .core import Source, balanced, split_top

ANNO = re.compile(r'@(?:(?:field|get|set|param|property|receiver|setparam|delegate|file):)?([\w.]+)')
CLASS_DECL = re.compile(
    r'(?:(?:public|private|protected|internal|open|abstract|sealed|data|value|enum|annotation|final|'
    r'static|inner|companion|non-sealed|strictfp)\s+)*(class|interface|object|record|enum)\s+(\w+)')
KT_FUN = re.compile(
    r'(?:(?:public|private|protected|internal|open|override|suspend|inline|operator|abstract|final|'
    r'tailrec|infix|external)\s+)*fun\s+(?:<[^>]*>\s*)?(?:[\w.<>?]+\.)?(`?\w+`?)\s*\(')
KT_PROP = re.compile(
    r'(?:(?:public|private|protected|internal|open|override|lateinit|const|final)\s+)*(?:val|var)\s+(\w+)')
JAVA_METHOD = re.compile(
    r'(?:(?:public|private|protected|static|final|abstract|synchronized|default|native)\s+)*'
    r'(?:<[^>]+>\s*)?([\w<>\[\],.? ]+?)\s+(\w+)\s*\(')
JAVA_CTOR = re.compile(r'(?:public|protected|private)\s+(\w+)\s*\(')
JAVA_FIELD = re.compile(
    r'(?:(?:public|private|protected|static|final|transient|volatile)\s+)+([\w<>\[\],.? ]+?)\s+(\w+)\s*(?:=|;)')
NOT_DECL = re.compile(r'(return|new|if|for|while|switch|catch|throw|else|try|do|case|yield|assert|'
                      r'super|this|import|package|val|var)\b')
KT_CTOR = re.compile(r'\s*(?:<[^>{]*>)?\s*(?:(?:@[\w.]+(?:\([^)]*\))?\s*)*'
                     r'(?:private|internal|public|protected)?\s*constructor\s*)?\(')
CHAIN = re.compile(r'\s*(\?\.|\.|\?:|&&|\|\||\+|-|\*)')


@dataclass
class Param:
    name: str
    type: str
    annos: list[str]
    text: str
    code: str


@dataclass
class Member:
    kind: str
    name: str
    line: int
    offset: int
    annos: list[str]
    anno_text: str
    anno_code: str
    anno_offset: int
    sig: str
    sig_code: str
    private: bool
    returns: str = ''
    params: list[Param] = field(default_factory=list)
    body: tuple[int, int] | None = None
    owner: 'Member | None' = None
    header: str = ''

    def has(self, *names: str) -> bool:
        return any(n in self.annos for n in names)


def _skip_ws(text: str, i: int, newlines: bool = False) -> int:
    chars = ' \t\n' if newlines else ' \t'
    while i < len(text) and text[i] in chars:
        i += 1
    return i


def _params(src: Source, open_at: int, close_at: int, kotlin: bool) -> list[Param]:
    inner = src.bare[open_at + 1:close_at]
    out = []
    for start, part in split_top(inner):
        code = src.code[open_at + 1 + start:open_at + 1 + start + len(part)]
        annos = [a.split('.')[-1] for a in ANNO.findall(part)]
        plain = re.sub(r'@(?:\w+:)?[\w.]+(?:\s*\([^)]*\))?', ' ', part).strip()
        if kotlin:
            m = re.match(r'(?:vararg\s+)?(?:(?:private|protected|internal|public|override|open|final)\s+)*'
                         r'(?:val\s+|var\s+)?(`?\w+`?)\s*:\s*(.+?)\s*(?:=.*)?$', plain, re.S)
            if m:
                out.append(Param(m.group(1), re.sub(r'\s+', ' ', m.group(2)), annos, part, code))
        else:
            tokens = [t for t in plain.replace('...', '[] ').split() if t != 'final']
            if len(tokens) >= 2:
                out.append(Param(tokens[-1], ' '.join(tokens[:-1]), annos, part, code))
    return out


def _body(bare: str, start: int, expression_ok: bool) -> tuple[int, int] | None:
    """The `{...}` body following `start`, or a Kotlin expression body, or None."""
    i = _skip_ws(bare, start, newlines=True)
    limit = min(len(bare), i + 600)
    j = i
    depth = 0
    while j < limit:
        ch = bare[j]
        if ch in '(<[':
            depth += 1
        elif ch in ')>]':
            depth -= 1
        elif depth <= 0 and ch == '{':
            end = balanced(bare, j, '{', '}')
            return (j, end if end > 0 else len(bare))
        elif depth <= 0 and ch == '=' and bare[j + 1:j + 2] != '=' and bare[j - 1:j] not in '!<>=' \
                and expression_ok:
            k, depth2 = _skip_ws(bare, j + 1, newlines=True), 0
            while k < len(bare):
                c = bare[k]
                if c in '([{':
                    depth2 += 1
                elif c in ')]}':
                    depth2 -= 1
                    if depth2 < 0:
                        break
                elif c == '\n' and depth2 == 0 and not CHAIN.match(bare, k + 1):
                    break
                k += 1
            return (j, k)
        elif depth <= 0 and (ch == ';' or (ch == '\n' and bare[i:j].strip() and
                                           not bare[i:j].rstrip().endswith((':', ',')) and
                                           not CHAIN.match(bare, j + 1) and
                                           re.match(r'\s*[\w@}]', bare[j + 1:j + 40]) and
                                           not re.match(r'\s*(where|throws)\b', bare[j + 1:j + 40]))):
            return None
        j += 1
    return None


def parse(src: Source) -> list[Member]:
    bare = src.bare
    kotlin = src.rel.endswith(('.kt', '.kts'))
    out: list[Member] = []
    pos, block_start = 0, None
    n = len(bare)
    while pos < n:
        line_end = bare.find('\n', pos)
        line_end = n if line_end < 0 else line_end
        seg = bare[pos:line_end]
        stripped = seg.lstrip()
        if not stripped.strip():
            pos = line_end + 1
            continue
        decl_at = pos + len(seg) - len(stripped)
        if stripped.startswith('@') and not stripped.startswith('@interface'):
            if block_start is None:
                block_start = decl_at
            k = decl_at
            while True:
                m = ANNO.match(bare, k)
                if not m:
                    break
                k = _skip_ws(bare, m.end())
                if bare[k:k + 1] == '(':
                    close = balanced(bare, k)
                    k = n if close < 0 else close + 1
                nxt = _skip_ws(bare, k, newlines=True)
                if bare[nxt:nxt + 1] == '@' and not bare.startswith('@interface', nxt):
                    k = nxt
                    continue
                break
            k = _skip_ws(bare, k)
            rest_end = bare.find('\n', k)
            rest_end = n if rest_end < 0 else rest_end
            if not bare[k:rest_end].strip():
                pos = rest_end + 1
                continue
            decl_at = k
            line_end = rest_end
        member = _declaration(src, decl_at, block_start, kotlin)
        block_start = None
        if member:
            out.append(member)
            if member.kind == 'class' or not member.body:
                pos = max(line_end, member.sig_end) + 1
            else:
                pos = member.body[1] + 1
                continue
        else:
            pos = line_end + 1
    for m in out:
        owners = [c for c in out if c.kind == 'class' and c.body and c.body[0] < m.offset < c.body[1]]
        m.owner = max(owners, key=lambda c: c.body[0]) if owners else None
    return out


def _declaration(src: Source, at: int, block_start: int | None, kotlin: bool) -> Member | None:
    bare, code = src.bare, src.code
    line_end = bare.find('\n', at)
    line = bare[at:line_end if line_end > 0 else len(bare)]
    if NOT_DECL.match(line) and not (kotlin and re.match(r'(val|var)\b', line)):
        return None
    anno_from = block_start if block_start is not None else at
    anno_text = bare[anno_from:at]
    common = dict(line=src.line_at(at), offset=at, anno_offset=anno_from,
                  annos=[a.split('.')[-1] for a in ANNO.findall(anno_text)],
                  anno_text=anno_text, anno_code=code[anno_from:at])

    m = CLASS_DECL.match(line)
    if m:
        name_end = at + m.end()
        sig_end = name_end
        params = []
        ctor = KT_CTOR.match(bare, name_end) if kotlin or m.group(1) == 'record' else None
        if ctor:
            open_at = ctor.end() - 1
            close = balanced(bare, open_at)
            if close > 0:
                params = _params(src, open_at, close, kotlin)
                sig_end = close + 1
        brace = bare.find('{', sig_end)
        next_decl = re.search(r'\n\s*(?:@|(?:\w+\s+)*(?:class|fun|interface|object)\b)', bare[sig_end:brace]) \
            if brace > 0 else None
        body = None
        if brace > 0 and not next_decl:
            end = balanced(bare, brace, '{', '}')
            body = (brace, end if end > 0 else len(bare))
        header_end = bare.find('\n', sig_end)
        header = bare[at:body[0] if body else (header_end if header_end > 0 else len(bare))]
        member = Member('class', m.group(2), sig=bare[at:sig_end], sig_code=code[at:sig_end],
                        private=bool(re.match(r'(?:\w+\s+)*private\b', line)), params=params,
                        body=body, header=header, **common)
        member.sig_end = sig_end
        member.kind_detail = m.group(1)
        return member

    if kotlin:
        m = KT_FUN.match(line)
        kind = 'method' if m else None
        if not m:
            m = KT_PROP.match(line)
            kind = 'field' if m else None
    else:
        m = JAVA_CTOR.match(line) or JAVA_METHOD.match(line)
        kind = 'method' if m else None
        if not m or ('=' in line[:m.end()] and kind == 'method'):
            m = JAVA_FIELD.match(line)
            kind = 'field' if m else None
    if not m:
        return None
    name = m.group(m.lastindex)
    open_at = at + m.end() - 1 if kind == 'method' else -1
    params, returns, sig_end, body = [], '', line_end if line_end > 0 else len(bare), None
    if kind == 'method':
        close = balanced(bare, open_at)
        if close < 0:
            return None
        params = _params(src, open_at, close, kotlin)
        sig_end = close + 1
        if kotlin:
            ret = re.match(r'\s*:\s*([^={\n]+)', bare[sig_end:sig_end + 200])
            returns = ret.group(1).strip() if ret else 'Unit'
        else:
            returns = '' if JAVA_CTOR.match(line) else m.group(1).strip()
        body = _body(bare, sig_end, kotlin)
    elif kind == 'field':
        ret = re.match(r'\s*:\s*([\w.<>?, ]+)', bare[at + m.end():at + m.end() + 200]) if kotlin else None
        returns = ret.group(1).strip() if ret else (m.group(1).strip() if not kotlin else '')
    member = Member(kind, name.strip('`'), sig=bare[at:sig_end], sig_code=code[at:sig_end],
                    private=bool(re.match(r'(?:\w+\s+)*private\b', line)), returns=returns,
                    params=params, body=body, **common)
    member.sig_end = sig_end
    member.kind_detail = kind
    return member


STEREOTYPES = [
    ('advice', {'RestControllerAdvice', 'ControllerAdvice'}),
    ('controller', {'RestController', 'Controller'}),
    ('client', {'FeignClient', 'HttpExchange'}),
    ('service', {'Service'}),
    ('repository', {'Repository'}),
    ('entity', {'Entity'}),
    ('superclass', {'MappedSuperclass'}),
    ('embeddable', {'Embeddable'}),
    ('app', {'SpringBootApplication'}),
    ('config', {'Configuration', 'AutoConfiguration'}),
    ('component', {'Component'}),
]
REPO_SUPER = re.compile(r'\b(Jpa|Crud|PagingAndSorting|ListCrud|ListPagingAndSorting|Reactive\w*|'
                        r'Mongo|R2dbc|Coroutine\w*|Kotlin\w*)Repository\s*<')


class JFile:
    def __init__(self, src: Source):
        self.src = src
        self.rel = src.rel
        self.kotlin = src.rel.endswith(('.kt', '.kts'))
        pkg = re.search(r'(?m)^\s*package\s+([\w.]+)', src.bare)
        self.package = pkg.group(1) if pkg else ''
        self.imports = re.findall(r'(?m)^\s*import\s+(?:static\s+)?([\w.]+)', src.bare)
        self.members = parse(src)
        self.classes = [m for m in self.members if m.kind == 'class']
        self.stereotype, self.cls = None, None
        for c in self.classes:
            kind = next((s for s, names in STEREOTYPES if c.has(*names)), None)
            if not kind and getattr(c, 'kind_detail', '') == 'interface' and REPO_SUPER.search(c.header):
                kind = 'repository'
            if kind:
                self.stereotype, self.cls = kind, c
                break
        if not self.cls and self.classes:
            self.cls = self.classes[0]
        self.name = self.cls.name if self.cls else src.path.stem

    def methods(self, owner: Member | None = None) -> list[Member]:
        return [m for m in self.members if m.kind == 'method' and (owner is None or m.owner is owner)]

    def body_text(self, m: Member, view: str = 'bare') -> str:
        if not m.body:
            return ''
        text = self.src.bare if view == 'bare' else self.src.code
        return text[m.body[0]:m.body[1] + 1]
