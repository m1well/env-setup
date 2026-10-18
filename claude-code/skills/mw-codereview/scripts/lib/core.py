"""Shared plumbing: file selection, comment and string masking, config parsing, the check registry."""
from __future__ import annotations

import bisect
import math
import os
import re
import subprocess
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

SEVERITIES = ('critical', 'high', 'medium', 'low')

SKIP_DIRS = {'node_modules', '.git', 'build', 'dist', 'target', 'out', '.gradle', '.angular', '.nx',
             '.idea', '.vscode', '.fleet', 'coverage', '.next', '.nuxt', 'tmp', '.cache', 'bin',
             '.mvn', '.yarn', '.pnpm-store', 'bower_components', '__pycache__', '.venv', 'venv',
             '.terraform', '.docusaurus', '.svelte-kit', 'storybook-static'}
OWN_OUTPUT = re.compile(r'(^|/)docs/mw-(codereview|topomap)-\d{8}/')
TEXT_EXT = {'.kt', '.kts', '.java', '.ts', '.tsx', '.js', '.mjs', '.cjs', '.jsx', '.html', '.htm',
            '.yml', '.yaml', '.properties', '.json', '.xml', '.gradle', '.toml', '.env', '.sh',
            '.bash', '.zsh', '.conf', '.tf', '.sql', '.ini', '.cfg', '.txt', '.groovy', '.py',
            '.dockerfile', '.scss', '.npmrc'}
TEXT_NAMES = re.compile(r'^(Dockerfile.*|Containerfile.*|Jenkinsfile|Makefile|\.env.*|\.npmrc|'
                        r'\.yarnrc.*|\.gitignore|\.dockerignore|\.gitlab-ci\.yml|id_rsa|id_ed25519|'
                        r'id_ecdsa|\.pypirc|\.netrc|kubeconfig)$')
SECRET_FILE_EXT = {'.pem', '.key', '.p12', '.pfx', '.jks', '.keystore', '.ppk', '.asc', '.gpg', '.kdbx'}
MAX_BYTES = 1_500_000
C_LIKE = {'.kt', '.kts', '.java', '.ts', '.tsx', '.js', '.mjs', '.cjs', '.jsx', '.gradle', '.groovy',
          '.scss'}

TEST_PATH = re.compile(
    r'(^|/)(src/(test|it|integrationTest|testFixtures|e2e|jmh)\w*/|__tests__/|__mocks__/|tests?/|'
    r'e2e/|cypress/|playwright/|testing/|fixtures?/|mocks?/|[\w-]+-e2e/|test-utils?/)'
    r'|\.(spec|test|e2e|cy|stories)\.[jt]sx?$|(Test|Tests|IT|Spec|Fixture|Fixtures)\.(kt|java)$')


def is_test_path(rel: str) -> bool:
    return bool(TEST_PATH.search(rel))


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    severity: str
    category: str
    verify: str
    security: bool
    rule: str
    owasp: str
    gdpr: str


CHECKS: dict[str, Check] = {}


def define(id, title, severity, category, verify, *, security=False, rule='', owasp='', gdpr=''):
    CHECKS[id] = Check(id, title, severity, category, verify, security, rule, owasp, gdpr)


def lower(severity: str, steps: int = 1) -> str:
    return SEVERITIES[min(SEVERITIES.index(severity) + steps, len(SEVERITIES) - 1)]


class Hits:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, check: str, file: str | None, line: int | None, evidence: str,
            severity: str | None = None, **extra):
        spec = CHECKS[check]
        sev = severity or spec.severity
        if file and is_test_path(file) and not extra.pop('keep_in_tests', False):
            sev, extra['test'] = lower(sev), True
        self.items.append({'check': check, 'severity': sev, 'file': file, 'line': line,
                           'evidence': clip(evidence), **extra})


def clip(text: str, limit: int = 180) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text if len(text) <= limit else text[:limit - 3] + '...'


def redact(value: str) -> str:
    value = value.strip()
    if len(value) <= 6:
        return '*' * len(value)
    return f'{value[:3]}***({len(value)} chars)'


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {c: value.count(c) for c in set(value)}
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def _blank(text: str) -> str:
    return re.sub(r'[^\n]', ' ', text)


_C_TOKENS = re.compile(r'//[^\n]*|/\*[\s\S]*?(?:\*/|$)|"""[\s\S]*?(?:"""|$)|"(?:\\.|[^"\\\n])*"?'
                       r"|'(?:\\.|[^'\\\n])*'?|`(?:\\.|[^`\\])*`?")
_HTML_COMMENT = re.compile(r'<!--[\s\S]*?(?:-->|$)')
_HASH_COMMENT = re.compile(r'(?m)^[ \t]*#.*$')


