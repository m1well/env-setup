"""Scans the fixtures and compares the hits of the checks each fixture was built for.

    python3 scripts/test_scan.py
"""
import functools
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = {
    'HTTP-X-PREFIX': 4, 'HTTP-XSS-PROTECTION': 3, 'SB-HEADER-TRUST': 3,
    'PII-COLLECTED-UNUSED': 1, 'PII-CONSENT-PROOF': 1, 'PII-FREE-TEXT': 1, 'PII-FRONTEND-STORAGE': 1,
    'PII-IN-URL': 1, 'PII-LOG': 1, 'PII-NO-ERASURE': 1, 'PII-NO-RETENTION': 1, 'PII-PLAINTEXT': 1,
    'PII-RESPONSE': 1, 'PII-SEED-DATA': 1, 'PII-SPECIAL-CATEGORY': 1, 'PII-THIRD-PARTY': 5, 'PII-TOSTRING': 1,
    'PII-TRACKING-CONSENT': 1,
}
EXPECTED_AUTHZ = {
    'SB-POSTAUTHORIZE-WRITE': 1, 'SB-POSTFILTER': 1, 'SB-PREAUTH-COMPLEX': 1, 'SB-AUTHZ-FAIL-OPEN': 2,
    'SB-ISSUER-FROM-TOKEN': 2, 'SB-TOKEN-RELAY': 1, 'SB-TENANT-THREADLOCAL': 2, 'SB-TENANT-CONTEXT-LOST': 3,
    'SB-CACHE-NO-TENANT': 1, 'SB-TENANT-FILTER-BYID': 1, 'SB-TENANT-NATIVE-SQL': 1, 'SB-RLS-SESSION-SET': 2,
    'DB-RLS-NO-FORCE': 1, 'DB-TENANT-NO-RLS': 1, 'DB-TENANT-CONSTRAINT': 2, 'TESTGAP-TENANT': 1,
    'KC-USER-ATTR-EDITABLE': 2, 'KC-ORG-FIRST': 1,
}

EXPECTED_BY_FIXTURE = {
    'correctness': {'SB-DST-DURATION': 4, 'SEED-INSERT-ONLY': 4, 'SB-LIMIT-UNUSED': 3, 'DB-NATIVE-COUNTER-OVERWRITE': 3},
    'authz-interceptors': {'DB-FK-NO-INDEX': 1, 'DB-NO-UNIQUE-KEY': 1, 'TESTGAP-LOGIC': 1},
    'privacy-retention': {
        'PII-FREE-TEXT': 1, 'PII-LOG': 1, 'PII-NO-ERASURE': 1, 'PII-NO-RETENTION': 2, 'PII-PLAINTEXT': 1,
        'PII-THIRD-PARTY': 3, 'SB-TOKEN-IN-LOG': 1, 'TOKEN-NO-EXPIRY': 1,
    },
    'frontend-checks': {
        'DEPS-BUILD-IN-PROD': 1, 'DEPS-UNUSED': 1, 'KC-JS-EXPIRED-THROWS': 1, 'NG-COMPONENT-HTTP': 2,
        'NG-IFRAME-WRITE': 2, 'NG-INTERCEPTOR-BYPASS': 2, 'NG-NO-GUARDS': 1, 'NG-ROUTE-UNGUARDED': 1,
        'NG-TOKEN-HOST-PREFIX': 2, 'NG-TOKEN-IN-PATH': 1, 'TESTGAP-E2E-ROUTE': 2, 'UX-DELETE-NO-CONFIRM': 2,
    },
    'spring-checks': {
        'SB-SEC-CSRF-OFF': 2, 'SB-AUTH-FILTER-SWALLOW': 1, 'SB-HEADER-RELAY': 1, 'ARCH-CALL-PER-REQUEST': 1,
        'AUTH-NO-RATELIMIT': 1, 'SB-GET-SIDE-EFFECT': 1, 'SB-OPEN-REDIRECT': 2, 'SB-SSRF-INPUT': 1,
        'SB-HOST-HEADER-LINK': 1, 'PUBLIC-MAIL-TO-INPUT': 1, 'SB-TX-REMOTE-CALL': 2, 'SB-CFG-SECRET': 1,
    },
}


