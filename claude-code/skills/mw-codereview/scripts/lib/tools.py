"""External scanners when installed: gitleaks, osv-scanner, npm audit, trivy, semgrep, zizmor."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .core import Hits, Repo, define

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


def run(repo: Repo, hits: Hits, stacks: dict, online: bool, workdir: Path) -> dict:
    status = {'gitleaks': gitleaks(repo, hits, workdir)}
    status['osv-scanner'] = osv(repo, hits, online)
    status['npm audit'] = npm_audit(repo, hits, stacks, online)
    status['trivy'] = trivy(repo, hits, online)
    status['semgrep'] = semgrep(repo, hits, online)
    status['zizmor'] = zizmor(repo, hits, online)
    return status


def gitleaks(repo: Repo, hits: Hits, workdir: Path) -> dict:
    if not shutil.which('gitleaks'):
        return _missing('gitleaks')
    config = workdir / 'gitleaks.toml'
    config.write_text("[extend]\nuseDefault = true\n\n[[allowlists]]\npaths = ['''" + SKIP +
                      "''', '''docs/mw-(codereview|topomap)-\\d{8}/''']\n", encoding='utf-8')
    targets = [(repo.root, '', 'git')] if repo.git else \
        [(repo.root / n, n + '/', 'git') for n in repo.nested] or [(repo.root, '', 'dir')]
    seen, errors = {}, []
    for i, (where, prefix, mode) in enumerate(targets):
        report = workdir / f'gitleaks-{i}.json'
        proc = _run(['gitleaks', mode, str(where), '--no-banner', '--redact', '--exit-code', '0',
                     '--log-level', 'error', '--config', str(config), '--report-format', 'json',
                     '--report-path', str(report)], where, 900)
        if isinstance(proc, str):
            errors.append(proc)
            continue
        try:
            findings = json.loads(report.read_text(encoding='utf-8') or '[]') if report.is_file() else []
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
                 history=not current and mode == 'git')
    if errors and not seen:
        return {'status': 'failed', 'detail': '; '.join(errors)[:200]}
    mode = 'git history' if targets[0][2] == 'git' else 'working tree'
    return {'status': 'ran', 'mode': mode + (f', {len(targets)} repos' if len(targets) > 1 else ''),
            'findings': len(seen)}


def osv(repo: Repo, hits: Hits, online: bool) -> dict:
    if not shutil.which('osv-scanner'):
        return _missing('osv-scanner')
    if not online:
        return {'status': 'skipped (needs --online)'}
    proc = _run(['osv-scanner', 'scan', 'source', '-r', '--format', 'json', str(repo.root)], repo.root, 600)
    if isinstance(proc, str):
        return {'status': 'failed', 'detail': proc}
    try:
        data = json.loads(proc.stdout or '{}')
    except ValueError:
        return {'status': 'failed', 'detail': (proc.stderr or proc.stdout).strip()[-200:]}
    count = 0
    for result in data.get('results') or []:
        source = os.path.relpath((result.get('source') or {}).get('path', ''), repo.root)
        for pkg in result.get('packages') or []:
            meta = pkg.get('package') or {}
            for group in pkg.get('groups') or [{'ids': [v.get('id')], 'max_severity': ''}
                                               for v in pkg.get('vulnerabilities') or []]:
                ids = group.get('ids') or []
                try:
                    score = float(group.get('max_severity') or 0)
                except ValueError:
                    score = 0
                sev = 'critical' if any(str(i).startswith('MAL-') for i in ids) or score >= 9 else \
                    'high' if score >= 7 else 'medium' if score >= 4 or not score else 'low'
                summary = next((v.get('summary', '') for v in pkg.get('vulnerabilities') or []
                                if v.get('id') in ids), '')
                hits.add('TOOL-OSV', source, None, f'{meta.get("name")} {meta.get("version")}: '
                                                   f'{", ".join(ids[:3])} {summary}', severity=sev)
                count += 1
    return {'status': 'ran', 'findings': count}


def npm_audit(repo: Repo, hits: Hits, stacks: dict, online: bool) -> dict:
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
            hits.add('TOOL-NPM-AUDIT', lock, None,
                     f'{name} {vuln.get("range", "")}: {"; ".join(titles[:2])}'
                     + ('   direct' if vuln.get('isDirect') else
                        f'   via {", ".join(sorted(parents)[:3])}' if parents else '   transitive')
                     + ('   fix available' if vuln.get('fixAvailable') else ''),
                     severity=SEV.get(vuln.get('severity', 'low'), 'low'))
            count += 1
    return {'status': 'ran' if not errors else 'partly failed', 'findings': count,
            **({'detail': '; '.join(errors)[:200]} if errors else {})}


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
                                                 f'{v.get("Title", "")}', severity=SEV.get(str(v.get('Severity')).lower(), 'low'))
            count += 1
        for s in result.get('Secrets') or []:
            hits.add('TOOL-TRIVY', target, s.get('StartLine'), f'secret {s.get("RuleID")}: {s.get("Title")}',
                     severity=SEV.get(str(s.get('Severity')).lower(), 'high'))
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
