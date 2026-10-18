"""Duplication and reuse: copied blocks, near-identical components and classes, helpers written twice."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from .core import Hits, Repo, define, is_test_path

define('DUP-BLOCK', 'Copied block of code', 'low', 'duplication',
       'Same lines in several places: a fix lands in one copy. Within one build it belongs in a shared function '
       'or component; across separately deployed services a copy can be the cheaper choice - say which.')
define('REUSE-SIMILAR', 'Near-identical components or classes', 'low', 'reuse',
       'Most lines agree. One shared version with an input or a flag for the difference - unless the two are '
       'expected to drift apart.')
define('REUSE-HELPER', 'Helper function written twice', 'low', 'reuse',
       'Same name, mostly the same body, several files: keep one in the shared lib or module.')

WINDOW = 8
CODE = ('.kt', '.java', '.ts', '.html')
SKIP_PATH = re.compile(r'(^|/)(generated|gen|openapi|api-client|i18n|migrations?|db/migration)/|\.d\.ts$|'
                       r'(^|/)environment[\w.-]*\.ts$|\.(routes|config)\.ts$')
TRIVIAL = re.compile(r'^[\s{}()\[\];,.<>/*+\-=:|&!?"\'`]*$|^(import|package|export \* from|\} from|@if|@else|@for|'
                     r'@case|@default|@switch|return;?$|break;?$|else\b)')
COMMON_NAMES = {'main', 'init', 'setup', 'config', 'create', 'build', 'get', 'set', 'handler', 'default', 'run',
                'toString', 'equals', 'hashCode', 'apply', 'invoke', 'of', 'from', 'parse', 'format', 'map', 'test'}


def _signature_lines(repo: Repo, rel: str) -> list[tuple[int, str]]:
    src = repo.source(rel)
    out = []
    for i, line in enumerate(src.code_lines, 1):
        s = re.sub(r'\s+', ' ', line).strip()
        if len(s) >= 6 and not TRIVIAL.match(s):
            out.append((i, s))
    return out


def _unit(repo: Repo, rel: str) -> str:
    return next((n for n in repo.nested if rel.startswith(n + '/')), '')


def blocks(repo: Repo, hits: Hits) -> list[dict]:
    files = [f for f in repo.files if f.endswith(CODE) and not is_test_path(f) and not SKIP_PATH.search(f)]
    sigs = [_signature_lines(repo, f) for f in files]
    occ = defaultdict(list)
    for fi, sig in enumerate(sigs):
        if len(sig) > 4000:
            continue
        for k in range(len(sig) - WINDOW + 1):
            occ[hash(tuple(s for _, s in sig[k:k + WINDOW]))].append((fi, k))
    runs = defaultdict(list)
    for locs in occ.values():
        if len(locs) < 2 or len(locs) > 12:
            continue
        for a in range(len(locs)):
            for b in range(a + 1, len(locs)):
                (fa, ka), (fb, kb) = sorted((locs[a], locs[b]))
                if fa == fb and kb - ka < WINDOW:
                    continue
                runs[(fa, fb, ka - kb)].append(ka)
    found = []
    for (fa, fb, delta), ks in runs.items():
        ks.sort()
        start = prev = ks[0]
        for k in ks[1:] + [None]:
            if k is not None and k == prev + 1:
                prev = k
                continue
            length = prev - start + WINDOW
            sa, sb = sigs[fa], sigs[fb]
            ra = (files[fa], sa[start][0], sa[start + length - 1][0])
            rb = (files[fb], sb[start - delta][0], sb[start - delta + length - 1][0])
            found.append((length, ra, rb))
            if k is not None:
                start = prev = k
    found.sort(key=lambda x: -x[0])
    clusters: list[dict] = []

    def overlaps(r, s):
        return r[0] == s[0] and min(r[2], s[2]) - max(r[1], s[1]) >= 0.5 * (r[2] - r[1])

    for length, ra, rb in found:
        home = next((c for c in clusters if any(overlaps(ra, m) or overlaps(rb, m) for m in c['members'])), None)
        if home is None:
            clusters.append({'length': length, 'members': [ra, rb]})
            continue
        for r in (ra, rb):
            if not any(overlaps(r, m) for m in home['members']):
                home['members'].append(r)
    out = []
    for c in clusters:
        members = c['members']
        span = max(m[2] - m[1] + 1 for m in members)
        units = {_unit(repo, m[0]) for m in members}
        sev = 'medium' if span >= 25 or len(members) >= 3 else None
        where = ', '.join(f'{m[0]}:{m[1]}' for m in members[1:6])
        hits.add('DUP-BLOCK', members[0][0], members[0][1],
                 f'{span} lines in {len(members)} places - also {where}'
                 + (' (across repositories)' if len(units) > 1 else ''), severity=sev,
                 files=[f'{m[0]}:{m[1]}-{m[2]}' for m in members])
        out.append({'lines': span, 'places': [f'{m[0]}:{m[1]}-{m[2]}' for m in members]})
    return out


def _lineset(repo: Repo, rel: str) -> set[str]:
    return {s for _, s in _signature_lines(repo, rel)}


def similar(repo: Repo, hits: Hits, comps: list[dict], jvm_files: list) -> int:
    count = 0
    templates = [(c, c['template'], _lineset(repo, c['template'])) for c in comps
                 if c.get('template') and c['kind'] == 'component']
    templates = [t for t in templates if len(t[2]) >= 12]
    reported = set()
    for i in range(len(templates)):
        a, ta, la = templates[i]
        for j in range(i + 1, len(templates)):
            b, tb, lb = templates[j]
            if os.path.dirname(ta) == os.path.dirname(tb):
                continue
            score = len(la & lb) / len(la | lb)
            same_name = os.path.basename(ta) == os.path.basename(tb)
            if score >= 0.75 or (same_name and score >= 0.5):
                key = frozenset((ta, tb))
                if key in reported:
                    continue
                reported.add(key)
                count += 1
                hits.add('REUSE-SIMILAR', a['file'], a['line'],
                         f'{a["name"]} and {b["name"]} ({b["file"]}): templates {round(score * 100)}% identical')
    by_name = defaultdict(list)
    for jf in jvm_files:
        if jf.cls and not is_test_path(jf.rel):
            by_name[jf.name].append(jf)
    for name, group in by_name.items():
        if len(group) < 2 or name in ('Application', 'package-info'):
            continue
        sets = [(jf, _lineset(repo, jf.rel)) for jf in group]
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                (ja, la), (jb, lb) = sets[i], sets[j]
                if len(la) < 10 or not (la | lb):
                    continue
                score = len(la & lb) / len(la | lb)
                if score >= 0.6:
                    count += 1
                    across = _unit(repo, ja.rel) != _unit(repo, jb.rel)
                    hits.add('REUSE-SIMILAR', ja.rel, ja.cls.line,
                             f'{name}: {round(score * 100)}% identical with {jb.rel}'
                             + (' (across repositories)' if across else ''))
    return count


def _body_lines(src, at: int) -> set[str]:
    """Lines of a top-level function: everything up to the next declaration in column 0."""
    out = set()
    for i, line in enumerate(src.code[at:].split('\n')):
        if i and line[:1] not in ('', ' ', '\t', '}', ')', ']', '.'):
            break
        s = re.sub(r'\s+', ' ', line).strip()
        if len(s) >= 4:
            out.add(s)
    return out


def helpers(repo: Repo, hits: Hits):
    defs = defaultdict(list)
    for rel in repo.files:
        if is_test_path(rel) or SKIP_PATH.search(rel) or not rel.endswith(('.ts', '.kt')):
            continue
        src = repo.source(rel)
        if rel.endswith('.ts'):
            found = re.finditer(r'(?m)^export\s+(?:async\s+)?function\s+(\w+)()|^export\s+const\s+(\w+)()\s*=\s*'
                                r'(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::\s*[^=]+)?=>', src.bare)
            items = [(m.group(1) or m.group(3), '', m) for m in found]
        else:
            items = [(m.group(2), m.group(1) or '', m) for m in re.finditer(
                r'(?m)^(?:(?:internal|public|inline)\s+)*fun\s+(?:<[^>]+>\s*)?(?:([\w.<>?, ]+)\.)?(\w+)\s*\(', src.bare)]
        for name, receiver, m in items:
            body = _body_lines(src, m.end())
            if len(body) >= 2:
                defs[(receiver, name)].append((rel, src.line_at(m.start()), body))
    for (receiver, name), places in sorted(defs.items()):
        if len({f for f, _, _ in places}) < 2 or name in COMMON_NAMES or name.startswith(('provide', 'with', 'ng')):
            continue
        similar_places = {(a[0], a[1]) for i, a in enumerate(places) for b in places[i + 1:]
                          if a[0] != b[0] and len(a[2] & b[2]) / len(a[2] | b[2]) >= 0.5} | \
            {(b[0], b[1]) for i, a in enumerate(places) for b in places[i + 1:]
             if a[0] != b[0] and len(a[2] & b[2]) / len(a[2] | b[2]) >= 0.5}
        if len(similar_places) < 2:
            continue
        files = sorted({f for f, _ in similar_places})
        first = min(similar_places)
        hits.add('REUSE-HELPER', first[0], first[1], f'{(receiver + ".") if receiver else ""}{name}() with matching '
                 f'bodies in {len(files)} files: ' + ', '.join(files[:5]), files=files[:40])


def run(repo: Repo, hits: Hits, comps: list[dict], jvm_files: list) -> dict:
    found = blocks(repo, hits)
    count = similar(repo, hits, comps, jvm_files)
    helpers(repo, hits)
    return {'duplicate_blocks': len(found), 'duplicate_lines': sum(b['lines'] for b in found), 'similar': count}
