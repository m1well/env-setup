"""Repository-wide checks: secrets, containers, CI, npm supply chain, web server and shell scripts."""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import math
import os
import re
import zipfile
from pathlib import Path
from types import SimpleNamespace

from .core import (SECRET_FILE_EXT, Hits, Repo, config_entries, define, entropy, is_test_path, read_text, redact,
                   secret_fields)

define('SB-RESOURCE-UNTRACKED', 'Git-ignored file under src/main/resources ends up in the artifact', 'high', 'secrets',
       'Real when no build exclude drops the file and the value is a live credential - bootJar and Maven package '
       'take everything in src/main/resources, git or not; read it only with scan.py --cat.', security=True,
       rule='SEC-5', owasp='A07')
define('SB-ARTIFACT-CONFIG', 'Built jar or war carries a Spring config file that is not in git', 'high', 'secrets',
       'Real when this jar, or an image built from it, left the machine - read the entry only with '
       'scan.py --cat <jar>!<entry>.', security=True, rule='SEC-5', owasp='A07')
define('REPO-SECRET-TOKEN', 'Credential in a known token format', 'critical', 'secrets',
       'Rotate first, then remove - a committed token is leaked, history included. Check whether it is a '
       'revoked test token.', security=True, rule='SEC-5', owasp='A07')
define('REPO-SECRET-LITERAL', 'Secret-looking literal assigned in code', 'high', 'secrets',
       'Open the line: a real credential, a test fixture or a constant name that only looks like one.',
       security=True, rule='SEC-5', owasp='A07')
define('REPO-SECRET-FILE', 'Private key, keystore or .env file in the repository', 'high', 'secrets',
       'Check whether it is tracked (git ls-files) and whether the key is used anywhere real.',
       security=True, rule='SEC-5', owasp='A07')
define('REPO-GITIGNORE', '.env files not ignored', 'low', 'secrets', '', security=True, owasp='A07')
define('DOCKER-ROOT', 'Container runs as root', 'medium', 'container',
       'No USER in the final stage. Add a non-root user or use a nonroot base image.', security=True,
       owasp='A02')
define('DOCKER-UNPINNED', 'Base image without a pinned tag or digest', 'low', 'supply-chain',
       'Tags move. A digest (image:tag@sha256:...) makes the build reproducible.', security=True, owasp='A03')
define('DOCKER-REMOTE', 'Remote code fetched during the image build', 'medium', 'supply-chain',
       'ADD <url> or curl | sh runs whatever the server returns today.', security=True, owasp='A03')
define('DOCKER-SECRET', 'Secret passed through ENV or ARG', 'high', 'secrets',
       'Both end up in the image history. RUN --mount=type=secret is the fix.', security=True, owasp='A07')
define('COMPOSE-RISK', 'Privileged container, host network or Docker socket', 'high', 'container',
       'Root on the host for whoever gets into the container.', security=True, owasp='A02')
define('COMPOSE-SECRET', 'Literal credential in a compose file', 'low', 'secrets',
       'Fine for a local database, a finding if the file is used for a real deployment.', security=True,
       owasp='A07')
define('K8S-RISK', 'Privileged pod settings', 'high', 'container', '', security=True, owasp='A02')
define('K8S-SECRET', 'Kubernetes Secret committed in plain base64', 'high', 'secrets',
       'base64 is not encryption. Sealed Secrets, SOPS or an external secret store.', security=True,
       owasp='A07')
define('K8S-NO-NONROOT', 'Workload without runAsNonRoot', 'medium', 'container', '', security=True, owasp='A02')
define('CI-UNPINNED-ACTION', 'GitHub Action not pinned to a commit SHA', 'medium', 'supply-chain',
       'tj-actions/changed-files (CVE-2025-30066) moved its tags to a malicious commit. Pin third-party '
       'actions to the full SHA.', security=True, owasp='A03')
define('CI-PR-TARGET', 'pull_request_target runs code from the pull request', 'critical', 'ci',
       'The PR code runs with secrets and a write token. Never check out the head ref there.', security=True,
       owasp='A08')
define('CI-SCRIPT-INJECTION', 'Untrusted event data interpolated into a run: step', 'high', 'injection',
       'A PR title or branch name becomes shell code. Pass it through env: and quote it.', security=True,
       owasp='A05')
define('CI-PERMISSIONS', 'Workflow without explicit permissions', 'low', 'ci',
       'The token gets the repository default, often write. Set permissions: contents: read on top.',
       security=True, owasp='A01')
define('CI-WORM-IOC', 'Indicator of the Shai-Hulud npm worm', 'critical', 'supply-chain',
       'Treat the machine and every token it had as compromised.', security=True, owasp='A03')
define('NPM-NO-LOCKFILE', 'package.json without a lockfile', 'medium', 'supply-chain',
       'Every install resolves fresh - the next compromised patch release lands without a diff.', security=True,
       owasp='A03')
define('NPM-LOOSE-VERSION', 'Dependency on *, latest or a git URL', 'medium', 'supply-chain', '', security=True,
       owasp='A03')
define('NPM-INSTALL', 'npm install instead of npm ci in a build', 'low', 'supply-chain',
       'npm ci installs exactly the lockfile and fails when it is out of date.', security=True, owasp='A03')
define('NPM-NO-SCRIPT-GUARD', 'No guard against install scripts or fresh releases', 'low', 'supply-chain',
       'ignore-scripts=true, npm min-release-age or pnpm minimumReleaseAge stop most worm-style attacks '
       '(Shai-Hulud ran from preinstall/postinstall).', security=True, owasp='A03')
define('NPM-TOKEN', '.npmrc with a literal auth token', 'critical', 'secrets', '', security=True, owasp='A07')
define('WEB-HEADERS', 'Web server config without security headers', 'medium', 'config',
       'nginx drops inherited add_header lines in any location that sets its own - check per location.',
       security=True, owasp='A02')