def run(*args: str) -> str:
    return subprocess.run([sys.executable, str(HERE / 'scan.py'), *args], check=True, capture_output=True,
                          text=True).stdout


@functools.cache
def scan(fixture: str) -> dict:
    with tempfile.TemporaryDirectory() as out:
        run(str(HERE / 'fixtures' / fixture), '--no-tools', '--baseline', 'none', '--out', out)
        return json.loads((Path(out) / 'scan.json').read_text(encoding='utf-8'))


def hits(fixture: str, check: str) -> list[dict]:
    return [h for h in scan(fixture)['hits'] if h['check'] == check]


class PrivacyAndHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = scan('privacy-headers')

    def test_hit_counts(self):
        counts = Counter(h['check'] for h in self.result['hits']
                         if h['check'].startswith(('PII-', 'HTTP-')) or h['check'] == 'SB-HEADER-TRUST')
        self.assertEqual(EXPECTED, dict(counts))

    def test_protection_need(self):
        privacy = self.result['inventory']['privacy']
        self.assertEqual('very high', privacy['need'])
        self.assertEqual('patient.diagnose: health', privacy['decided_by'])


class AuthorizationAndTenancy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = scan('authz-tenancy')

    def test_hit_counts(self):
        counts = Counter(h['check'] for h in self.result['hits'] if h['check'] in EXPECTED_AUTHZ)
        self.assertEqual(EXPECTED_AUTHZ, dict(counts))

    def test_inventory(self):
        tenancy = self.result['inventory']['authz']['tenancy']
        self.assertTrue(tenancy['tenant_app'])
        self.assertEqual(4, tenancy['tenant_tables'])
        self.assertIn('RLS on 2 of 4 tenant tables (1 forced)', tenancy['isolation'])
        self.assertIn('claim tenant_id', tenancy['model'])


class Fixtures(unittest.TestCase):
    def test_hit_counts(self):
        for fixture, expected in EXPECTED_BY_FIXTURE.items():
            with self.subTest(fixture):
                counts = Counter(h['check'] for h in scan(fixture)['hits'] if h['check'] in expected)
                self.assertEqual(expected, dict(counts))

    def test_interceptors_and_tenancy(self):
        az = scan('authz-interceptors')['inventory']['authz']
        self.assertFalse(az['tenancy']['tenant_app'])
        self.assertEqual([('ProjectMemberInterceptor', 2), ('ReportAccessInterceptor', 1)],
                         sorted((i['class'], i['endpoints']) for i in az['interceptors']))
        self.assertEqual([('GET', '/api/projects/{projectId}/public'), ('GET', '/api/reports/{reportId}/export'),
                          ('GET', '/api/support/projects/{projectId}'), ('POST', '/api/documents/{id}/archive'),
                          ('PUT', '/api/documents/{id}')], sorted((e['http'], e['path']) for e in az['object_access']))

    def test_privacy_profile(self):
        pv = scan('privacy-retention')['inventory']['privacy']
        self.assertEqual('high (needs reader)', pv['need'])
        self.assertIn('*.username', [h['table'] for h in pv['hubs']])
        self.assertNotIn('employees', pv['subjects'])
        self.assertEqual(['Bereinigung.naechtlich -> anfrage, passwort_reset'], pv['retention_jobs'])

    def test_frontend_stack_and_deps(self):
        ws = scan('frontend-checks')['stacks']['angular'][0]
        self.assertEqual((False, 'zoneless 2 of 2 apps'), (bool(ws['ssr']), ws['zone_detail']))
        self.assertEqual(['@angular/ssr', '@types/express', 'express', 'zone.js'], hits('frontend-checks', 'DEPS-UNUSED')[0]['names'])
        self.assertEqual([], hits('frontend-checks', 'NG-DOM-XSS') + hits('frontend-checks', 'NG-ZONE'))

    def test_spring_chain_and_calls(self):
        self.assertEqual({'low'}, {h['severity'] for h in hits('spring-checks', 'SB-SEC-CSRF-OFF')})
        self.assertEqual('cad9f95e4918', hits('spring-checks', 'SB-CFG-SECRET')[0]['secret'])
        calls = {c['where']: c for c in scan('spring-checks')['inventory']['spring']['calls']}
        self.assertEqual((True, 'auth.internal.test'), (calls['AuthClient.verify']['per_request'],
                                                        calls['AuthClient.verify']['host']))
        self.assertEqual(('mail', 'smtp.mail.test'), (calls['MailGateway.send']['kind'], calls['MailGateway.send']['host']))


class SecretsAndArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / 'repo'
        shutil.copytree(HERE / 'fixtures' / 'secrets-artifacts', cls.root)
        (cls.root / '_gitignore').rename(cls.root / '.gitignore')
        subprocess.run(['git', 'init', '-q'], cwd=cls.root, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=cls.root, check=True)
        out = Path(cls.tmp.name) / 'out'
        run(str(cls.root), '--no-tools', '--baseline', 'none', '--out', str(out))
        cls.result = json.loads((out / 'scan.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_hit_counts(self):
        expected = {'SB-RESOURCE-UNTRACKED': 3, 'SB-ARTIFACT-CONFIG': 2, 'REPO-SECRET-TOKEN': 3}
        self.assertEqual(expected, dict(Counter(h['check'] for h in self.result['hits'] if h['check'] in expected)))

    def test_one_value_one_cluster(self):
        high = {h['secret'] for h in self.result['hits'] if h['severity'] == 'high' and h.get('secret')}
        self.assertEqual(1, len(high))
        tokens = {h['line']: h for h in self.result['hits'] if h['check'] == 'REPO-SECRET-TOKEN'}
        self.assertEqual(tokens[2]['secret'], tokens[5]['secret'])
        self.assertNotEqual(tokens[2]['secret'], tokens[8]['secret'])
        self.assertIn('signature looks fake', tokens[8]['note'])

    def test_cat_masks_values(self):
        text = run(str(self.root), '--cat', 'src/main/resources/application-local.yaml')
        self.assertNotIn('Zq8vR2mT6wX1pL9kD4hF7jN3bC5sA0yE', text)
        self.assertIn('api-key: Zq8***(32 chars)', text)


class Baseline(unittest.TestCase):
    def test_decisions_and_findings_carry_over(self):
        fixture = str(HERE / 'fixtures' / 'spring-checks')
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            run(fixture, '--no-tools', '--baseline', 'none', '--out', first)
            run('--out', first, '--decide', 'SB-OPEN-REDIRECT', 'discarded', 'constant base')
            book = json.loads((Path(first) / 'findings.json').read_text(encoding='utf-8'))
            book['findings'] = [{'id': 'F01', 'title': 'gone', 'status': 'open', 'file': 'backend/build.gradle.kts',
                                 'line': 1, 'anchor': 'no such text anywhere'}]
            (Path(first) / 'findings.json').write_text(json.dumps(book), encoding='utf-8')
            digest = run(fixture, '--no-tools', '--baseline', str(Path(first) / 'scan.json'), '--out', second)
            result = json.loads((Path(second) / 'scan.json').read_text(encoding='utf-8'))
            self.assertIn('code unchanged', digest)
            self.assertEqual({'discarded'}, {h['decided']['verdict'] for h in result['hits']
                                            if h['check'] == 'SB-OPEN-REDIRECT'})
            self.assertEqual(['anchor gone - verify fixed'], [f['recheck'] for f in result['carried']['findings']])
            carried = json.loads((Path(second) / 'findings.json').read_text(encoding='utf-8'))
            self.assertEqual(2, len(carried['decisions']))


if __name__ == '__main__':
    unittest.main()
