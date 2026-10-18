"""External scanners when installed: gitleaks, osv-scanner, npm audit, trivy, semgrep, zizmor."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .core import OWN_OUTPUT, Hits, Repo, define, secret_fields, version_tuple

define('TOOL-GITLEAKS', 'gitleaks: secret in the working tree or the git history', 'high', 'secrets',
       'A secret only in history is still leaked - rotate it. Check whether the file still has it.',
       security=True, rule='SEC-5', owasp='A07')
define('TOOL-OSV', 'osv-scanner: vulnerable or malicious dependency', 'high', 'supply-chain',
       'MAL- ids are malicious packages: treat the machine as compromised.', security=True, owasp='A03')
define('TOOL-NPM-AUDIT', 'npm audit: vulnerable dependency', 'medium', 'supply-chain',
       'Direct dependencies first. A dev-only dependency still runs on every CI install.', security=True,
       owasp='A03')
define('TOOL-TRIVY', 'trivy finding', 'medium', 'supply-chain', '', security=True, owasp='A03')
define('TOOL-SEMGREP', 'semgrep finding', 'medium', 'injection', 'Rule-based, read the rule message.',
       security=True)
define('TOOL-ZIZMOR', 'zizmor: GitHub Actions weakness', 'medium', 'ci', '', security=True, owasp='A08')

INSTALL = {'gitleaks': 'brew install gitleaks', 'osv-scanner': 'brew install osv-scanner',
           'trivy': 'brew install trivy', 'semgrep': 'brew install semgrep', 'zizmor': 'brew install zizmor',
           'npm': 'install Node.js'}
SKIP = r'(^|/)(node_modules|dist|build|target|out|coverage|\.angular|\.nx|\.gradle|\.git)/'
SEV = {'critical': 'critical', 'high': 'high', 'error': 'high', 'moderate': 'medium', 'medium': 'medium',
       'warning': 'medium', 'low': 'low', 'info': 'low', 'informational': 'low', 'unknown': 'low', 'note': 'low'}


def _run(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess | str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f'timed out after {timeout}s'
    except OSError as exc:
        return str(exc)


def _missing(name: str) -> dict:
    return {'status': 'not installed', 'install': INSTALL.get(name, '')}


def run(repo: Repo, hits: Hits, stacks: dict, online: bool, workdir: Path, out: Path | None = None,
        versions: dict | None = None) -> dict:
    found = {'ids': {}, 'alias': {}}
    status = {}
    for name, call in (('gitleaks', lambda: gitleaks(repo, hits, workdir)),
                       ('osv-scanner', lambda: osv(repo, hits, stacks, online, out, versions or {}, found)),
                       ('npm audit', lambda: npm_audit(repo, hits, stacks, online, found['alias'])),
                       ('trivy', lambda: trivy(repo, hits, online)),
                       ('semgrep', lambda: semgrep(repo, hits, online)),
                       ('zizmor', lambda: zizmor(repo, hits, online))):
        start = len(hits.items)
        status[name] = call()
        _drop_ignored(repo, hits, start, status[name])
    _second_source(hits, found)
    return status


def _note(status: dict, text: str):
    status['note'] = '; '.join(filter(None, (status.get('note'), text)))


def _drop_ignored(repo: Repo, hits: Hits, start: int, status: dict):
    """The tools read the disk, the scope is git: hits in ignored files go, SB-RESOURCE-UNTRACKED covers resources."""
    kept, ignored = [], 0
    for h in hits.items[start:]:
        file = h.get('file') or ''
        if file and not h.get('history') and repo.ignored(file):
            ignored += 1
        elif not OWN_OUTPUT.search(file):
            kept.append(h)
    if 'findings' in status:
        status['findings'] -= len(hits.items) - start - len(kept)
    hits.items[start:] = kept
    if ignored:
        _note(status, f'{ignored} hits in git-ignored files skipped')


def _second_source(hits: Hits, found: dict):
    for h in hits.items:
        if h['check'] != 'DEPS-FLOOR' or not h.get('package'):
            continue
        ids = found['ids'].get((h['package'].lower(), h.get('version')))
        if ids is None:
            continue
        wanted = set(re.findall(r'(?:CVE|GHSA)-[\w-]+', h['evidence'])) | {h.get('advisory')}
        text = f'osv-scanner confirms {", ".join(sorted(ids & wanted))}' if ids & wanted else \
            f'osv-scanner lists other advisories: {", ".join(sorted(ids)[:3])}' if ids else \
            'osv-scanner knows no advisory for this version'
        h['note'] = '; '.join(filter(None, (h.get('note'), text)))


def _advisory(ids: list[str]) -> str | None:
    return next((i for prefix in ('CVE-', 'GHSA-') for i in ids if i.startswith(prefix)), ids[0] if ids else None)


def gitleaks(repo: Repo, hits: Hits, workdir: Path) -> dict:
    if not shutil.which('gitleaks'):
        return _missing('gitleaks')
    config = workdir / 'gitleaks.toml'
    config.write_text("[extend]\nuseDefault = true\n\n[[allowlists]]\npaths = ['''" + SKIP +
                      "''', '''docs/mw-(codereview|topomap)-\\d{8}/''']\n", encoding='utf-8')
    targets = [(repo.root, '', 'git')] if repo.git else \
        [(repo.root / n, n + '/', 'git') for n in repo.nested] or [(repo.root, '', 'dir')]
    seen, errors = {}, []
    for where, prefix, mode in targets:
        # the report goes to stdout, unredacted, so the value can be hashed without ever touching the disk
        proc = _run(['gitleaks', mode, str(where), '--no-banner', '--exit-code', '0', '--log-level', 'error',
                     '--config', str(config), '--report-format', 'json', '--report-path', '-'], where, 900)
        if isinstance(proc, str):
            errors.append(proc)
            continue
        try:
            findings = json.loads(proc.stdout or '[]')
        except ValueError:
            errors.append(proc.stderr.strip()[-200:])
            continue
        for f in findings:
            file = f.get('File') or ''
            rel = os.path.relpath(file, repo.root) if os.path.isabs(file) else prefix + file
            seen.setdefault((rel, f.get('RuleID'), f.get('StartLine'), mode), []).append(f)
    for (rel, rule, line, mode), group in seen.items():
        first = group[0]
        current = rel in repo.files
        commits = sorted({g.get('Commit', '')[:8] for g in group if g.get('Commit')})
        hits.add('TOOL-GITLEAKS', rel, line, f'{rule}: {first.get("Description", "")}'
                 + (f'   commits {", ".join(commits[:3])}' if commits else '')
                 + ('' if current or mode == 'dir' else '   (file no longer in the tree - history only)'),
                 history=not current and mode == 'git',
                 **(secret_fields(first['Secret']) if first.get('Secret') else {}))
    if errors and not seen:
        return {'status': 'failed', 'detail': '; '.join(errors)[:200]}
    mode = 'git history' if targets[0][2] == 'git' else 'working tree'
    return {'status': 'ran', 'mode': mode + (f', {len(targets)} repos' if len(targets) > 1 else ''),
            'findings': len(seen)}


def _sbom(out: Path, artifacts: dict[str, str]) -> Path:
    components = []
    for coord, version in sorted(artifacts.items()):
        group, _, name = coord.partition(':')
        purl = f'pkg:maven/{group}/{name}@{version}'
        components.append({'type': 'library', 'bom-ref': purl, 'group': group, 'name': name, 'version': version,
                           'purl': purl})
    path = out / 'bom.cdx.json'
    path.write_text(json.dumps({'bomFormat': 'CycloneDX', 'specVersion': '1.5', 'version': 1,
                                'components': components}, indent=1), encoding='utf-8')
    return path


def osv(repo: Repo, hits: Hits, stacks: dict, online: bool, out: Path | None, versions: dict, found: dict) -> dict:
    if not shutil.which('osv-scanner'):
        return _missing('osv-scanner')
    artifacts = (versions.get('spring') or {}).get('artifacts') or {}
    sbom = _sbom(out, artifacts) if artifacts and out else None
    if not online:
        return {'status': 'skipped (needs --online)', **({'sbom': str(sbom)} if sbom else {})}
    proc = _run(['osv-scanner', 'scan', 'source', '-r', '--format', 'json', str(repo.root)]
                + (['-L', str(sbom)] if sbom else []), repo.root, 600)
    if isinstance(proc, str):
        return {'status': 'failed', 'detail': proc}
    try:
        data = json.loads(proc.stdout or '{}')
    except ValueError:
        return {'status': 'failed', 'detail': (proc.stderr or proc.stdout).strip()[-200:]}
    build_file = next((f for f in repo.files if os.path.basename(f) in ('build.gradle.kts', 'build.gradle', 'pom.xml')),
                      None)
    count = 0
    for result in data.get('results') or []:
        path = (result.get('source') or {}).get('path', '')
        from_sbom = sbom is not None and os.path.realpath(path) == os.path.realpath(sbom)
        source = build_file if from_sbom else os.path.relpath(path, repo.root)
        for pkg in result.get('packages') or []:
            meta = pkg.get('package') or {}
            key = (str(meta.get('name')).lower(), meta.get('version'))
            for group in pkg.get('groups') or [{'ids': [v.get('id')], 'max_severity': ''}
                                               for v in pkg.get('vulnerabilities') or []]:
                ids = group.get('ids') or []
                every = list(group.get('aliases') or []) + list(ids)
                found['ids'].setdefault(key, set()).update(every)
                found['alias'].update(dict.fromkeys(every, _advisory(every)))
                try:
                    score = float(group.get('max_severity') or 0)
                except ValueError:
                    score = 0
                sev = 'critical' if any(str(i).startswith('MAL-') for i in ids) or score >= 9 else \
                    'high' if score >= 7 else 'medium' if score >= 4 or not score else 'low'
                summary = next((v.get('summary', '') for v in pkg.get('vulnerabilities') or []
                                if v.get('id') in ids), '')
                hits.add('TOOL-OSV', source, None, f'{meta.get("name")} {meta.get("version")}: '
                                                   f'{", ".join(ids[:3])} {summary}', severity=sev,
                         package=meta.get('name'), version=meta.get('version'),
                         advisory=_advisory(every))
                count += 1
    status = {'status': 'ran', 'findings': count}
    if sbom:
        for coord, version in artifacts.items():
            found['ids'].setdefault((coord.lower(), version), set())
        status['sbom'] = str(sbom)
        _note(status, f'SBOM of {len(artifacts)} resolved Maven artifacts')
    elif 'gradle' in ((stacks.get('spring') or {}).get('build') or []) and not any(
            (repo.root / os.path.dirname(f) / 'gradle.lockfile').is_file() for f in repo.files
            if os.path.basename(f) in ('build.gradle.kts', 'build.gradle')):
        _note(status, '0 Gradle packages read (no lockfile; --resolve feeds an SBOM)')
    elif 'No package sources found' in (proc.stderr or ''):
        _note(status, 'no lockfile or SBOM found')
    return status


def _walk_up(path: list[str], up, direct) -> str | None:
    queue, seen = [path], set(path)
    while queue:
        path = queue.pop(0)
        if direct(path[-1]):
            return 'path ' + ' <- '.join(path + ['(direct)'])
        for parent in sorted(set(up(path[-1])) - seen - {''}):
            seen.add(parent)
            queue.append(path + [parent])
    return None


def _npm_path(name: str, node: str, vulns: dict, owners: dict) -> str | None:
    # npm stops marking dependents whose range already allows the fix - then the lockfile graph has to do
    chain = [p.strip('/') for p in node.split('node_modules/')[1:]][::-1] or [name]
    return _walk_up([name], lambda n: (vulns.get(n) or {}).get('effects') or [],
                    lambda n: (vulns.get(n) or {}).get('isDirect')) or \
        _walk_up(chain, lambda n: owners.get(n, ()), lambda n: '' in owners.get(n, ()))


def npm_audit(repo: Repo, hits: Hits, stacks: dict, online: bool, alias: dict) -> dict:
    roots = sorted({os.path.dirname(f) for f in repo.files if os.path.basename(f) == 'package.json'
                    and (repo.root / os.path.dirname(f) / 'package-lock.json').is_file()})
    if not roots:
        return {'status': 'skipped (no package-lock.json)'}
    if not shutil.which('npm'):
        return _missing('npm')
    if not online:
        return {'status': 'skipped (needs --online)'}
    count, errors = 0, []
    for base in roots:
        proc = _run(['npm', 'audit', '--json', '--package-lock-only'], repo.root / base, 300)
        if isinstance(proc, str):
            errors.append(proc)
            continue
        try:
            data = json.loads(proc.stdout or '{}')
        except ValueError:
            errors.append(proc.stderr.strip()[-120:])
            continue
        lock = os.path.join(base, 'package-lock.json') if base else 'package-lock.json'
        try:
            packages = json.loads((repo.root / lock).read_text(encoding='utf-8')).get('packages') or {}
        except (OSError, ValueError):
            packages = {}
        owners = {}
        for where, meta in packages.items():
            owner = where.rsplit('node_modules/', 1)[-1] if 'node_modules/' in where else ''
            for dep in {**(meta.get('dependencies') or {}), **(meta.get('optionalDependencies') or {}),
                        **(meta.get('devDependencies') or {} if not owner else {})}:
                owners.setdefault(dep, set()).add(owner)
        vulns = data.get('vulnerabilities') or {}
        dependents = {}
        for name, vuln in vulns.items():
            for via in vuln.get('via') or []:
                if isinstance(via, str):
                    dependents.setdefault(via, set()).add(name)
        # npm marks every ancestor of a vulnerable package as vulnerable too
        for name, vuln in vulns.items():
            advisories = [v for v in vuln.get('via') or [] if isinstance(v, dict)]
            if not advisories:
                continue
            titles = [v.get('title', '') + (f' ({v.get("url", "").rsplit("/", 1)[-1]})' if v.get('url') else '')
                      for v in advisories]
            parents = dependents.get(name, set())
            sev = SEV.get(vuln.get('severity', 'low'), 'low')
            node = next(iter(vuln.get('nodes') or []), f'node_modules/{name}')
            fix = vuln.get('fixAvailable')
            current = isinstance(fix, dict) and (packages.get(f'node_modules/{fix.get("name")}') or {}).get('version')
            ghsa = _advisory([v.get('url', '').rsplit('/', 1)[-1] for v in advisories if v.get('url')])
            notes = [_npm_path(name, node, vulns, owners) if sev in ('critical', 'high') else None,
                     f'fix is a downgrade to {fix["name"]} {fix["version"]}' if current and fix.get('version') and
                     version_tuple(fix['version']) < version_tuple(current) else None]
            hits.add('TOOL-NPM-AUDIT', lock, None,
                     f'{name} {vuln.get("range", "")}: {"; ".join(titles[:2])}'
                     + ('   direct' if vuln.get('isDirect') else
                        f'   via {", ".join(sorted(parents)[:3])}' if parents else '   transitive')
                     + ('   fix available' if vuln.get('fixAvailable') else ''),
                     severity=sev, package=name, version=(packages.get(node) or {}).get('version'),
                     advisory=alias.get(ghsa, ghsa),
                     **({'note': '; '.join(filter(None, notes))} if any(notes) else {}))
            count += 1
    return {'status': 'ran' if not errors else 'partly failed', 'findings': count,
            **({'detail': '; '.join(errors)[:200]} if errors else {})}


def _trivy_secret(path: Path, finding: dict) -> str | None:
    """Trivy masks the value in its report - the real one sits in the file at the reported byte offset."""
    stars = max((len(run) for run in re.findall(r'\*+', finding.get('Match') or '')), default=0)
    offset = finding.get('Offset')
    if not stars or not isinstance(offset, int):
        return None
    try:
        with open(path, 'rb') as fh:
            fh.seek(offset)
            value = fh.read(stars).decode('utf-8', 'replace')
    except OSError:
        return None
    return value if value.strip() and '*' not in value and '\n' not in value else None


def trivy(repo: Repo, hits: Hits, online: bool) -> dict:
    if not shutil.which('trivy'):
        return _missing('trivy')
    if not online:
        return {'status': 'skipped (needs --online for its database)'}
    proc = _run(['trivy', 'fs', '--quiet', '--format', 'json', '--scanners', 'vuln,secret,misconfig',
                 '--skip-dirs', 'node_modules', str(repo.root)], repo.root, 900)
    if isinstance(proc, str):
        return {'status': 'failed', 'detail': proc}
    try:
        data = json.loads(proc.stdout or '{}')
    except ValueError:
        return {'status': 'failed', 'detail': proc.stderr.strip()[-200:]}
    count = 0
    for result in data.get('Results') or []:
        target = result.get('Target')
        for v in result.get('Vulnerabilities') or []:
            hits.add('TOOL-TRIVY', target, None, f'{v.get("PkgName")} {v.get("InstalledVersion")} -> '
                                                 f'{v.get("FixedVersion") or "no fix"}: {v.get("VulnerabilityID")} '
                                                 f'{v.get("Title", "")}', severity=SEV.get(str(v.get('Severity')).lower(), 'low'),
                     package=v.get('PkgName'), version=v.get('InstalledVersion'), advisory=v.get('VulnerabilityID'))
            count += 1
        for s in result.get('Secrets') or []:
            raw = _trivy_secret(repo.root / target, s) if target else None
            hits.add('TOOL-TRIVY', target, s.get('StartLine'), f'secret {s.get("RuleID")}: {s.get("Title")}',
                     severity=SEV.get(str(s.get('Severity')).lower(), 'high'), **(secret_fields(raw) if raw else {}))
            count += 1
        for m in result.get('Misconfigurations') or []:
            line = (m.get('CauseMetadata') or {}).get('StartLine')
            hits.add('TOOL-TRIVY', target, line, f'{m.get("ID")}: {m.get("Title")}',
                     severity=SEV.get(str(m.get('Severity')).lower(), 'low'))
            count += 1
    return {'status': 'ran', 'findings': count}


def semgrep(repo: Repo, hits: Hits, online: bool) -> dict:
    if not shutil.which('semgrep'):
        return _missing('semgrep')
    if not online:
        return {'status': 'skipped (registry rules need --online)'}
    proc = _run(['semgrep', 'scan', '--config', 'p/default', '--config', 'p/owasp-top-ten', '--json', '--metrics=off',
                 '--quiet',
                 '--exclude', 'node_modules', '--exclude', 'dist', '--exclude', 'build', str(repo.root)],
                repo.root, 900)
    if isinstance(proc, str):
        return {'status': 'failed', 'detail': proc}
    try:
        data = json.loads(proc.stdout or '{}')
    except ValueError:
        return {'status': 'failed', 'detail': proc.stderr.strip()[-200:]}
    count = 0
    for r in data.get('results') or []:
        extra = r.get('extra') or {}
        hits.add('TOOL-SEMGREP', os.path.relpath(r.get('path', ''), repo.root) if os.path.isabs(r.get('path', ''))
                 else r.get('path'), (r.get('start') or {}).get('line'),
                 f'{r.get("check_id", "").rsplit(".", 1)[-1]}: {extra.get("message", "")}',
                 severity=SEV.get(str(extra.get('severity', '')).lower(), 'medium'))
        count += 1
    return {'status': 'ran', 'findings': count}


def zizmor(repo: Repo, hits: Hits, online: bool) -> dict:
    if not (repo.root / '.github' / 'workflows').is_dir():
        return {'status': 'skipped (no .github/workflows)'}
    if not shutil.which('zizmor'):
        return _missing('zizmor')
    cmd = ['zizmor', '--format', 'json', str(repo.root)] + ([] if online else ['--offline'])
    proc = _run(cmd, repo.root, 300)
    if isinstance(proc, str):
        return {'status': 'failed', 'detail': proc}
    try:
        data = json.loads(proc.stdout or '[]')
    except ValueError:
        return {'status': 'failed', 'detail': proc.stderr.strip()[-200:]}
    count = 0
    for f in data if isinstance(data, list) else []:
        det = f.get('determinations') or {}
        loc = (f.get('locations') or [{}])[0]
        path = (((loc.get('symbolic') or {}).get('key') or {}).get('Local') or {}).get('given_path')
        row = (((loc.get('concrete') or {}).get('location') or {}).get('start_point') or {}).get('row')
        hits.add('TOOL-ZIZMOR', os.path.relpath(path, repo.root) if path and os.path.isabs(path) else path,
                 row + 1 if isinstance(row, int) else None, f'{f.get("ident")}: {f.get("desc")}',
                 severity=SEV.get(str(det.get('severity', '')).lower(), 'medium'))
        count += 1
    return {'status': 'ran', 'findings': count}
