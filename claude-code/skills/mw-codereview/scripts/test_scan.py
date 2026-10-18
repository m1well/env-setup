"""Scans fixtures/privacy-headers and compares the hits of the checks the fixture was built for.

    python3 scripts/test_scan.py
"""
import json
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


class PrivacyAndHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([sys.executable, str(HERE / 'scan.py'), str(HERE / 'fixtures' / 'privacy-headers'),
                            '--no-tools', '--baseline', 'none', '--out', out], check=True, capture_output=True)
            cls.result = json.loads((Path(out) / 'scan.json').read_text(encoding='utf-8'))

    def test_hit_counts(self):
        counts = Counter(h['check'] for h in self.result['hits']
                         if h['check'].startswith(('PII-', 'HTTP-')) or h['check'] == 'SB-HEADER-TRUST')
        self.assertEqual(EXPECTED, dict(counts))

    def test_protection_need(self):
        privacy = self.result['inventory']['privacy']
        self.assertEqual('very high', privacy['need'])
        self.assertEqual('patient.diagnose: health', privacy['decided_by'])


if __name__ == '__main__':
    unittest.main()