define('HTTP-X-PREFIX', 'Own HTTP header named with the deprecated X- prefix', 'low', 'http',
       'RFC 6648 (BCP 178) deprecated X- in 2012, RFC 9110 repeats it: once such a header is standardised, both names '
       'live on (X-Forwarded-For next to Forwarded). A plain name, with the product as prefix when it must not '
       'collide (Myapp-Tenant). Renaming a header clients already send breaks them - accept both for a while.')
define('HTTP-XSS-PROTECTION', 'X-XSS-Protection switched on', 'low', 'config',
       'Chrome removed the XSS auditor in version 78, Firefox never had one; where it still runs, mode=block lets an '
       'attacker switch off chosen scripts and probe the page. OWASP Secure Headers: send 0 or nothing and let the CSP '
       'do the work. Spring Security 6 sends 0 by default - only an explicit config brings 1 back. In a Keycloak realm '
       'it is browserSecurityHeaders.xXSSProtection.', security=True, owasp='A02')
define('SH-INSECURE', 'Insecure pattern in a shell script', 'medium', 'ci',
       'TLS verification off, a password on the command line, world-writable files, host keys ignored.',
       security=True, owasp='A02')

TOKENS = [
    ('AWS access key', r'\b(AKIA|ASIA)[0-9A-Z]{16}\b'),
    ('GitHub token', r'\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b'),
    ('GitLab token', r'\bglpat-[A-Za-z0-9_-]{20,}\b'),
    ('Slack token', r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b'),
    ('Slack webhook', r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+'),
    ('Discord webhook', r'https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]{20,}'),
    ('Discord bot token', r'\b[MNO][A-Za-z\d_-]{23,27}\.[\w-]{6}\.[\w-]{27,40}\b'),
    ('Stripe live key', r'\b(sk|rk)_live_[A-Za-z0-9]{20,}\b'),
    ('Google API key', r'\bAIza[0-9A-Za-z_-]{35}\b'),
    ('OpenAI key', r'\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,}\b|\bsk-proj-[A-Za-z0-9_-]{60,}\b'),
    ('Anthropic key', r'\bsk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_-]{80,}\b'),
    ('OpenRouter key', r'\bsk-or-v1-[a-f0-9]{64}\b'),
    ('npm token', r'\bnpm_[A-Za-z0-9]{36}\b'),
    ('SendGrid key', r'\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b'),
    ('Private key', r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----'),
    ('Credentials in URL', r'\b[a-z][a-z0-9+.-]{2,}://[^/\s:@"\'`$<>{}]{2,}:[^/\s:@"\'`$<>{}*]{4,}@[\w.-]+'),
    ('JSON web token', r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b'),
]
TOKEN_RX = [(name, re.compile(rx)) for name, rx in TOKENS]
PEM_BLOCK = re.compile(r'-----BEGIN[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----(?:[\s\S]{0,10000}?'
                       r'-----END[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----|[^\n]*)')
LITERAL = re.compile(r'(?i)\b([\w.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key|'
                     r'private[_-]?key|client[_-]?secret|auth[_-]?key|signing[_-]?key|credentials?))["\']?\s*'
                     r'(?::\s*\w+\s*)?[:=]\s*["\'`]([^"\'`\s]{8,})["\'`]')
PLACEHOLDER = re.compile(r'(?i)(\$\{|\{\{|<[\w-]+>|%[\w]+%|^x{3,}|\*{3,}|changeme|change-me|your[-_]|example|'
                         r'dummy|sample|placeholder|replace|redacted|todo|fixme|test|fake|mock|secret$|password$)')
SECRETISH_KEY = re.compile(r'(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|access[_-]?key|'
                           r'credentials?)')
SAFE_EVENT_FIELD = re.compile(r'\.(number|id|node_id|sha|size|run_id|run_number|created_at|updated_at|'
                              r'merged|draft|state|action)\s*\}\}')
WORKLOADS = {'Deployment', 'StatefulSet', 'DaemonSet', 'Pod', 'Job', 'CronJob', 'ReplicaSet'}


def run(repo: Repo, hits: Hits, stacks: dict) -> dict:
    secrets(repo, hits)
    untracked_resources(repo, hits)
    artifacts(repo, hits)
    docker(repo, hits)
    compose(repo, hits)
    kubernetes(repo, hits)
    ci(repo, hits)
    npm(repo, hits, stacks)
    web_servers(repo, hits)
    custom_headers(repo, hits)
    xss_auditor(repo, hits)
    shell(repo, hits)
    return {}


def _code_like(rel: str) -> bool:
    return rel.endswith(('.kt', '.java', '.ts', '.js', '.mjs', '.cjs', '.py', '.sh', '.groovy', '.gradle', '.kts'))


def secrets(repo: Repo, hits: Hits):
    spring_config = re.compile(r'(^|/)(application|bootstrap)(-[\w.-]+)?\.(ya?ml|properties)$')
    for rel in repo.files:
        name = os.path.basename(rel)
        suffix = os.path.splitext(name)[1].lower()
        src = repo.source(rel)
        text = src.text
        tracked = repo.is_tracked(rel)
        if suffix in ('.pem', '.key', '.p12', '.pfx', '.jks', '.keystore', '.ppk', '.kdbx') or \
                name in ('id_rsa', 'id_ed25519', 'id_ecdsa', '.pypirc', '.netrc'):
            if suffix == '.pem' and 'PRIVATE KEY' not in text and 'BEGIN' in text:
                continue
            hits.add('REPO-SECRET-FILE', rel, None, f'{name} ({"tracked" if tracked else "untracked, not ignored"})',
                     severity='critical' if 'PRIVATE KEY' in text and tracked else None)
            continue
        if re.match(r'\.env(\.|$)', name) and not re.search(r'\.(example|sample|template|dist|defaults?)$', name):
            hits.add('REPO-SECRET-FILE', rel, None, f'{name} ({"tracked" if tracked else "untracked, not ignored"})',
                     severity='high' if tracked else 'medium')
            for i, line in enumerate(src.lines, 1):
                m = re.match(r'\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*["\']?([^"\'\s#]+)', line)
                if m and SECRETISH_KEY.search(m.group(1)) and not PLACEHOLDER.search(m.group(2)):
                    hits.add('REPO-SECRET-LITERAL', rel, i, f'{m.group(1)}={redact(m.group(2))}',
                             **secret_fields(m.group(2)))
        if not text or name == 'package-lock.json':
            continue
        token_lines = set()
        for label, rx in TOKEN_RX:
            for m in rx.finditer(text):
                value = m.group(0)
                if label == 'Credentials in URL' and (PLACEHOLDER.search(value) or re.search(r'://[^:]+:\$', value)):
                    continue
                line = src.line_at(m.start())
                token_lines.add(line)
                sev = 'medium' if label == 'JSON web token' else None
                hits.add('REPO-SECRET-TOKEN', rel, line, f'{label}: {redact(value)}', severity=sev,
                         tracked=tracked, **secret_fields(_raw_secret(label, text, m)))
        if _code_like(rel) and not spring_config.search(rel) and not re.search(r'environment[\w.-]*\.ts$', rel):
            code = src.code
            for m in LITERAL.finditer(code):
                key, value = m.group(1), m.group(2)
                if PLACEHOLDER.search(value) or entropy(value) < 3.0 or re.fullmatch(r'[a-z.\-_]+', value) or \
                        value.startswith(('/', 'http', 'classpath:', 'Bearer')) or re.fullmatch(r'[A-Z0-9_]+', value) \
                        or re.search(r'(?i)(header|param|name|key|field|label|type|url|path|prefix)$', key):
                    continue
                if src.line_at(m.start()) not in token_lines:
                    hits.add('REPO-SECRET-LITERAL', rel, src.line_at(m.start()), f'{key} = {redact(value)}',
                             **secret_fields(value))
    ignore = repo.root / '.gitignore'
    if repo.git and any(re.match(r'\.env(\.|$)', os.path.basename(f)) for f in repo.files) and \
            not (ignore.is_file() and re.search(r'(?m)^\s*\*?\.env', ignore.read_text(errors='replace'))):
        hits.add('REPO-GITIGNORE', '.gitignore', None, '.env files present, no .env pattern in .gitignore')


def _raw_secret(label: str, text: str, m: re.Match) -> str:
    if label == 'Private key':
        return PEM_BLOCK.match(text, m.start()).group(0)
    if label == 'Credentials in URL':
        return re.search(r'://[^:]+:([^@]+)@', m.group(0)).group(1)
    return m.group(0)


def _logical_lines(text: str) -> list[tuple[int, str]]:
    out, buf, start = [], '', 0
    for i, line in enumerate(text.split('\n'), 1):
        if not buf:
            start = i
        stripped = line.rstrip()
        if stripped.endswith('\\'):
            buf += stripped[:-1] + ' '
            continue
        buf += stripped
        out.append((start, buf))
        buf = ''
    if buf:
        out.append((start, buf))
    return out


def docker(repo: Repo, hits: Hits):
    for rel in repo.files:
        name = os.path.basename(rel)
        if not re.match(r'(Dockerfile|Containerfile)(\.[\w.-]+)?$|.+\.dockerfile$', name):
            continue
        lines = [(n, l.strip()) for n, l in _logical_lines(repo.source(rel).text) if l.strip() and not l.strip().startswith('#')]
        stages, aliases = [], set()
        for n, l in lines:
            m = re.match(r'(?i)FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?', l)
            if m:
                stages.append((n, m.group(1)))
                if m.group(2):
                    aliases.add(m.group(2).lower())
                image = m.group(1)
                if image.lower() not in aliases and image != 'scratch' and '@sha256:' not in image and \
                        '$' not in image:
                    tag = image.rsplit('/', 1)[-1]
                    if ':' not in tag or tag.endswith(':latest'):
                        hits.add('DOCKER-UNPINNED', rel, n, l)
            if re.match(r'(?i)ADD\s+(--\S+\s+)*https?://', l) and '--checksum' not in l:
                hits.add('DOCKER-REMOTE', rel, n, l)
            if re.search(r'(curl|wget)\s[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b', l):
                hits.add('DOCKER-REMOTE', rel, n, l)
            env = re.match(r'(?i)(ENV|ARG)\s+(\w+)(?:\s*=\s*|\s+)?(\S*)', l)
            if env and SECRETISH_KEY.search(env.group(2)) and not re.search(r'(?i)(_FILE|_PATH|_URL|_ID)$', env.group(2)):
                literal = env.group(3) and not env.group(3).startswith('$')
                hits.add('DOCKER-SECRET', rel, n, f'{env.group(1)} {env.group(2)}' +
                         (f'={redact(env.group(3))}' if literal else ''),
                         severity='high' if literal else 'medium')
            if re.search(r'\bnpm\s+(install|i)\b(?!\s+-g)', l) and 'npm ci' not in l:
                hits.add('NPM-INSTALL', rel, n, l)
        if not stages:
            continue
        final_line, final_image = stages[-1]
        final_lines = [l for n, l in lines if n >= final_line]
        users = [re.match(r'(?i)USER\s+(\S+)', l).group(1) for l in final_lines if re.match(r'(?i)USER\s+\S+', l)]
        nonroot_base = re.search(r'(?i)nonroot|chainguard|cgr\.dev|dhi\.io|distroless.*:nonroot|-rootless', final_image)
        if (not users or users[-1] in ('root', '0', '0:0')) and not nonroot_base:
            hits.add('DOCKER-ROOT', rel, final_line, f'final stage FROM {final_image}, '
                                                     f'USER {users[-1] if users else "not set"}')


def _compose_files(repo: Repo) -> list[str]:
    return [f for f in repo.files if re.search(r'(^|/)(docker-)?compose[\w.-]*\.ya?ml$', f)]


def compose(repo: Repo, hits: Hits):
    for rel in _compose_files(repo):
        src = repo.source(rel)
        for i, line in enumerate(src.lines, 1):
            s = line.split('#')[0]
            if re.search(r'\bprivileged:\s*true|network_mode:\s*["\']?host|/var/run/docker\.sock|\bpid:\s*["\']?host|'
                         r'cap_add:.*\b(ALL|SYS_ADMIN)\b', s):
                hits.add('COMPOSE-RISK', rel, i, s.strip())
            m = re.match(r'\s*-?\s*["\']?([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY|ACCESS_KEY|PRIVATE_KEY)[A-Z0-9_]*)'
                         r'["\']?\s*[:=]\s*["\']?([^"\'\s]+)', s)
            if m and not m.group(2).startswith('$') and not m.group(2).endswith(('_FILE', '.txt')):
                hits.add('COMPOSE-SECRET', rel, i, f'{m.group(1)}: {redact(m.group(2))}',
                         severity='medium' if re.search(r'(?i)prod|live|stage', rel) else None)


def kubernetes(repo: Repo, hits: Hits):
    for rel in repo.by_ext('.yml', '.yaml'):
        text = repo.source(rel).text
        if 'apiVersion:' not in text or 'kind:' not in text:
            continue
        offset = 0
        for doc in re.split(r'(?m)^---\s*$', text):
            kind = re.search(r'(?m)^kind:\s*(\w+)', doc)
            start_line = text.count('\n', 0, text.find(doc, offset)) + 1 if doc else 1
            offset += len(doc)
            if not kind:
                continue
            k = kind.group(1)
            if k == 'Secret' and re.search(r'(?m)^(data|stringData):\s*\n\s+\w', doc):
                hits.add('K8S-SECRET', rel, start_line, f'kind: Secret {re.search(r"name:\s*(\S+)", doc).group(1) if re.search(r"name:\s*(\S+)", doc) else ""}')
            if k in WORKLOADS:
                for m in re.finditer(r'(privileged:\s*true|allowPrivilegeEscalation:\s*true|host(Network|PID|IPC):\s*true|'
                                     r'runAsUser:\s*0\b)', doc):
                    hits.add('K8S-RISK', rel, start_line + doc.count('\n', 0, m.start()), m.group(0))
                if 'runAsNonRoot: true' not in doc:
                    hits.add('K8S-NO-NONROOT', rel, start_line, f'kind: {k}')


def ci(repo: Repo, hits: Hits):
    workflows = [f for f in repo.files if re.search(r'(^|/)\.github/workflows/[^/]+\.ya?ml$', f)]
    for rel in workflows:
        base = next((n for n in repo.nested if rel.startswith(n + '/')), None)
        remote = repo._git('remote', 'get-url', 'origin', cwd=repo.root / base if base else None).strip() \
            if repo.git or base else ''
        owner = re.search(r'github\.com[:/]([\w.-]+)/', remote)
        owner = owner.group(1).lower() if owner else None
        src = repo.source(rel)
        text = src.text
        if re.search(r'shai-hulud|SHA1HULUD', text, re.I) or 'shai-hulud' in rel.lower():
            hits.add('CI-WORM-IOC', rel, None, 'workflow references Shai-Hulud')
        unpinned = []
        for i, line in enumerate(src.lines, 1):
            m = re.match(r'\s*-?\s*uses:\s*["\']?([^@\s"\']+)@([^\s"\'#]+)', line)
            if m and not m.group(1).startswith(('./', 'docker://')) and not re.fullmatch(r'[0-9a-f]{40}', m.group(2)):
                unpinned.append((i, f'{m.group(1)}@{m.group(2)}', m.group(1).startswith(('actions/', 'github/'))))
        own = [u for u in unpinned if not u[2] and owner and u[1].lower().startswith(owner + '/')]
        third = [u for u in unpinned if not u[2] and u not in own]
        if third:
            hits.add('CI-UNPINNED-ACTION', rel, third[0][0], ', '.join(u[1] for u in third[:8]))
        if own:
            hits.add('CI-UNPINNED-ACTION', rel, own[0][0], ', '.join(u[1] for u in own[:8]), severity='low',
                     note=f'same organisation ({owner}) - pinned to a branch, not a SHA')
        first_party = [u for u in unpinned if u[2]]
        if first_party:
            hits.add('CI-UNPINNED-ACTION', rel, first_party[0][0], ', '.join(u[1] for u in first_party)[:160],
                     severity='low', note='first-party actions')
        if re.search(r'(?m)^\s*pull_request_target\s*:|on:\s*\[?[^\n]*pull_request_target', text):
            head = re.search(r'ref:\s*\$\{\{\s*github\.(event\.pull_request\.head\.(sha|ref)|head_ref)', text)
            hits.add('CI-PR-TARGET', rel, src.line_at(head.start()) if head else None,
                     'pull_request_target + checkout of the PR head' if head else 'pull_request_target trigger',
                     severity=None if head else 'medium')
        in_run, run_indent = False, 0
        for i, line in enumerate(src.lines, 1):
            m = re.match(r'(\s*)(?:-\s*)?run:\s*(.*)$', line)
            indent = len(line) - len(line.lstrip())
            if m:
                in_run, run_indent = m.group(2).strip() in ('|', '>', '|-', '>-', ''), len(m.group(1))
                body = m.group(2)
            elif in_run and (indent > run_indent or not line.strip()):
                body = line
            else:
                in_run = False
                continue
            for inj in re.finditer(r'\$\{\{\s*(github\.event\.[^}]+|github\.head_ref)\s*\}\}', body):
                if not SAFE_EVENT_FIELD.search(inj.group(0)):
                    hits.add('CI-SCRIPT-INJECTION', rel, i, body.strip())
            if re.search(r'\bnpm\s+(install|i)\b(?!\s+-g)', body):
                hits.add('NPM-INSTALL', rel, i, body.strip())
            if re.search(r'echo\s+[^\n]*\$\{\{\s*secrets\.', body):
                hits.add('SH-INSECURE', rel, i, body.strip(), note='secret echoed into the log')
        if not re.search(r'(?m)^permissions\s*:', text):
            hits.add('CI-PERMISSIONS', rel, None, 'no top-level permissions block')
        elif re.search(r'(?m)^permissions\s*:\s*write-all', text):
            hits.add('CI-PERMISSIONS', rel, None, 'permissions: write-all', severity='medium')


def npm(repo: Repo, hits: Hits, stacks: dict):
    packages = [f for f in repo.files if os.path.basename(f) == 'package.json']
    roots = set()
    for rel in packages:
        try:
            pkg = json.loads(repo.source(rel).text or '{}')
        except ValueError:
            continue
        base = repo.root / os.path.dirname(rel)
        lock_dir = next((d for d in [base, *base.parents] if any((d / n).is_file() for n in (
            'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lockb', 'bun.lock', 'npm-shrinkwrap.json'))),
                        None)
        deps = {**(pkg.get('dependencies') or {}), **(pkg.get('devDependencies') or {})}
        if not deps:
            continue
        if lock_dir is None or repo.root not in [lock_dir, *lock_dir.parents]:
            hits.add('NPM-NO-LOCKFILE', rel, None, f'{len(deps)} dependencies, no lockfile')
        else:
            roots.add(lock_dir)
        loose = [f'{n}@{v}' for n, v in deps.items() if isinstance(v, str) and (
            v.strip() in ('*', 'latest', 'x', '') or re.match(r'(git\+|git:|github:|https?://|>=\s*\d)', v.strip()))]
        if loose:
            hits.add('NPM-LOOSE-VERSION', rel, None, ', '.join(loose[:10]))
    if not packages:
        return
    guards = False
    for rel in repo.files:
        name = os.path.basename(rel)
        if name == '.npmrc':
            text = repo.source(rel).text
            for i, line in enumerate(text.split('\n'), 1):
                m = re.search(r'_authToken\s*=\s*(\S+)', line)
                if m and not m.group(1).startswith('${'):
                    hits.add('NPM-TOKEN', rel, i, f'_authToken={redact(m.group(1))}')
            guards |= bool(re.search(r'(?m)^\s*(ignore-scripts\s*=\s*true|min-release-age\s*=)', text))
        if name == 'pnpm-workspace.yaml':
            guards |= bool(re.search(r'minimumReleaseAge|onlyBuiltDependencies|allowBuilds|strictDepBuilds',
                                     repo.source(rel).text))
        if name in ('bunfig.toml', '.yarnrc.yml'):
            guards |= bool(re.search(r'minimumReleaseAge|npmMinimalAgeGate|enableScripts:\s*false',
                                     repo.source(rel).text))
    if not guards and roots:
        hits.add('NPM-NO-SCRIPT-GUARD', next(iter(sorted(packages))), None,
                 'no ignore-scripts, min-release-age or pnpm minimumReleaseAge in the repo')
    for root in roots:
        nm = root / 'node_modules'
        if not nm.is_dir():
            continue
        try:
            entries = [nm / e for e in os.listdir(nm)]
            entries = [s for e in entries for s in ([e / x for x in os.listdir(e)] if e.name.startswith('@') and e.is_dir()
                                                    else [e])]
        except OSError:
            continue
        for pkg in entries:
            for ioc in ('setup_bun.js', 'bun_environment.js'):
                if (pkg / ioc).is_file():
                    hits.add('CI-WORM-IOC', os.path.relpath(pkg / ioc, repo.root), None,
                             f'{pkg.name} ships {ioc} (Shai-Hulud 2.0)')


def web_servers(repo: Repo, hits: Hits):
    wanted = {'Content-Security-Policy': r'Content-Security-Policy',
              'Strict-Transport-Security': r'Strict-Transport-Security',
              'X-Content-Type-Options': r'X-Content-Type-Options',
              'frame protection': r'X-Frame-Options|frame-ancestors',
              'Referrer-Policy': r'Referrer-Policy'}
    for rel in repo.files:
        if not (rel.endswith('.conf') or os.path.basename(rel) in ('nginx.conf', 'default.conf', 'Caddyfile')):
            continue
        text = repo.source(rel).text
        if not re.search(r'\bserver\s*\{|\blocation\s+[^{]+\{', text):
            continue
        missing = [k for k, rx in wanted.items() if not re.search(rx, text, re.I)]
        tokens = re.search(r'server_tokens\s+off', text)
        if missing or not tokens:
            hits.add('WEB-HEADERS', rel, None, ('missing: ' + ', '.join(missing) if missing else 'headers present')
                     + ('' if tokens else '; server_tokens not off'),
                     severity='medium' if missing else 'low')
        for m in re.finditer(r'autoindex\s+on', text):
            hits.add('WEB-HEADERS', rel, text.count('\n', 0, m.start()) + 1, 'autoindex on', severity='medium')


# defined by proxies, browsers, platforms and frameworks - the app cannot rename them
FOREIGN_X_HEADER = re.compile(
    r'(?i)^x-(forwarded-[\w-]+|real-ip|requested-with|frame-options|content-type-options|xss-protection|robots-tag|'
    r'request-id|correlation-id|csrf-token|xsrf-token|dns-prefetch-control|permitted-cross-domain-policies|'
    r'download-options|powered-by|ua-compatible|http-method-override|original-[\w-]+|accel-[\w-]+|sendfile|cache|'
    r'content-security-policy|webkit-csp|amzn?-[\w-]+|goog-[\w-]+|ms-[\w-]+|azure-[\w-]+|hub-signature(-256)?|'
    r'github-[\w-]+|gitlab-[\w-]+|slack-[\w-]+|shopify-[\w-]+|paypal-[\w-]+|twilio-[\w-]+|cloud-trace-context|'
    r'b3-[\w-]+|envoy-[\w-]+|kong-[\w-]+|datadog-[\w-]+|vercel-[\w-]+|nf-[\w-]+|auth-request-[\w-]+)$')
QUOTED_X_HEADER = re.compile(r'["\'`]([Xx]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)["\'`]')


def custom_headers(repo: Repo, hits: Hits):
    found = {}
    for rel in repo.files:
        if is_test_path(rel) or not rel.endswith(('.kt', '.java', '.ts', '.js', '.mjs', '.yml', '.yaml',
                                                   '.properties', '.conf')):
            continue
        src = repo.source(rel)
        for i, line in enumerate(src.code_lines, 1):
            if rel.endswith('.conf'):
                names = re.findall(r'\b(?:add_header|proxy_set_header|more_set_headers|proxy_hide_header)\s+["\']?'
                                   r'([Xx]-[\w-]+)', line)
            elif rel.endswith(('.yml', '.yaml', '.properties')):
                names = re.findall(r'(?<![\w-])([Xx]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)', line) \
                    if re.search(r'(?i)header', line) else []
            else:
                names = [n for n in QUOTED_X_HEADER.findall(line)
                         if re.search(r'(?i)header', line) or re.fullmatch(r'X-[A-Z][a-z0-9]*(?:-[A-Z0-9][A-Za-z0-9]*)+', n)]
            for name in names:
                if not FOREIGN_X_HEADER.match(name):
                    found.setdefault(name.lower(), (name, []))[1].append((rel, i))
    for name, places in sorted(found.values()):
        rel, line = places[0]
        hits.add('HTTP-X-PREFIX', rel, line, f'{name} - {len(places)} place(s)',
                 files=sorted({r for r, _ in places})[:20])


XSS_AUDITOR_ON = re.compile(r'(?i)x-?xss-?protection["\'\s:=,]*1\b|HeaderValue\s*\.\s*ENABLED(?:_MODE_BLOCK)?\b|'
                            r'xssProtection\s*(?:\(\s*\)\s*\.\s*block\s*\(\s*true|\{[^}]*\bblock\s*=\s*true)|'
                            r'xssProtectionEnabled\s*\(\s*true')


def xss_auditor(repo: Repo, hits: Hits):
    for rel in repo.files:
        if is_test_path(rel):
            continue
        src = repo.source(rel)
        for m in XSS_AUDITOR_ON.finditer(src.code):
            line = src.line_at(m.start())
            hits.add('HTTP-XSS-PROTECTION', rel, line, src.line(line).strip())


def shell(repo: Repo, hits: Hits):
    patterns = [
        (r'\bcurl\b[^\n|]*\s(-k|--insecure)\b', 'curl without TLS verification'),
        (r'\bwget\b[^\n|]*--no-check-certificate', 'wget without TLS verification'),
        (r'\bsshpass\s+-p\s*\S', 'password on the sshpass command line'),
        (r'docker\s+login\b[^\n]*\s(-p|--password)\s+(?!\$)\S', 'docker login with a literal password'),
        (r'\bchmod\s+(-R\s+)?(0?777|a\+rwx)\b', 'world-writable permissions'),
        (r'StrictHostKeyChecking\s*=?\s*no', 'SSH host key checking off'),
        (r'(curl|wget)\s[^|\n]*\|\s*(sudo\s+)?(ba|z)?sh\b', 'remote script piped into a shell'),
    ]
    for rel in repo.files:
        if not (rel.endswith(('.sh', '.bash', '.zsh')) or os.path.basename(rel) in ('Jenkinsfile', 'Makefile')):
            continue
        src = repo.source(rel)
        for i, line in enumerate(src.lines, 1):
            if line.lstrip().startswith('#'):
                continue
            for rx, label in patterns:
                if re.search(rx, line):
                    hits.add('SH-INSECURE', rel, i, line.strip(), note=label)
            if re.search(r'\bnpm\s+(install|i)\b(?!\s+(-g|--global))', line) and not is_test_path(rel):
                hits.add('NPM-INSTALL', rel, i, line.strip())


SECRET_LEAF = re.compile(r'(^|_)(password|passwd|pwd|pass|secret|token|api_?key|apikey|private_?key|access_?key|'
                         r'secret_?key|signing_?key|encryption_?key|master_?key|client_?secret|credentials?|'
                         r'auth_?token|access_?token|refresh_?token|webhook_?secret)$')
LOOSE_LEAF = re.compile(r'password|passwd|pwd|secret|token|api_?key|private|access_?key|credential|auth|bearer|'
                        r'cookie|session|signature|salt|dsn|connection_?string|license|(^|_)(pass|key)$')
KV_START = re.compile(r'^[ \t]*(?:-[ \t]+)?(?:export[ \t]+)?(["\']?)([\w.\-\[\]/@]+)\1[ \t]*[:=][ \t]*')
JSON_PAIR = re.compile(r'"([\w.\-@/]+)"\s*:\s*"((?:\\.|[^"\\\n])*)"')
XML_PAIR = re.compile(r'<([\w.\-:]+)>([^<\n]+)</\1>')
NO_VALUE = re.compile(r'(?i)^(true|false|null|none|nil|~|yes|no|on|off|[|>][+-]?|\[\]|\{\}|""|\'\')$')
WEAK_VALUE = re.compile(r'(?i)^(changeme|change-me|password\d*|secret\d*|admin\d*|root|postgres|sa|test\w*|user|guest|'
                        r'demo|default|dev|develop|local|localhost|12345\d*)$')
PLAIN_URL = re.compile(r'(?i)[a-z][\w+.:-]*://[^\s@?]+(\?(?!.*\b(token|key|secret|sig|signature|password|code)=)\S*)?')
JUNK = re.compile(r'(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$|(~|\.swp)$')


def _leaf(key: str) -> str:
    leaf = ([p for p in re.split(r'[.\[\]/]', key) if p] or [''])[-1]
    return re.sub(r'-', '_', re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', leaf)).lower()


def _value_span(line: str, pos: int) -> tuple[int, int] | None:
    rest = line[pos:]
    if rest[:1] in ('"', "'", '`'):
        end = rest.find(rest[0], 1)
        if end < 0:
            return (pos + 1, len(line.rstrip())) if rest[1:].strip() else None
        return (pos + 1, pos + end) if end > 1 else None
    value = re.split(r'\s+#', rest, maxsplit=1)[0].rstrip().rstrip(',;').rstrip()
    return (pos, pos + len(value)) if value else None


def _real_secret(value: str) -> bool:
    v = value.strip()
    return bool(v) and not (NO_VALUE.match(v) or PLACEHOLDER.search(v) or WEAK_VALUE.match(v) or PLAIN_URL.fullmatch(v))


def _loose_value(value: str) -> list[tuple[int, int]]:
    v = value.strip()
    if not v or NO_VALUE.match(v) or PLAIN_URL.fullmatch(v):
        return []
    if '${' in value:
        return [m.span(2) for m in re.finditer(r'\$\{[^:}?]+(:\?|\?|:-|:)([^}]+)\}', value) if '?' not in m.group(1)]
    return [(0, len(value))]


def _random_looking(token: str) -> bool:
    if not (re.search(r'\d', token) and re.search(r'[A-Za-z]', token)):
        return False
    return bool(re.fullmatch(r'[0-9a-fA-F-]{32,}', token)) or \
        entropy(token) >= min(4.3, math.log2(len(token)) - 0.7)


def secret_spans(text: str, loose: bool = False) -> list[tuple[int, int, str]]:
    """(start, end, key or token kind) of every secret-like value; loose also takes anything that might be one."""
    spans, offset, block = [], 0, None
    for line in text.split('\n'):
        indent = len(line) - len(line.lstrip())
        if block is not None and (not line.strip() or indent > block):
            if line.strip():
                spans.append((offset + indent, offset + len(line.rstrip()), 'block'))
            offset += len(line) + 1
            continue
        block = None
        pairs = []
        m = KV_START.match(line)
        span = _value_span(line, m.end()) if m else None
        if span:
            pairs.append((m.group(2), *span))
        pairs += [(p.group(1), *p.span(2)) for rx in (JSON_PAIR, XML_PAIR, LITERAL)[:3 if loose else 2]
                  for p in rx.finditer(line)]
        for key, start, end in pairs:
            leaf, value = _leaf(key), line[start:end]
            if loose and LOOSE_LEAF.search(leaf):
                if re.fullmatch(r'[|>][+-]?', value.strip()):
                    block = indent
                else:
                    spans += [(offset + start + a, offset + start + b, key) for a, b in _loose_value(value)]
            elif SECRET_LEAF.search(leaf) and _real_secret(value):
                spans.append((offset + start, offset + end, key))
        offset += len(line) + 1
    for label, rx in TOKEN_RX:
        for m in rx.finditer(text):
            if label == 'Private key':
                spans.append((m.start(), PEM_BLOCK.match(text, m.start()).end(), label))
            elif label == 'Credentials in URL':
                if loose or not (PLACEHOLDER.search(m.group(0)) or re.search(r'://[^:]+:\$', m.group(0))):
                    p = re.search(r'://[^:]+:([^@]+)@', m.group(0))
                    spans.append((m.start() + p.start(1), m.start() + p.end(1), label))
            else:
                spans.append((*m.span(), label))
    if loose:
        spans += [(*m.span(), 'random') for m in re.finditer(r'[A-Za-z0-9+/_\-.=~]{20,}', text)
                  if _random_looking(m.group())]
    return sorted(set(spans))


def _secrets_in(name: str, text: str) -> tuple[list[str], str | None, int | None, list[str]]:
    """Secret-like keys, the first raw value and its line, and the keys of a Spring config file."""
    lines = {e.line: e.key for e in config_entries(SimpleNamespace(path=Path(name), lines=text.split('\n')))} \
        if name.endswith(('.yml', '.yaml', '.properties')) else {}
    found = [(text.count('\n', 0, s) + 1, label, text[s:e]) for s, e, label in secret_spans(text)]
    keys = list(dict.fromkeys(lines.get(n, label) for n, label, _ in found))
    return keys, found[0][2] if found else None, found[0][0] if found else None, list(dict.fromkeys(lines.values()))


def _keys_text(keys: list[str], secret: bool, limit: int = 4) -> str:
    if not keys:
        return 'no secret-like value' if not secret else 'secret-like content'
    return ('secret-like ' if secret else 'keys ') + ', '.join(keys[:limit]) + \
        (f' +{len(keys) - limit}' if len(keys) > limit else '')


def _excluded_by_build(repo: Repo, module: str, resource: str) -> bool:
    texts = [read_text(repo.root / d / b) for d in {module, *map(str, Path(module).parents)}
             for b in ('build.gradle.kts', 'build.gradle', 'pom.xml')]
    patterns = [p.removeprefix('**/') for t in texts for p in re.findall(r'exclude\s*\(?\s*["\']([^"\']+)["\']', t)
                + re.findall(r'<exclude>\s*([^<\s]+)\s*</exclude>', t)]
    return any(fnmatch.fnmatch(resource, p) or fnmatch.fnmatch(os.path.basename(resource), p) for p in patterns)


def untracked_resources(repo: Repo, hits: Hits):
    for entry in repo.ignored_entries:
        if not re.search(r'(^|/)src/main/resources/', entry):
            continue
        files = [entry] if not entry.endswith('/') else sorted(
            os.path.relpath(os.path.join(d, f), repo.root) for d, _, names in os.walk(repo.root / entry) for f in names)
        found = 0
        for rel in files:
            module, resource = re.split(r'(?:^|/)src/main/resources/', rel, maxsplit=1)
            if JUNK.search(rel) or _excluded_by_build(repo, module, resource):
                continue
            name, text = os.path.basename(rel), read_text(repo.root / rel)
            suffix = os.path.splitext(name)[1].lower()
            if suffix in SECRET_FILE_EXT and (suffix != '.pem' or 'PRIVATE KEY' in text):
                hits.add('SB-RESOURCE-UNTRACKED', rel, None, 'git-ignored key or keystore file, packaged by the build',
                         ignored=True)
                found += 1
                continue
            keys, raw, line, config = _secrets_in(name, text)
            if raw or not entry.endswith('/'):
                hits.add('SB-RESOURCE-UNTRACKED', rel, line, 'git-ignored, packaged by the build - '
                         + _keys_text(keys or config, bool(raw)), severity=None if raw else 'medium', ignored=True,
                         **(secret_fields(raw) if raw else {}))
                found += 1
        if entry.endswith('/') and files and not found:
            hits.add('SB-RESOURCE-UNTRACKED', entry, None, f'git-ignored directory with {len(files)} file(s), '
                     'packaged by the build - no secret-like value', severity='low', ignored=True)


def artifacts(repo: Repo, hits: Hits):
    if repo.tracked is None:
        return
    modules = sorted({os.path.dirname(f) for f in repo.files
                      if os.path.basename(f) in ('build.gradle.kts', 'build.gradle', 'pom.xml')})
    for module in modules:
        base = '' if repo.git else next((n + '/' for n in repo.nested if (module + '/').startswith(n + '/')), None)
        if base is None:
            continue
        # the boot jar of a multi-module build sits in another module than its resources
        in_git = {os.path.basename(f) for f in repo.tracked if f.startswith(base) and '/src/main/resources/' in '/' + f}
        for jar in sorted(p for g in ('build/libs/*.jar', 'build/libs/*.war', 'target/*.jar', 'target/*.war')
                          for p in (repo.root / module).glob(g)):
            try:
                with zipfile.ZipFile(jar) as z:
                    texts = {i.filename: z.read(i).decode('utf-8', 'replace') for i in z.infolist() if re.fullmatch(
                        r'(?:BOOT-INF|WEB-INF)/classes/(application[\w.-]*\.(?:ya?ml|properties))', i.filename)
                             and os.path.basename(i.filename) not in in_git}
            except (OSError, zipfile.BadZipFile):
                continue
            built = dt.date.fromtimestamp(jar.stat().st_mtime)
            for entry, text in texts.items():
                keys, raw, _, config = _secrets_in(entry, text)
                extra = secret_fields(raw) if raw else {}
                extra['note'] = '; '.join(filter(None, (f'artifact built {built}', extra.get('note'))))
                hits.add('SB-ARTIFACT-CONFIG', os.path.relpath(jar, repo.root), None,
                         f'{entry} is not in git - ' + _keys_text(keys or config, bool(raw)),
                         severity=None if raw else 'medium',
                         **({'ignored': True} if repo.ignored(os.path.relpath(jar, repo.root)) else {}), **extra)


def mask_secrets(text: str) -> str:
    spans = secret_spans(text, loose=True)
    # a password that doubles as user or database name would show up there
    for value in {text[s:e].strip() for s, e, _ in spans if '\n' not in text[s:e] and len(text[s:e].strip()) >= 6}:
        spans += [(*m.span(), 'again')
                  for m in re.finditer(rf'(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])', text)]
    merged = []
    for start, end, _ in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    out, pos = [], 0
    for start, end in merged:
        value = text[start:end]
        out += [text[pos:start], redact(value), '\n***' * value.count('\n')]
        pos = end
    return ''.join(out + [text[pos:]])


def cat(root: Path, rel: str, start: int | None = None, end: int | None = None) -> str:
    """The file with line numbers and every secret-like value masked. `jar!entry` reads from inside an archive."""
    target, _, entry = rel.partition('!')
    if entry and (root / rel).is_file():
        target, entry = rel, ''
    path = Path(target) if os.path.isabs(target) else root / target
    try:
        if entry:
            with zipfile.ZipFile(path) as z:
                data = z.read(entry)
        else:
            data = path.read_bytes()
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        return f'cannot read {rel}: {exc}'
    if b'\0' in data[:4096]:
        return f'{rel}: binary file, {len(data)} bytes - not printed'
    lines = mask_secrets(data.decode('utf-8', 'replace').replace('\r\n', '\n')).split('\n')
    first, last = max(start or 1, 1), min(end or len(lines), len(lines))
    return '\n'.join(f'{i:>5}  {lines[i - 1]}' for i in range(first, last + 1)) or f'{rel}: {len(lines)} lines'