def mask(text: str, suffix: str) -> tuple[str, str]:
    """(code, bare): comments blanked in both, string contents in bare - offsets stay valid in all three."""
    if suffix in ('.html', '.htm', '.xml'):
        code = _HTML_COMMENT.sub(lambda m: _blank(m.group()), text)
        return code, code
    if suffix in ('.yml', '.yaml', '.properties', '.sh', '.toml', '.conf'):
        code = _HASH_COMMENT.sub(lambda m: _blank(m.group()), text)
        return code, code
    if suffix not in C_LIKE:
        return text, text
    code, bare, pos = [], [], 0
    for m in _C_TOKENS.finditer(text):
        start, end = m.span()
        tok = m.group()
        code.append(text[pos:start])
        bare.append(text[pos:start])
        if tok.startswith(('//', '/*')):
            code.append(_blank(tok))
            bare.append(_blank(tok))
        else:
            q = 3 if tok.startswith('"""') else 1
            closed = len(tok) >= 2 * q and tok.endswith(tok[:q])
            inner = tok[q:-q] if closed else tok[q:]
            code.append(tok)
            bare.append(tok[:q] + _blank(inner) + (tok[-q:] if closed else ''))
        pos = end
    code.append(text[pos:])
    bare.append(text[pos:])
    return ''.join(code), ''.join(bare)


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_BYTES:
            return ''
        return path.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n')
    except OSError:
        return ''


class Source:
    def __init__(self, root: Path, rel: str):
        self.rel = rel
        self.path = root / rel
        self.text = read_text(self.path)

    @cached_property
    def views(self) -> tuple[str, str]:
        return mask(self.text, self.path.suffix.lower())

    @property
    def code(self) -> str:
        return self.views[0]

    @property
    def bare(self) -> str:
        return self.views[1]

    @cached_property
    def lines(self) -> list[str]:
        return self.text.split('\n')

    @cached_property
    def code_lines(self) -> list[str]:
        return self.code.split('\n')

    @cached_property
    def bare_lines(self) -> list[str]:
        return self.bare.split('\n')

    @cached_property
    def _breaks(self) -> list[int]:
        return [i for i, ch in enumerate(self.text) if ch == '\n']

    def line_at(self, offset: int) -> int:
        return bisect.bisect_left(self._breaks, offset) + 1

    def line(self, number: int) -> str:
        return self.lines[number - 1] if 0 < number <= len(self.lines) else ''


class Repo:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.git = self._git('rev-parse', '--is-inside-work-tree').strip() == 'true'
        self.nested: list[str] = []
        if self.git:
            candidates, self.tracked = self._listed(self.root, '')
        else:
            # a folder holding several repositories: each one decides via its own .gitignore
            self.nested = self._nested_repos()
            candidates, self.tracked = list(self._walk(skip=set(self.nested))), set()
            for sub in self.nested:
                files, tracked = self._listed(self.root / sub, sub + '/')
                candidates += files
                self.tracked |= tracked
            if not self.nested:
                self.tracked = None
        self.files = sorted(f for f in candidates if self._keep(f))
        self._cache: dict[str, Source] = {}

    def _git(self, *args, cwd: Path | None = None) -> str:
        try:
            return subprocess.run(['git', *args], cwd=cwd or self.root, capture_output=True, text=True,
                                  timeout=60).stdout
        except (OSError, subprocess.SubprocessError):
            return ''

    def _listed(self, where: Path, prefix: str) -> tuple[list[str], set[str]]:
        listed = self._git('ls-files', '-co', '--exclude-standard', '-z', cwd=where).split('\0')
        tracked = {prefix + f for f in self._git('ls-files', '-z', cwd=where).split('\0') if f}
        return [prefix + f for f in listed if f and (where / f).is_file()], tracked

    def _nested_repos(self, depth: int = 4) -> list[str]:
        found = []
        for dirpath, dirnames, _ in os.walk(self.root):
            rel = os.path.relpath(dirpath, self.root)
            level = 0 if rel == '.' else rel.count(os.sep) + 1
            if '.git' in dirnames and rel != '.':
                found.append(rel)
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS] if level < depth else []
        return sorted(found)

    def _walk(self, skip: set[str] = frozenset()):
        for dirpath, dirnames, filenames in os.walk(self.root):
            rel_dir = os.path.relpath(dirpath, self.root)
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and
                           os.path.normpath(os.path.join(rel_dir, d)) not in skip]
            for name in filenames:
                yield os.path.relpath(os.path.join(dirpath, name), self.root)

    @staticmethod
    def _keep(rel: str) -> bool:
        parts = rel.split('/')
        # a package called `build` or `out` inside a source tree is code, not output
        inside_src = 'src' in parts and parts.index('src') < len(parts) - 1
        if not inside_src and any(p in SKIP_DIRS for p in parts[:-1]):
            return False
        if 'node_modules' in parts or OWN_OUTPUT.search(rel):
            return False
        name = parts[-1]
        if name.endswith(('.min.js', '.min.css', '.map', '-lock.json', '.lock', '.lockb', 'lock.yaml')):
            return False
        suffix = os.path.splitext(name)[1].lower()
        return suffix in TEXT_EXT or suffix in SECRET_FILE_EXT or bool(TEXT_NAMES.match(name))

    def source(self, rel: str) -> Source:
        if rel not in self._cache:
            self._cache[rel] = Source(self.root, rel)
        return self._cache[rel]

    def by_ext(self, *exts: str) -> list[str]:
        return [f for f in self.files if f.lower().endswith(exts)]

    def is_tracked(self, rel: str) -> bool | None:
        return None if self.tracked is None else rel in self.tracked


def balanced(text: str, start: int, opening: str = '(', closing: str = ')') -> int:
    """Index of the bracket closing the one at `start`, or -1. Run it on a `bare` view."""
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == opening:
            depth += 1
        elif ch == closing:
            depth -= 1
            if depth == 0:
                return i
    return -1


def split_top(text: str, sep: str = ',') -> list[tuple[int, str]]:
    """Parts of `text` split on `sep` outside of brackets, each with its start offset."""
    parts, depth, start = [], 0, 0
    clean = text.replace('->', '  ').replace('=>', '  ').replace('>=', '  ').replace('<=', '  ')
    for i, ch in enumerate(clean):
        if ch in '([{<':
            depth += 1
        elif ch in ')]}>':
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append((start, text[start:i]))
            start = i + 1
    parts.append((start, text[start:]))
    return [(s, p) for s, p in parts if p.strip()]


STRING_LIT = re.compile(r'"((?:\\.|[^"\\\n])*)"|\'((?:\\.|[^\'\\\n])*)\'')


def strings_in(code: str) -> list[str]:
    return [a if a is not None else b for a, b in STRING_LIT.findall(code)]


@dataclass
class Entry:
    key: str
    value: str
    line: int
    profile: str | None
    norm: str = field(init=False)

    def __post_init__(self):
        self.norm = re.sub(r'[-_]', '', self.key.lower())


_PROFILE_FILE = re.compile(r'(?:application|bootstrap)-([\w.-]+)\.(?:ya?ml|properties)$')
_YAML_KEY = re.compile(r'^(\s*)(-\s+)?("[^"]+"|\'[^\']+\'|[^\s#:][^:#]*?)\s*:(?:\s+(.*)|\s*)$')


def _strip_yaml_comment(value: str) -> str:
    if value and value[0] in '"\'':
        end = value.find(value[0], 1)
        return value[:end + 1] if end > 0 else value
    return re.split(r'\s+#', value, maxsplit=1)[0].strip()


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        return value[1:-1]
    return value


def config_entries(src: Source) -> list[Entry]:
    name = src.path.name
    file_profile = (_PROFILE_FILE.search(name) or [None, None])[1]
    if name.endswith('.properties'):
        out = []
        for i, raw in enumerate(src.lines, 1):
            line = raw.strip()
            if not line or line[0] in '#!':
                continue
            m = re.match(r'^([^=:\s]+)\s*[=:]\s*(.*)$', line)
            if m:
                out.append(Entry(m.group(1), m.group(2).strip(), i, file_profile))
        doc_profile = next((e.value for e in out if e.key in (
            'spring.config.activate.on-profile', 'spring.profiles')), None)
        for e in out:
            e.profile = e.profile or doc_profile
        return out

    docs: list[list[Entry]] = [[]]
    stack: list[tuple[int, str]] = []
    block_indent = None
    for i, raw in enumerate(src.lines, 1):
        if raw.startswith('---'):
            docs.append([])
            stack, block_indent = [], None
            continue
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        indent = len(raw) - len(raw.lstrip())
        if block_indent is not None:
            if indent > block_indent:
                continue
            block_indent = None
        m = _YAML_KEY.match(raw)
        if not m:
            continue
        indent = len(m.group(1)) + (len(m.group(2)) if m.group(2) else 0)
        key = _unquote(m.group(3))
        value = _strip_yaml_comment(m.group(4) or '')
        while stack and stack[-1][0] >= indent:
            stack.pop()
        full = '.'.join([k for _, k in stack] + [key])
        if value in ('|', '>', '|-', '>-', '|+', '>+'):
            block_indent = indent
            docs[-1].append(Entry(full, value, i, file_profile))
        elif value:
            docs[-1].append(Entry(full, _unquote(value), i, file_profile))
        else:
            stack.append((indent, key))
    out = []
    for doc in docs:
        doc_profile = next((e.value for e in doc if e.key in (
            'spring.config.activate.on-profile', 'spring.profiles')), None)
        for e in doc:
            e.profile = e.profile or doc_profile
        out += doc
    return out


DEV_PROFILE = re.compile(r'^(local|dev|develop|development|test|testing|it|e2e|h2|demo|mock|ci|'
                         r'docker-local|localhost|sandbox)([-_.]\w+)?$', re.I)


def profile_kind(profile: str | None) -> str:
    """'default', 'dev' or 'prod-like' - dev settings only count where they can reach production."""
    if not profile:
        return 'default'
    return 'dev' if all(DEV_PROFILE.match(p.strip()) for p in re.split(r'[,|&!]', profile)
                        if p.strip()) else 'prod-like'


def version_tuple(version: str) -> tuple[int, ...]:
    nums = re.findall(r'\d+', re.split(r'[-+]', version.strip().lstrip('^~>=v '), maxsplit=1)[0])
    return tuple(int(n) for n in nums[:4]) or (0,)
