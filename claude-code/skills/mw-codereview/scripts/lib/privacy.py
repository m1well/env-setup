"""Personal data: what the schema stores about whom, how much of it needs protection, and where it travels -
logs, responses, URLs, seed files, browser storage, third parties. The scanner draws the map; whether the data
fits the purpose of the app is reader work (references/privacy.md)."""
from __future__ import annotations

import re
from collections import defaultdict

from . import schema, ux
from .core import balanced, define, is_test_path, profile_kind, redact, split_top
from .extract import entity as entity_x

define('PII-SPECIAL-CATEGORY', 'Special category or criminal data stored', 'medium', 'privacy',
       'Open the column and the code that writes it. Health, religion, union membership, biometrics, sex life and '
       'criminal records need an exception from Art. 9(2) or Art. 10, a reason this app needs exactly this value, '
       'and access limited to the people who need it. A name match on a config table is a false positive.',
       gdpr='Art. 9')
define('PII-PLAINTEXT', 'Sensitive personal data stored in plain text', 'medium', 'privacy',
       'A dump, a backup or a read replica shows the value as is. Field-level encryption (an encrypting '
       'AttributeConverter, pgcrypto, Vault transit) or a reason it is not needed - a value printed on every '
       'invoice is public anyway.', security=True, owasp='A04', gdpr='Art. 32')
define('PII-LOG', 'Personal data written to the log', 'medium', 'privacy',
       'Logs live longer than the rows, go to aggregators and are read by people who never see the database. '
       'Log the id, not the email.', security=True, owasp='A09', gdpr='Art. 5(1)(f)')
define('PII-TOSTRING', 'Entity with personal data and a generated toString()', 'low', 'privacy',
       'data class, Lombok @Data/@ToString and records print every field - one log line or exception message '
       'with the entity carries the IBAN along. Override toString or exclude the fields.',
       security=True, owasp='A09', gdpr='Art. 32')
define('PII-RESPONSE', 'API response carries sensitive personal fields', 'medium', 'privacy',
       'Check whether the screen behind the endpoint shows the field. A list endpoint that ships IBAN or birth '
       'date for every row is a bulk export nobody designed.', security=True, owasp='A01', gdpr='Art. 5(1)(c)')
define('PII-IN-URL', 'Personal data in the URL', 'medium', 'privacy',
       'Path and query end up in access logs, proxy logs, browser history and the Referer header. A POST body or '
       'an opaque id instead.', security=True, gdpr='Art. 32')
define('PII-SEED-DATA', 'Real-looking personal data in seed or test files', 'medium', 'privacy',
       'An IBAN that passes the checksum or an address at a real mail provider belongs to somebody - and stays in '
       'git history. example.com and the published sample IBANs instead.', security=True, gdpr='Art. 5(1)(f)')
define('PII-FRONTEND-STORAGE', 'Personal data kept in browser storage', 'low', 'privacy',
       'localStorage survives logout and every script on the origin reads it. Check what goes in and whether '
       'logout clears it.', security=True, gdpr='Art. 32')
define('PII-NO-ERASURE', 'Personal tables without a delete or anonymisation path', 'medium', 'privacy',
       'A name match - open the service for each table. A retention duty (invoices 8 or 10 years) justifies '
       'keeping rows for that time, not forever. A soft delete flag is not erasure.', gdpr='Art. 17')
define('PII-NO-RETENTION', 'Growing personal table without a scheduled cleanup', 'low', 'privacy',
       'No @Scheduled delete reaches this table, directly or by cascade. Look for a job outside the app (pg_cron, a '
       'Kubernetes CronJob). Without one every row lives as long as the database - IP addresses and login trails '
       'included. A retention duty (invoices 10 years) sets the end date, it does not remove it.', gdpr='Art. 5(1)(e)')
define('SB-TOKEN-IN-LOG', 'Request URI with an access token written to a log or a notification', 'medium', 'logging',
       'The app has routes with a token, link, code or key in the path, and this code writes the raw request URI '
       'to the log or a chat or mail notification - whoever reads it can use the token. Log the route pattern '
       '(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE) or mask the variable.', security=True, owasp='A09')
define('TOKEN-NO-EXPIRY', 'Access token stored without an expiry', 'medium', 'authentication',
       'A link, code or token in this table opens access, and the table has neither an expiry column nor a cleanup '
       'job - a forwarded mail from last year still works. Check whether the code compares the creation time '
       'with a maximum age, and whether the token can be revoked.', security=True, owasp='A07')
define('PII-CONSENT-PROOF', 'Consent stored as a bare flag', 'medium', 'privacy',
       'The controller has to prove consent: when, with which text, how (double opt-in for email marketing). '
       'A boolean proves nothing.', gdpr='Art. 7(1)')
define('PII-FREE-TEXT', 'Free text fields on personal records', 'low', 'privacy',
       'Notes collect what nobody planned: diagnoses, family matters, opinions about the person. A hint in the '
       'form, and they belong in every access request and every deletion.', gdpr='Art. 5(1)(c)')
define('PII-COLLECTED-UNUSED', 'Personal field stored that almost no code reads', 'low', 'privacy',
       'Open the references. If they only copy the value from the form into the entity, nothing uses it - ask '
       'what it is for. Data that is not collected cannot leak.', gdpr='Art. 5(1)(c)')
define('PII-THIRD-PARTY', 'Personal data may reach a third party', 'low', 'privacy',
       'Per provider: which personal data reaches it, a processing agreement, and for a US company the Data '
       'Privacy Framework listing or standard contractual clauses. An AI API gets whatever is in the prompt.',
       gdpr='Art. 28, 44')
define('PII-TRACKING-CONSENT', 'Tracking or third-party assets load without a consent manager', 'medium', 'privacy',
       'Analytics, pixels and session replay need consent before they load (TDDDG §25). Fonts, CDNs, maps and '
       'captchas send the visitor\'s IP on page load - LG München I 3 O 17493/20 on Google Fonts. Self-host or '
       'load after consent.', gdpr='Art. 6')

TIERS = ('special', 'high', 'identifying', 'quasi', 'free_text')
WEIGHT = {'special': 20, 'high': 6, 'identifying': 2, 'quasi': 1, 'free_text': 1}
NEEDS = ('normal', 'high (needs reader)', 'high', 'very high')


def _t(*words: str) -> str:
    return r'(?:^|_)(?:' + '|'.join(words) + r')(?:_|$)'


# first match wins: an insurance number is an id, not health data
CATEGORIES = [(c, tier, re.compile(rx)) for c, tier, rx in (
    ('criminal', 'special', r'vorstraf|straftat|fuehrungszeugnis|criminal|conviction|strafregister'),
    ('gov_id', 'high', r'steueridentifikation|sozialversicherung|social_?security|ausweis|id_?card|passnummer|passport|'
                       r'reisepass|fuehrerschein|driver_?licen|versichertennummer|krankenversicherungsnummer|'
                       + _t('steuer_?id', 'tax_?id', 'ssn', 'svnr', 'rvnr', 'kvnr')),
    ('profile', 'quasi', r'krankenkasse|krankenversicherung|health_?insur'),
    ('health', 'special', r'krank|diagnos|gesundheit|health|medizin|medical|medikament|medication|allergi|behinder|'
                          r'disabilit|schwanger|pregnan|mutterschutz|blutgruppe|blood_?type|therapie|therapy|befund|'
                          r'symptom|impfung|impfstatus|vaccin|arbeitsunfaehig|pflegegrad|quarant|'
                          + _t('icd', 'reha', 'gdb', 'bmi')),
    ('religion', 'special', r'religi|konfession|kirchensteuer|glaubens'),
    ('origin', 'special', r'ethni|' + _t('rasse')),
    ('politics', 'special', r'politisch|political|parteizugehoerig|parteimitglied|gewerkschaft|trade_?union'),
    ('sex_life', 'special', r'sexual|sexuell'),
    ('biometric', 'special', r'biometr|fingerabdruck|face_?(?:id|template|embedding|vector)|gesichtsmerkmal|'
                             + _t('iris')),
    ('genetic', 'special', r'genetic|genetisch|' + _t('dna')),
    ('card', 'high', r'kreditkart|credit_?card|card_?number|kartennummer|' + _t('pan', 'cvv', 'cvc')),
    ('bank', 'high', r'iban|kontonummer|account_?number|bankverbindung|mandatsreferenz|' + _t('sepa')),
    ('credential', 'high', r'passwor|kennwort|recovery_?code|sicherheitsfrage|security_?(?:question|answer)|'
                           + _t('pin', 'otp', 'totp', 'mfa_?secret', 'otp_?secret')),
    ('location', 'high', r'latitude|longitude|geolocation|koordinat|standort|breitengrad|laengengrad|'
                         + _t('lat', 'lng', 'lon', 'geo', 'gps')),
    ('income', 'high', r'gehalt|salary|einkommen|income|verdienst|stundenlohn|bruttolohn|nettolohn|' + _t('lohn')),
    ('birth', 'identifying', r'geburt|birth|' + _t('dob')),
    ('tax_number', 'identifying', r'steuernummer|umsatzsteuer_?id|' + _t('ust_?id', 'ust_?idnr', 'vat_?id')),
    ('device', 'quasi', r'user_?agent|device_?id|geraete_?id|fingerprint|mac_?(?:adresse|address)|push_?token|'
                        r'fcm_?token|imei|' + _t('ip', 'ip_?adresse', 'ip_?address', 'ipaddress', 'remote_?addr',
                                                 'remote_?address', 'client_?ip')),
    ('contact', 'identifying', r'e_?mail|telefon|phone|mobilnummer|whatsapp|'
                               + _t('mail', 'tel', 'fax', 'mobil', 'mobile', 'handy')),
    ('address', 'identifying', r'strasse|street|hausnummer|house_?number|adresse|address|anschrift|wohnort|'
                               + _t('plz', 'postleitzahl', 'zip', 'zipcode', 'postal_?code', 'postcode')),
    ('name', 'identifying', _t('vorname', 'nachname', 'familienname', 'first_?name', 'last_?name', 'surname',
                               'given_?name', 'full_?name', 'rufname', 'display_?name')),
    ('account', 'identifying', _t('username', 'user_?name', 'benutzername', 'login', 'login_?name', 'personalnummer',
                                  'mitarbeiternummer', 'kundennummer', 'customer_?number', 'mitgliedsnummer',
                                  'member_?number', 'patientennummer', 'keycloak_?sub')),
    ('photo', 'identifying', r'foto|photo|avatar|profilbild|portrait|unterschrift|signatur|signature|selfie'),
    ('profile', 'quasi', r'geschlecht|gender|nationalit|staatsangehoerig|citizenship|familienstand|marital|'
                         r'occupation|arbeitgeber|employer|muttersprache|'
                         + _t('anrede', 'salutation', 'sex', 'alter', 'age', 'kinder', 'children', 'beruf')),
    ('activity', 'quasi', r'last_?login|last_?seen|last_?active|zuletzt_(?:angemeldet|online|gesehen|aktiv)|'
                          r'letzte_?anmeldung|letzte_?aktivitaet|tracking|'
                          + _t('gesehen_am', 'gelesen_am', 'geoeffnet_am', 'opened_at', 'read_at', 'clicked_at',
                               'geklickt_am')),
    ('free_text', 'free_text', _t('notiz', 'notizen', 'note', 'notes', 'bemerkung', 'bemerkungen', 'kommentar',
                                  'comment', 'comments', 'anmerkung', 'anmerkungen', 'freitext', 'nachricht',
                                  'message', 'wunsch', 'anliegen')),
)]
TIER = {c: tier for c, tier, _ in CATEGORIES}
# a timestamp called email_bestaetigt_am or a boolean called telefon_geprueft holds no email and no phone number
VALUE_CATS = {'contact', 'address', 'name', 'account', 'photo', 'tax_number', 'bank', 'gov_id', 'card', 'device',
              'credential', 'free_text', 'location'}
NO_VALUE_TYPE = re.compile(r'^(bool|timestamp|date|time|uuid|interval)', re.I)
NUMERIC = re.compile(r'^(int|bigint|smallint|serial|numeric|decimal|double|real|float)', re.I)
NO_NUMBER_CATS = {'contact', 'name', 'free_text', 'photo', 'device'}
# a counter, a switch or a template about the email is not the email
NOT_A_VALUE = re.compile(r'(limit|anzahl|count|max|min|pro_tag|per_day|aktiv|active|enabled|erlaubt|allowed|bestaetigt|'
                         r'verified|versendet|sent|_ids?|typ|type|status|vorlage|template|feld|field|format|sichtbar|'
                         r'visible|pflicht|required|pattern|regex|config|service|client|sender|key)$')
SETTINGS = re.compile(r'(?i)einstellung|setting|config|konfiguration|vorgabe|option|vorlage|template')
TEXT_TYPE = re.compile(r'^(text|varchar|char|character|json|clob|nvarchar)', re.I)
FREE_TEXT_TABLE = re.compile(r'notiz|kommentar|comment|nachricht|message|anmerkung|ticket|anfrage|anliegen')
HEALTH_VALUE = re.compile(r'(?i)^(krank\w*|kind_?krank\w*|sick\w*|illness|arbeitsunfaehig\w*|mutterschutz|'
                          r'schwanger\w*|pregnan\w*|maternity\w*|beschaeftigungsverbot|reha\w*|quarantaene|'
                          r'quarantine|behinder\w*|schwerbehindert\w*|disab\w*)$')
RELIGION_VALUE = re.compile(r'(?i)^(evangelisch|katholisch|roemisch_?katholisch|islamisch|muslim\w*|juedisch|'
                            r'jewish|catholic|protestant\w*|konfessionslos|orthodox\w*|buddhist\w*|hindu\w*)$')

SUBJECTS = [(s, re.compile(rx)) for s, rx in (
    ('children', r'^kind$|kinder|child|schueler|pupil|minor'),
    ('patients', r'patient|klient'),
    ('applicants', r'bewerb|applicant'),
    ('employees', r'mitarbeiter|employee|arbeitnehmer|angestellte|beschaeftigte|azubi|auszubildende|'
                  + _t('personal', 'staff', 'worker', 'fahrer', 'driver')),
    ('customers', r'kunde|customer|kaeufer|buyer|auftraggeber|' + _t('mieter')),
    ('members', _t('member', 'members', 'mitglied', 'mitglieder') + '|mitgliedschaft'),
    ('users', r'benutzer|nutzer|' + _t('users?', 'besitzer', 'owner', 'profil', 'profile')),
    ('contacts', r'kontakt|contact|interessent|abonnent|subscriber|empfaenger|recipient|ansprechpartner|teilnehmer|'
                 r'participant|besucher|visitor|melder|' + _t('lead', 'leads', 'gast', 'gaeste', 'guest')),
    ('persons', r'person|people|' + _t('privat')),
)]
BUSINESS = re.compile(r'mandant|' + _t('tenant', 'betrieb', 'firma', 'company', 'organisation', 'organization',
                                       'verein'))
# a driver, a member or a staff table alone does not make a workplace - BetrVG and payroll duties need one
EMPLOYMENT = re.compile(r'gehalt|salary|payroll|lohn(?!ung)|(?:^|_)wages?(?:_|$)|vertrag|contract|urlaub|vacation|'
                        r'krank|sick|arbeitszeit|working_?(?:time|hours)|sollstunden|wochenstunden|ueberstunden|'
                        r'overtime|personalnummer|elternzeit|parental_?leave|arbeitsunfaehig|abwesenheit|absence|'
                        r'leave_?request')
LOG_TOKEN = re.compile(r'(?:event|audit|access|activity|change|login|request|error|mail|send|sync|job|call|api|webhook|'
                       r'action)?logs?|audit\w*|protokoll\w*|journal|trail|ereignis\w*|zugriff\w*')
WEAK_LOG_TOKEN = re.compile(r'events?|histor\w*|verlauf|aktivitaet\w*|activit\w*')
ACTOR = re.compile(r'(?:^|_)by$|^(?:erstellt|angelegt|geaendert|bearbeitet|geloescht|ausgefuehrt|erfasst)_von$|'
                   r'^(?:users?|user_?name|user_?ref|benutzer|benutzer_?ref|benutzername|nutzer|wer|actor|akteur|'
                   r'principal)$')
LOG_FREE = re.compile(r'^(?:text|message|msg|nachricht|details?|beschreibung|description|inhalt|eintrag|'
                      r'aenderung(?:en)?|changes|old_values?|new_values?|alter_wert|neuer_wert)$')
GROWING = re.compile(r'requests?|anfragen?|access|zugriff\w*|tokens?|sessions?|attempts?|versuche?|visits?|aufrufe?')
CREATED = re.compile(r'^(?:created|creation|erstellt|angelegt|inserted|eingegangen|eingang|received|empfangen|logged|'
                     r'occurred|aufgetreten|timestamp|zeitstempel|zeitpunkt|zeit|ts)'
                     r'(?:_(?:at|am|on|date|datum|zeit|time|ts))?$')
TIME_TYPE = re.compile(r'^(timestamp|date|datetime|instant|bigint|offsetdatetime|localdatetime)', re.I)
TOKEN_COL = re.compile(r'(?:^|_)(?:token|secret)(?:_?(?:hash|digest))?$|^(?:token|secret)_(?:hash|digest|value)$|'
                       r'(?:magic|zugangs?|einladungs?|invite|invitation|access|login|reset|verification|verify|'
                       r'bestaetigungs?|confirmation|aktivierungs?|activation|einmal|freischalt\w*)_?'
                       r'(?:code|link|key|schluessel|hash|pin|token)(?:_?hash)?$')
TOKEN_GENERIC = re.compile(r'^(?:code|link|hash|key|schluessel|pin)(?:_?hash)?$')
ACCESS_TABLE = re.compile(r'zugang|einladung|invit|magic|einmal|access|token|link|verif|bestaetig|confirm|reset|'
                          r'aktivier|activation|freischalt|onboarding|login_?code')
TOKEN_SKIP = re.compile(r'push|fcm|apns|device|firebase|csrf|xsrf|otp|mfa|webhook|signing|stripe|paypal|client_?secret|'
                        r'api_?secret')
EXPIRY = re.compile(r'expir|valid_?(?:until|to|till)|gueltig_?bis|gilt_?bis|ablauf|verfall|ttl|lifetime|laeuft_?ab|'
                    r'max_?age')
DELETE_SQL = re.compile(r'(?i)\b(?:delete\s+(?:from\s+)?|truncate\s+(?:table\s+)?)(?:\w+\.)?"?([A-Za-z_]\w*)')
DERIVED_DELETE = re.compile(r'^(?:delete|remove)(?:All\w*|By\w+|In\w+|\w*By\w+)?$')
CLEANUP = re.compile(r'(?i)delete|remove|anonymi|purge|cleanup|bereinig|loesch|lösch|expire|ablauf|aufraeum')
OWN_PREFIX = re.compile(r'^(absender|sender|eigen|own|firma|firmen|company|betrieb|mandant)_')
SOFT_DELETE = re.compile(r'(?:^|_)(geloescht|deleted|is_deleted|archiviert|archived)(?:_am|_at)?$')
ANONYMISED = re.compile(r'anonymi|pseudonymi')
CONSENT = re.compile(r'newsletter|marketing|werbung|einwillig|consent|opt_?in|double_?opt|tracking_?(?:erlaubt|allowed)')
PROOF = re.compile(r'(?:_am|_at|_datum|_date|_zeitpunkt|_time)$|nachweis|proof|einwilligungstext|consent_?text|'
                   r'version|quelle|source')
ANON_METHOD = re.compile(r'(?i)^(anonymi|pseudonymi|erase|forget|purge|vergess|bereinig|cleanup|clean_?up)')
ENCRYPTING = re.compile(r'(?i)crypt|cipher|verschl|seal|vault|tink|aead')
CRYPT_BODY = re.compile(r'Cipher\s*\.\s*getInstance|Encryptors\s*\.|TextEncryptor|BytesEncryptor|\bAead\b|pgp_sym')
WRAPPERS = {'ResponseEntity', 'List', 'MutableList', 'Set', 'Collection', 'Iterable', 'Page', 'Slice', 'Optional',
            'Mono', 'Flux', 'Flow', 'Stream', 'Map', 'String', 'Unit', 'Void', 'Array', 'PagedModel', 'EntityModel',
            'CollectionModel', 'HttpEntity', 'Any', 'Object', 'Long', 'Int', 'Integer', 'Boolean', 'UUID'}
RESPONSE_CATS = {'credential', 'bank', 'gov_id', 'card', 'birth', 'income', 'location'}
URL_CATS = {'contact', 'name', 'bank', 'gov_id', 'card', 'birth', 'address', 'credential'}
UNUSED_CATS = {'birth', 'profile', 'income', 'location', 'gov_id', 'photo'}
LOGGER = re.compile(r'\b(?:log|logger|LOG|LOGGER|Log|kLogger|klogger)\s*\.\s*(?:trace|debug|info|warn|warning|error|'
                    r'atTrace|atDebug|atInfo|atWarn|atError)\s*([({])')
LOG_FIELD = re.compile(r'(?i)(?<![\w$])(?:\w+\s*\??\.\s*)*(e_?mail\w*|iban|telefon\w*|phone\w*|mobil\w*|handy\w*|'
                       r'geburts\w*|birth\w*|vorname|nachname|first_?name|last_?name|full_?name|strasse\w*|street\w*|'
                       r'(?:e_?mail|post|wohn|liefer|rechnungs|home|billing|shipping)_?(?:adresse|address)|anschrift|'
                       r'steuer_?id|tax_?id|ip_?adresse|ip_?address|remote_?addr\w*|'
                       r'user_?agent|diagnose\w*|krankheit\w*|sozialversicherung\w*)\b')
SUBJECT_VAR = re.compile(r'(?<![\w.$])(kunde|customer|user|benutzer|mitarbeiter|employee|patient|person|kontakt|'
                         r'contact|member|mitglied|bewerber|applicant)\b(?!\s*\??\.)')
STORAGE = re.compile(r'\b(localStorage|sessionStorage)\s*\.\s*setItem\s*\(')
STORAGE_PERSONAL = re.compile(r'(?i)user|profil|kunde|customer|e_?mail|adress|address|patient|mitarbeiter|person|'
                              r'kontakt|contact|draft|entwurf|formular|form\b')
FREEMAIL = re.compile(r'\b([\w.+-]+)@((?:gmail|googlemail|gmx|web|t-online|outlook|hotmail|live|yahoo|ymail|icloud|me|'
                      r'posteo|freenet|aol|mail|protonmail|proton|arcor|online|vodafone)\.(?:com|de|net|at|ch|me|org))\b',
                      re.I)
FAKE_LOCAL = re.compile(r'(?i)^(test|max|erika|john|jane|foo|bar|example|demo|dummy|user|info|noreply|no-reply|admin|'
                        r'mustermann|musterfrau|sample|fake)|mustermann|musterfrau|example|\btest')
IBAN = re.compile(r'\b([A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,3})?)\b')
SAMPLE_IBANS = {'DE89370400440532013000', 'DE02120300000000202051', 'DE12500105170648489890', 'DE75512108001245126199',
                'DE91100000000123456789', 'DE44500105175407324931', 'DE02500105170137075030', 'GB82WEST12345698765432',
                'AT611904300234573201', 'CH9300762011623852957', 'DE68210501700012345678', 'DE27100777770209299700',
                'DE02100500000054540402', 'DE02300209000106531065', 'DE02700100800030876808'}
IBAN_LENGTH = {'DE': 22, 'AT': 20, 'CH': 21, 'NL': 18, 'FR': 27, 'IT': 27, 'ES': 24, 'BE': 16, 'LU': 20, 'GB': 22,
               'PL': 28, 'DK': 18, 'SE': 24, 'LI': 21, 'IE': 22}

# provider, kind, seat - the seat decides whether a transfer outside the EU needs a basis
PROVIDERS = [(n, k, seat, re.compile(rx, re.I)) for n, k, seat, rx in (
    ('Stripe', 'payment', 'US', r'com\.stripe|stripe-java|@stripe/|api\.stripe\.com|js\.stripe\.com'),
    ('PayPal', 'payment', 'US', r'com\.paypal|@paypal/|paypal\.com/sdk|api(?:-m)?\.paypal\.com'),
    ('Mollie', 'payment', 'EU', r'mollie'),
    ('SendGrid', 'email', 'US', r'com\.sendgrid|sendgrid\.(?:net|com)'),
    ('Mailjet', 'email', 'EU', r'com\.mailjet|mailjet\.com'),
    ('Mailgun', 'email', 'US', r'mailgun'),
    ('Postmark', 'email', 'US', r'postmarkapp|com\.wildbit'),
    ('Brevo', 'email', 'EU', r'brevo|sendinblue'),
    ('Amazon SES', 'email', 'US', r'awssdk[:/]ses|aws-java-sdk-ses|email\.[\w-]+\.amazonaws\.com'),
    ('Google Mail', 'email', 'US', r'smtp\.gmail\.com'),
    ('Microsoft 365', 'email', 'US', r'smtp\.office365\.com|graph\.microsoft\.com'),
    ('AWS', 'cloud', 'US', r'awssdk[:/]s3|spring-cloud-aws|s3\.[\w.-]*amazonaws\.com|@aws-sdk/'),
    ('Google Cloud', 'cloud', 'US', r'com\.google\.cloud|storage\.googleapis\.com|@google-cloud/'),
    ('Azure', 'cloud', 'US', r'com\.azure|blob\.core\.windows\.net|@azure/'),
    ('Firebase', 'cloud', 'US', r'firebase-admin|@angular/fire|"firebase"|fcm\.googleapis\.com'),
    ('Twilio', 'sms', 'US', r'com\.twilio|api\.twilio\.com'),
    ('Sentry', 'monitoring', 'US', r'io\.sentry|@sentry/|sentry\.io'),
    ('Datadog', 'monitoring', 'US', r'com\.datadoghq|@datadog/|datadoghq\.(?:com|eu)'),
    ('New Relic', 'monitoring', 'US', r'newrelic'),
    ('OpenAI', 'ai', 'US', r'com\.openai|openai-java|spring-ai-openai|api\.openai\.com|"openai"'),
    ('Anthropic', 'ai', 'US', r'com\.anthropic|spring-ai-anthropic|api\.anthropic\.com|@anthropic-ai/'),
    ('Google Gemini', 'ai', 'US', r'spring-ai-vertex|google-genai|generativelanguage\.googleapis\.com|@google/genai'),
    ('Mistral', 'ai', 'EU', r'spring-ai-mistral|api\.mistral\.ai'),
    ('OpenRouter', 'ai', 'US', r'openrouter\.ai|open-?router'),
    ('Azure OpenAI', 'ai', 'US', r'openai\.azure\.com|spring-ai-azure-openai'),
    ('Groq', 'ai', 'US', r'api\.groq\.com'),
    ('DeepSeek', 'ai', 'CN', r'api\.deepseek\.com'),
    ('Hugging Face', 'ai', 'US', r'huggingface\.co'),
    ('Aleph Alpha', 'ai', 'EU', r'aleph-alpha\.com'),
    ('Google Cloud Vision / Document AI', 'ocr', 'US', r'vision\.googleapis\.com|documentai\.googleapis\.com|'
                                                         r'google-cloud-vision|google-cloud-document-ai'),
    ('AWS Textract', 'ocr', 'US', r'awssdk[:/]textract|aws-java-sdk-textract|textract\.[\w-]+\.amazonaws\.com'),
    ('Azure Document Intelligence', 'ocr', 'US', r'cognitiveservices\.azure\.com|formrecognizer|documentintelligence'),
    ('Mindee', 'ocr', 'EU', r'api\.mindee\.net|com\.mindee'),
    ('OpenHolidays API', 'holidays', 'EU', r'openholidaysapi\.org'),
    ('Nager.Date', 'holidays', 'EU', r'date\.nager\.at'),
    ('feiertage-api.de', 'holidays', 'EU', r'feiertage-api\.de'),
    ('Nominatim (OpenStreetMap)', 'maps', 'UK', r'nominatim\.openstreetmap\.org'),
    ('Adyen', 'payment', 'EU', r'adyen'),
    ('Klarna', 'payment', 'EU', r'api(?:-\w+)?\.klarna\.com|com\.klarna'),
    ('GoCardless', 'payment', 'UK', r'gocardless'),
    ('DeepL', 'translation', 'EU', r'api(?:-free)?\.deepl\.com|deepl-java'),
    ('HubSpot', 'crm', 'US', r'hubspot|api\.hubapi\.com'),
    ('Slack', 'chat', 'US', r'hooks\.slack\.com|com\.slack\.api|slack[_-]?web[_-]?hook'),
    ('Discord', 'chat', 'US', r'discord(?:app)?\.com|discord[_-]?web[_-]?hook'),
    ('Microsoft Teams', 'chat', 'US', r'webhook\.office\.com|teams[_-]?web[_-]?hook'),
    ('Telegram', 'chat', 'AE', r'api\.telegram\.org|telegram_?bot'),
    ('Google Chat', 'chat', 'US', r'chat\.googleapis\.com'),
    ('GoDaddy Mail', 'email', 'US', r'secureserver\.net'),
    ('IONOS Mail', 'email', 'EU', r'smtp\.ionos\.\w+|smtp\.1and1\.\w+|kundenserver\.de'),
    ('Strato Mail', 'email', 'EU', r'smtp\.strato\.\w+'),
    ('All-Inkl Mail', 'email', 'EU', r'kasserver\.com'),
    ('Hetzner Mail', 'email', 'EU', r'your-server\.de'),
    ('mailbox.org', 'email', 'EU', r'smtp\.mailbox\.org'),
    ('GMX / WEB.DE Mail', 'email', 'EU', r'mail\.gmx\.\w+|smtp\.web\.de'),
    ('Zoho Mail', 'email', 'US', r'smtp\.zoho\.com'),
    ('Zoho Mail EU', 'email', 'EU', r'smtp\.zoho\.eu'),
    ('Google Analytics', 'analytics', 'US', r'googletagmanager\.com|google-analytics\.com|ngx-google-analytics|\bgtag\('),
    ('Meta Pixel', 'analytics', 'US', r'connect\.facebook\.net|\bfbq\('),
    ('Hotjar', 'analytics', 'EU', r'hotjar'),
    ('Microsoft Clarity', 'analytics', 'US', r'clarity\.ms'),
    ('PostHog', 'analytics', 'US', r'posthog'),
    ('Mixpanel', 'analytics', 'US', r'mixpanel'),
    ('Segment', 'analytics', 'US', r'cdn\.segment\.com|@segment/'),
    ('Matomo', 'analytics', 'EU', r'matomo'),
    ('Plausible', 'analytics-cookieless', 'EU', r'plausible\.io'),
    ('Google Fonts', 'fonts', 'US', r'fonts\.googleapis\.com|fonts\.gstatic\.com'),
    ('Adobe Fonts', 'fonts', 'US', r'use\.typekit\.net'),
    ('Font Awesome CDN', 'cdn', 'US', r'kit\.fontawesome\.com|use\.fontawesome\.com'),
    ('jsDelivr / unpkg / cdnjs', 'cdn', 'US', r'cdn\.jsdelivr\.net|unpkg\.com|cdnjs\.cloudflare\.com'),
    ('Google Maps', 'maps', 'US', r'maps\.googleapis\.com|@angular/google-maps|@googlemaps/'),
    ('Mapbox', 'maps', 'US', r'mapbox'),
    ('Google reCAPTCHA', 'captcha', 'US', r'google\.com/recaptcha|ng-recaptcha|recaptcha'),
    ('hCaptcha', 'captcha', 'US', r'hcaptcha'),
    ('YouTube', 'video', 'US', r'youtube\.com/embed|youtube-nocookie|@angular/youtube-player'),
    ('Vimeo', 'video', 'US', r'player\.vimeo\.com'),
)]
PAGE_LOAD = {'analytics', 'fonts', 'cdn', 'maps', 'captcha', 'video'}
CONSENT_TOOL = re.compile(r'(?i)cookiebot|usercentrics|klaro|cookieconsent|cookie-consent|ccm19|consentmanager|'
                          r'borlabs|onetrust|didomi|iubenda|tarteaucitron|consent-?banner|cookie-?banner')
URL_HOST = re.compile(r'(?i)\b(?:https?|smtps?|wss?)://(?:[^@/\s"\'{}]*@)?([a-z0-9][\w-]*(?:\.[\w-]+)+)')
LOCAL_HOST = re.compile(r'(?i)^(?:localhost|127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|'
                        r'host\.docker\.internal)|\.(?:local|internal|localhost|lan|svc|test|example|invalid|arpa)$|'
                        r'(?:^|\.)example\.(?:com|org|net)$')
# the app's own addresses and its infrastructure are no recipients
OWN_KEY = re.compile(r'(?i)cors|origin|redirect|callback|return|success|cancel|frontend|base-?url|public-?url|app-?url|'
                     r'homepage|website|^(?:server|management|springdoc|logging|info)\.|'
                     r'^spring\.(?!mail\.|ai\.|security\.oauth2\.client)')
KIND_HINTS = [(k, re.compile(rx, re.I)) for k, rx in (
    ('email', r'mail|smtp'),
    ('chat', r'webhook|discord|slack|teams|telegram|chat'),
    ('ai', r'(?:^|[^a-z])(?:ai|llm|gpt|ki)(?:[^a-z]|$)|openai|ocr|texterkennung|belegerkennung|vision'),
    ('payment', r'payment|zahlung|billing'),
    ('holidays', r'feiertag|holiday|ferien'),
    ('storage', r'storage|minio|(?:^|[^a-z])s3(?:[^a-z]|$)|bucket|blob'),
    ('identity', r'auth|identit|oauth|issuer|jwk|keycloak|sso'),
    ('maps', r'geocod|nominatim|routing|(?:^|[^a-z])maps?(?:[^a-z]|$)'))]
MAIL_CODE = re.compile(r'\bJavaMailSender\b|\bMimeMessageHelper\b|\bSimpleMailMessage\b')
NOTIFIER = re.compile(r'(?i)webhook|discord|slack|mattermost|telegram|msteams|JavaMailSender|MimeMessageHelper|'
                      r'SimpleMailMessage')
NOTIFY_NAME = re.compile(r'(?i)notif|webhook|discord|slack|alert|mail')
CALL = re.compile(r'\b(\w+)\s*\??\.\s*(\w+)\s*\(')
URI_READ = re.compile(r'\b(?:requestURI|getRequestURI|requestURL|getRequestURL|servletPath|getServletPath|queryString|'
                      r'getQueryString)\b')
PATH_VAR = re.compile(r'\{\s*(\w+)\s*(?::[^}]*)?\}')
TOKEN_VAR = re.compile(r'(?i)^(?:\w*token|\w*link)$')
CODE_VAR = re.compile(r'(?i)^(?:\w*code|\w*key)$')
LOOKUP_VAR = re.compile(r'(?i)^(?:country|language|lang|locale|currency|iso|postal|zip|product|status|type|colou?r|'
                        r'area|region|i18n|message|translation|sort|group|category|kategorie|sprach|land|waehrung|'
                        r'discount|rabatt|promo|voucher|gutschein|coupon)')
AUTHORITY_RULE = re.compile(r'^(?:has(?:Any)?(?:Authority|Role)|authenticated|fullyAuthenticated|denyAll)')
# what a log call may name without logging the value: a template, a counter, a switch
LOG_IDENT_SKIP = re.compile(r'_(?:properties|props|settings|sender|service|client|host|port|server|enabled|from|'
                            r'subject|body|text|html|content|message|result|response|request|job|queue|event|task|'
                            r'size|status|domain|provider|pattern|regex|validator|verified|template|config|count|'
                            r'limit|util|utils|helper|formatter|parser|mapper|factory|builder|handler|listener|'
                            r'repository|repo|valid|invalid|changed|exists|taken|unique|confirmed|updated|missing|'
                            r'blank|empty|matches)$')
MASKING = re.compile(r'(?i)mask|redact|anonymi|pseudonym|hash|abbreviat|truncat|obfuscat|kuerz|schwaerz|verdeck|'
                     r'verschleier|unkenntlich')
# adresse alone is as often a service URL as a postal address
PERSON_ADDRESS = re.compile(r'strasse|street|anschrift|wohnort|(?:post|wohn|liefer|rechnungs|privat|heim|melde|kunden?|'
                            r'customer|user|billing|shipping|home|delivery|postal|mailing)_?(?:adresse|address)')
CONFIG_HOLDER = re.compile(r'(?i)propert|props$|config|einstellung|eigenschaft|setting|option')


def snake(name: str) -> str:
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower().strip('_')


def classify(col: str, sql_type: str = '') -> str | None:
    for cat, _, rx in CATEGORIES:
        if rx.search(col):
            if cat in VALUE_CATS and (NO_VALUE_TYPE.match(sql_type) or NOT_A_VALUE.search(col)) or \
                    cat in NO_NUMBER_CATS and NUMERIC.match(sql_type):
                continue
            return cat
    return None


def _value_category(values: list[str]) -> tuple[str, str] | None:
    health = [v for v in values if HEALTH_VALUE.match(v)]
    if health:
        return 'health', health[0]
    religion = [v for v in values if RELIGION_VALUE.match(v)]
    if len(religion) >= 2:
        return 'religion', religion[0]
    return None


def _subject(name: str) -> str | None:
    if BUSINESS.search(name):
        return 'business'
    return next((s for s, rx in SUBJECTS if rx.search(name)), None)


def _enums(ctx) -> dict[str, list[str]]:
    out = {}
    for j in ctx.main:
        bare = j.src.bare
        for m in re.finditer(r'\benum\s+(?:class\s+)?(\w+)[^{;]*\{', bare):
            close = balanced(bare, m.end() - 1, '{', '}')
            body = bare[m.end():close if close > 0 else len(bare)].split(';')[0]
            names = [re.match(r'\s*(?:@[\w.]+(?:\([^)]*\))?\s*)*(\w+)', p) for _, p in split_top(body)]
            out[m.group(1)] = [n.group(1) for n in names if n and re.match(r'[A-Z][A-Z0-9_]*$', n.group(1))]
    return out


def _encrypting_converters(ctx) -> tuple[set[str], set[str]]:
    """(converter names that encrypt, value types an autoApply encrypting converter covers)."""
    names, auto = set(), set()
    for j in ctx.main:
        for c in j.classes:
            conv = re.search(r'AttributeConverter\s*<\s*([\w.]+)', c.header)
            if not conv:
                continue
            body = j.src.code[c.body[0]:c.body[1]] if c.body else ''
            if ENCRYPTING.search(c.name) or CRYPT_BODY.search(body):
                names.add(c.name)
                if re.search(r'autoApply\s*=\s*true', c.anno_code):
                    auto.add(conv.group(1).split('.')[-1])
    return names, auto


def _encrypted(prop: dict, converters: set[str], auto: set[str]) -> bool:
    code = prop['anno_code']
    conv = re.search(r'@Convert\s*\([^)]*?converter\s*=\s*(\w+)', code)
    if conv and (conv.group(1) in converters or ENCRYPTING.search(conv.group(1))):
        return True
    if re.search(r'@ColumnTransformer[\s\S]*?(pgp_sym|encrypt|decrypt)', code, re.I):
        return True
    if {'Encrypted', 'Encrypt', 'Verschluesselt'} & set(prop['annos']) or re.search(r'@Type\([^)]*Encrypt', code):
        return True
    return prop['type'].replace('?', '').strip() in auto


def _tables(ctx, mig: dict, enums: dict) -> dict[str, dict]:
    """Every table with its columns, each column with type, location, entity property and enum values."""
    converters, auto = _encrypting_converters(ctx)
    tables: dict[str, dict] = {}
    for name, t in mig['tables'].items():
        table_at = tuple(t['file'].rsplit(':', 1)) if t['file'] else None
        cols = {c: {'type': t['types'].get(c, ''), 'where': t['where'].get(c) or table_at, 'values': [], 'prop': None,
                    'encrypted': False} for c in t['columns']}
        for col, values, rel, line in t['checks']:
            if col in cols:
                cols[col]['values'] += values
        tables[name] = {'columns': cols, 'entity': None, 'file': t['file'],
                        'fk_refs': [(c, ref) for cs, ref, _, _ in t['fks'] for c in cs],
                        'ondelete': t['ondelete']}
    for j in ctx.main:
        for cls in j.classes:
            if not cls.has('Entity'):
                continue
            explicit = re.search(r'@Table\s*\(\s*(?:name\s*=\s*)?"([^"]+)"', cls.anno_code)
            tname = (explicit.group(1) if explicit else snake(cls.name)).split('.')[-1].lower()
            t = tables.setdefault(tname, {'columns': {}, 'entity': None, 'file': f'{j.rel}:{cls.line}', 'fk_refs': [],
                                          'ondelete': []})
            t['entity'] = (j, cls)
            for p in schema._props(j, cls):
                if {'Transient', 'OneToMany', 'ManyToMany', 'Embedded', 'EmbeddedId'} & set(p['annos']):
                    continue
                named = re.search(r'name\s*=\s*"(\w+)"', schema._anno_args(p['anno_code'], 'Column') or
                                  schema._anno_args(p['anno_code'], 'JoinColumn') or '')
                ref = {'ManyToOne', 'OneToOne'} & set(p['annos'])
                col = named.group(1).lower() if named else snake(p['name']) + ('_id' if ref else '')
                base = p['type'].replace('?', '').strip()
                entry = t['columns'].setdefault(col, {'type': entity_x.SQL.get(base, ''), 'where': (j.rel, p['line']),
                                                      'values': [], 'prop': None, 'encrypted': False})
                entry['prop'] = p
                entry['encrypted'] = _encrypted(p, converters, auto)
                if base in enums:
                    entry['values'] += enums[base]
                if ref:
                    t['fk_refs'].append((col, snake(schema._target(p))))
    return tables


def _link(name: str, t: dict) -> list[str]:
    own = _subject(name)
    if own:
        return [own]
    if t['entity'] and _subject(snake(t['entity'][1].name)):
        return [_subject(snake(t['entity'][1].name))]
    via = []
    for col, ref in t['fk_refs']:
        for cand in (_subject(ref), _subject(col[:-3]) if col.endswith('_id') else None):
            if cand and cand != 'business' and cand not in via:
                via.append(cand)
    return via


def _log_table(name: str, columns) -> bool:
    words = name.split('_')
    return any(LOG_TOKEN.fullmatch(w) for w in words) or \
        any(WEAK_LOG_TOKEN.fullmatch(w) for w in words) and any(ACTOR.search(c) for c in columns)


def _employer(tables: dict) -> bool:
    words = [n for n in tables] + [c for t in tables.values() for c in t['columns']] + \
        [v.lower() for t in tables.values() for c in t['columns'].values() for v in c['values']]
    return any(EMPLOYMENT.search(w) for w in words)


def profile_tables(tables: dict) -> list[dict]:
    out = []
    employer = _employer(tables)
    for name, t in tables.items():
        subjects = _link(name, t)
        log = _log_table(name, t['columns'])
        cols = []
        for col, c in sorted(t['columns'].items()):
            if OWN_PREFIX.match(col) and subjects != ['business']:
                continue
            cat = classify(col, c['type'])
            via = None
            hit = _value_category(c['values'])
            if hit and TIER.get(cat) != 'special':
                cat, via = hit[0], f'value {hit[1]}'
            if not cat and re.search(r'(?:^|_)name$', col) and col != 'name' and \
                    (_subject(col[:-5]) not in (None, 'business') or re.search(r'_(von|by)_name$', col)):
                cat = 'name'
            if not cat and col == 'name' and subjects and subjects[0] not in ('business',) and _subject(name):
                cat = 'name'
            if not cat and re.search(_t('ort', 'city', 'stadt'), col) and \
                    any(classify(o, '') == 'address' for o in t['columns'] if o != col):
                cat = 'address'
            if not cat and FREE_TEXT_TABLE.search(name) and col in ('text', 'inhalt', 'body', 'content') and \
                    not NUMERIC.match(c['type']):
                cat = 'free_text'
            if not cat and log and not NUMERIC.match(c['type']) and not NO_VALUE_TYPE.match(c['type']):
                cat = 'account' if ACTOR.search(col) else 'free_text' if LOG_FREE.match(col) else None
            if cat:
                cols.append({'column': col, 'category': cat, 'tier': TIER[cat], 'via': via, 'type': c['type'],
                             'encrypted': c['encrypted'], 'where': c['where'], 'prop': c['prop']})
        if not subjects and any(c['category'] in ('name', 'contact', 'birth') for c in cols):
            subjects = ['persons']
        elif not subjects and cols and not SETTINGS.search(name) and \
                (log or any(c['category'] == 'account' for c in cols)):
            account = next((c['column'] for c in cols if c['category'] == 'account'), '')
            subjects = [s if (s := _subject(account)) not in (None, 'business') else 'users']
        subjects = list(dict.fromkeys('users' if s == 'employees' and not employer else s for s in subjects))
        if not subjects or not cols:
            continue
        if subjects == ['business']:
            cols = [c for c in cols if c['tier'] != 'special']
        if not cols:
            continue
        out.append({'table': name, 'subjects': subjects, 'columns': cols, 'entity': t['entity'], 'file': t['file'],
                    'all_columns': list(t['columns']), 'types': {k: v['type'] for k, v in t['columns'].items()},
                    'fk_refs': t['fk_refs'], 'ondelete': t['ondelete'], 'log': log})
    for p in out:
        p['need'], p['reason'] = _need(p)
    return sorted(out, key=lambda p: (-NEEDS.index(p['need']), p['table']))


def _need(p: dict) -> tuple[str, str]:
    """BSI 200-2 categories: the highest single column decides (Maximumprinzip), several high ones together raise
    the level (Kumulationseffekt)."""
    if p['subjects'] == ['business']:
        return 'normal', ''
    cats = {c['category'] for c in p['columns']}
    tiers = {c['tier'] for c in p['columns']}
    special = next((c for c in p['columns'] if c['tier'] == 'special'), None)
    if special:
        return 'very high', f'{p["table"]}.{special["column"]}: {special["category"]}' + \
            (f' ({special["via"]})' if special['via'] else '')
    if 'children' in p['subjects'] and 'identifying' in tiers:
        return 'very high', f'{p["table"]}: identifying data of children'
    high = cats & {c for c, tier, _ in CATEGORIES if tier == 'high'}
    if (len(high) >= 2 and cats & {'name', 'address'}) or (high & {'bank', 'gov_id', 'card'} and 'birth' in cats):
        return 'very high', f'{p["table"]}: {", ".join(sorted(high | (cats & {"birth"})))} together with a name'
    if high == {'bank'} and not cats & {'name', 'address', 'birth'}:
        return 'high (needs reader)', f'{p["table"]}: bank without name or address - often the business account'
    if high:
        return 'high', f'{p["table"]}: {", ".join(sorted(high))}'
    if set(p['subjects']) & {'employees', 'patients', 'applicants'} and cats & {'device', 'activity'}:
        return 'high', f'{p["table"]}: behaviour trail of {p["subjects"][0]}'
    return 'normal', ''


def _hubs(profiles: list[dict]) -> list[dict]:
    by_name = {p['table']: p for p in profiles}
    out = []
    for p in profiles:
        if not _subject(p['table']) or _subject(p['table']) == 'business':
            continue
        reached = [q for q in profiles if q is not p and any(ref == p['table'] for _, ref in q['fk_refs'])]
        if len(reached) >= 2:
            cats = sorted({c['category'] for q in [p] + reached for c in q['columns']})
            out.append({'table': p['table'], 'reached': [q['table'] for q in reached], 'categories': cats,
                        'need': max((by_name[q['table']]['need'] for q in reached + [p]), key=NEEDS.index)})
    same = defaultdict(list)
    for p in profiles:
        fks = {c for c, _ in p['fk_refs']}
        keys = {c['column'] for c in p['columns'] if c['category'] == 'account'} | \
            {c for c in p['all_columns'] if re.search(r'_(?:id|ref)$', c)
             and _subject(re.sub(r'_(?:id|ref)$', '', c)) not in (None, 'business')}
        for col in keys - fks:
            same[col].append(p)
    for col, reached in same.items():
        if len(reached) >= 3:
            out.append({'table': f'*.{col}', 'by': 'name', 'reached': [q['table'] for q in reached],
                        'categories': sorted({c['category'] for q in reached for c in q['columns']}),
                        'need': max((q['need'] for q in reached), key=NEEDS.index)})
    return sorted(out, key=lambda h: (-NEEDS.index(h['need']), -len(h['reached'])))[:5]


def _erasure(ctx, profiles: list[dict]) -> dict[str, tuple[str, str]]:
    """table -> ('delete' | 'anonymise', how). Only a real delete cascades to the child tables."""
    code = '\n'.join(j.src.code for j in ctx.main).lower()
    deleted = set(re.findall(r'\bdelete\s+from\s+(?:\w+\.)?(\w+)', code))
    nulled = set(re.findall(r'\bupdate\s+(?:\w+\.)?(\w+)\s+set\b[^;]{0,400}?\bnull\b', code))
    repo_of, by_repo, anon = {}, {}, {}
    for j in ctx.main:
        for c in j.classes:
            m = re.search(r'Repository\s*<\s*(\w+)', c.header)
            if m:
                repo_of[c.name] = m.group(1)
                if any(re.match(r'(delete|remove)', x.name) for x in j.methods(c)):
                    by_repo[m.group(1)] = f'{c.name} declares a delete'
    for j in ctx.main:
        bare = j.src.bare
        typed = {f: t for f, t in re.findall(r'(\w+)\s*:\s*(\w+)', bare) if t in repo_of}
        typed.update({f: t for t, f in re.findall(r'\b(\w+)\s+(\w+)\s*[;,)=]', bare) if t in repo_of})
        for f in re.findall(r'\b(\w+)\s*\??\.\s*(?:delete|remove)\w*\s*\(', bare):
            if f in typed:
                by_repo.setdefault(repo_of[typed[f]], f'{typed[f]}.delete in {j.name}')
        m = next((m for m in j.methods() if ANON_METHOD.match(m.name)), None)
        if m:
            for word in set(re.findall(r'\b[A-Z]\w+', bare)):
                anon.setdefault(word, f'{j.name}.{m.name}')
    paths = {}
    for p in profiles:
        t = p['table']
        entity = p['entity'][1].name if p['entity'] else ''
        column = next((c for c in p['all_columns'] if ANONYMISED.search(c)), None)
        if t in deleted or entity.lower() in deleted:
            paths[t] = ('delete', 'delete statement')
        elif entity in by_repo:
            paths[t] = ('delete', by_repo[entity])
        elif t in nulled:
            paths[t] = ('anonymise', 'update to null')
        elif column:
            paths[t] = ('anonymise', f'anonymised ({column})')
        elif entity in anon:
            paths[t] = ('anonymise', anon[entity])
    changed = True
    while changed:
        changed = False
        for p in profiles:
            if p['table'] in paths:
                continue
            ref = next((ref for _, ref, action in p['ondelete'] if action == 'cascade'
                        and paths.get(ref, ('',))[0] == 'delete'), None)
            if ref:
                paths[p['table']] = ('delete', f'cascade from {ref}')
                changed = True
    return paths


def _supertypes(j, c) -> list[str]:
    head = c.header.split('{')[0]
    if j.kotlin:
        return [s.split('.')[-1] for s in entity_x.supertypes_of(head)]
    parts = re.split(r'\b(?:extends|implements)\b', head, maxsplit=1)
    return [s.split('.')[-1] for s in re.findall(r'\b([A-Z][\w.]*)', parts[1])] if len(parts) > 1 else []


def _typed(bare: str) -> dict[str, str]:
    """field or parameter name -> declared type, Kotlin and Java style."""
    out = {f: t for f, t in re.findall(r'(\w+)\s*:\s*([A-Z]\w+)', bare)}
    out.update({f: t for t, f in re.findall(r'\b([A-Z]\w+)(?:<[^>]*>)?\s+(\w+)\s*[;,)=]', bare)})
    return out


def _deleters(ctx, tables: dict):
    """deleted(class, method) -> tables a call deletes from, following fields, interfaces and own methods 3 deep."""
    by_entity = {t['entity'][1].name: n for n, t in tables.items() if t['entity']}
    classes, impls, fields = {}, defaultdict(list), {}
    for j in ctx.main:
        for c in j.classes:
            classes.setdefault(c.name, (j, c))
            for sup in _supertypes(j, c):
                impls[sup].append(c.name)
        fields[j.rel] = _typed(j.src.bare)

    def table_of(word: str) -> str | None:
        return next((t for t in (word.lower(), by_entity.get(word), snake(word)) if t in tables), None)

    memo = {}

    def deleted(cls: str, method: str, depth: int = 0) -> set[str]:
        if (cls, method) in memo or depth > 3:
            return memo.get((cls, method), set())
        memo[cls, method] = out = set()
        for name in [cls] + impls.get(cls, []):
            if name not in classes:
                continue
            j, c = classes[name]
            entity = re.search(r'Repository\s*<\s*(\w+)', c.header)
            ms = [m for m in j.methods(c) if m.name == method]
            if entity and DERIVED_DELETE.match(method) and not any(m.has('Query') for m in ms):
                out |= {table_of(entity.group(1))} - {None}
            own = {x.name for x in j.methods(c)}
            for m in ms:
                out |= {t for w in DELETE_SQL.findall(m.anno_code + j.body_text(m, 'code')) if (t := table_of(w))}
                body = j.body_text(m)
                for recv, call in CALL.findall(body):
                    if recv in fields[j.rel]:
                        out |= deleted(fields[j.rel][recv], call, depth + 1)
                for call in set(re.findall(r'(?<![\w.$])(\w+)\s*\(', body)) & own - {method}:
                    out |= deleted(name, call, depth + 1)
        return out
    return deleted


def _retention(ctx, tables: dict) -> tuple[list[str], dict[str, str]]:
    """(cleanup jobs with the tables they reach, table -> job). A cascade from a cleaned table cleans the child."""
    deleted = _deleters(ctx, tables)
    jobs, cleaned = [], {}
    for j in ctx.main:
        for m in j.methods():
            if not m.has('Scheduled', 'SchedulerLock') or not m.owner:
                continue
            reached = sorted(deleted(m.owner.name, m.name))
            if reached or CLEANUP.search(m.name):
                job = f'{j.name}.{m.name}'
                jobs.append(job + (f' -> {", ".join(reached)}' if reached else ' (no table found)'))
                for t in reached:
                    cleaned.setdefault(t, job)
    changed = True
    while changed:
        changed = False
        for name, t in tables.items():
            ref = next((ref for _, ref, action in t['ondelete'] if action == 'cascade' and ref in cleaned), None)
            if name not in cleaned and ref:
                cleaned[name] = f'cascade from {ref}'
                changed = True
    for src, entries in ctx.configs:
        for e in entries:
            if re.search(r'retention|aufbewahr|loeschfrist|delete-?after|(?:^|[.-])ttl(?:$|[.-])', e.key.lower()):
                jobs.append(f'{src.rel}:{e.line} {e.key}')
    return jobs, cleaned


def _hinted(code: str) -> str:
    """Only the lines that can name a provider: a host, an import, a tracking call - the rest of the code cannot."""
    return '\n'.join(line for line in code.split('\n') if '://' in line or 'import' in line or '.com' in line or
                     '.net' in line or '.io' in line or 'gtag' in line or 'fbq' in line or 'from ' in line or
                     'ebhook' in line)


def _outbound_hosts(ctx, calls: list[dict]) -> list[tuple[str, str, str]]:
    """(host, hint for the kind, where) for every URL-valued config key and every resolved call host. The mail host
    stands in for every mail the app sends; without one in the repo it is a recipient of unknown seat."""
    out, mail_at = [], None
    for src, entries in ctx.configs:
        if is_test_path(src.rel):
            continue
        for e in entries:
            if profile_kind(e.profile) == 'dev':
                continue
            if e.key.lower().endswith('mail.host'):
                host = re.sub(r'^\$\{[^:}]*:?([^}]*)\}$', r'\1', e.value.strip()).strip()
                mail_at = mail_at or src.rel
                if '.' in host and not LOCAL_HOST.search(host) and '$' not in host:
                    out.append((host.lower(), 'smtp', src.rel))
            elif not OWN_KEY.search(e.key):
                out += [(h.lower(), e.key, src.rel) for h in URL_HOST.findall(e.value)]
    for c in calls:
        if c.get('host'):
            out.append((c['host'].lower().split(':')[0], 'smtp' if c.get('kind') == 'mail' else
                        f'{c.get("where", "")} {c.get("target", "")}', c['file']))
    out = [(h, hint, where) for h, hint, where in out if not LOCAL_HOST.search(h)]
    mails = [c for c in calls if c.get('kind') == 'mail']
    if (mails or MAIL_CODE.search(ctx.all_main)) and not any(hint == 'smtp' for _, hint, _ in out):
        out.append(('', 'smtp', mails[0]['file'] if mails else mail_at or next(
            (j.rel for j in ctx.main if MAIL_CODE.search(j.src.bare)), '')))
    return out


def _call_texts(repo, calls: list[dict]) -> list[tuple[str, str]]:
    """The call site and the three lines after it - where a builder names its URL property."""
    out = []
    for c in calls:
        src = repo.source(c['file'])
        lines = '\n'.join(src.line(i) for i in range(c['line'], min(c['line'] + 4, len(src.lines) + 1)))
        out.append((c['file'], f'{c.get("where", "")} {c.get("target", "")} {c.get("host") or ""}\n{lines}'))
    return out


def _recipients(repo, ctx, workspaces, calls: list[dict]) -> list[dict]:
    texts = []
    if ctx:
        texts.append(('build files', ctx.build))
        texts += [(s.rel, s.text) for s, _ in ctx.configs if not is_test_path(s.rel)]
        texts += [(j.rel, _hinted(j.src.code)) for j in ctx.main]
    for w in workspaces:
        pkg = w.prefix + 'package.json'
        if pkg in repo.files:
            deps = re.search(r'"dependencies"\s*:\s*\{[^}]*\}', repo.source(pkg).text)
            texts.append((pkg, deps.group() if deps else ''))
        for f in w.files:
            if f.endswith(('.html', '.scss', '.css')) and not is_test_path(f):
                texts.append((f, repo.source(f).code))
        texts += [(f, _hinted(repo.source(f).code)) for f in w.main_ts]
    texts += _call_texts(repo, calls)
    found = {}
    for name, kind, seat, rx in PROVIDERS:
        where = list(dict.fromkeys(rel for rel, text in texts if rx.search(text)))
        if where:
            frontend = any(rel.endswith(('.html', '.scss', '.css', '.ts', 'package.json')) for rel in where)
            found[name] = {'name': name, 'kind': kind, 'seat': seat, 'where': where[:6], 'frontend': frontend}
    for host, hint, where in _outbound_hosts(ctx, calls) if ctx else []:
        known = next(((n, k, s) for n, k, s, rx in PROVIDERS if host and rx.search(host)), None)
        name = known[0] if known else host or 'SMTP server (host set outside the repo)'
        kind = known[1] if known else 'email' if hint == 'smtp' else \
            next((k for k, rx in KIND_HINTS if rx.search(f'{hint} {host}')), 'api')
        r = found.setdefault(name, {'name': name, 'kind': kind, 'seat': known[2] if known else 'unknown',
                                    'where': [], 'frontend': False})
        if host:
            r['host'] = host
        if where not in r['where'] and len(r['where']) < 6:
            r['where'].append(where)
    return list(found.values())


def _log_idents(exprs: list[str]) -> list[str]:
    """Compound names (customerEmail, getIban(), rechnungsAdresse) the field list above cannot spell out."""
    out = []
    for e in exprs:
        if MASKING.search(e):
            continue
        for holder, ident, call in re.findall(r'(?<![\w$])(?:(\w+)\s*\??\.\s*)?([A-Za-z_]\w*)(\s*\()?', e):
            prop = ident[3:] if call and re.match(r'get[A-Z]', ident) else None if call or ident[0].isupper() else ident
            s = snake(prop or '')
            if not s or LOG_IDENT_SKIP.search(s) or NOT_A_VALUE.search(s) or CONFIG_HOLDER.search(holder):
                continue
            cat = 'contact' if re.match(r'(?:recipients?|empfaenger\w*|to_?address|mail_?to)$', s) else classify(s)
            if cat in ('contact', 'bank', 'birth', 'gov_id', 'card') or cat == 'address' and (
                    PERSON_ADDRESS.search(s) or SUBJECT_VAR.match(holder.lower())):
                out.append(prop)
    return out


def _log_hits(ctx):
    for j in ctx.main:
        bare, code = j.src.bare, j.src.code
        for m in LOGGER.finditer(bare):
            opening = m.end() - 1
            close = balanced(bare, opening, *(('(', ')') if m.group(1) == '(' else ('{', '}')))
            args_bare = bare[opening:close if close > 0 else opening + 300]
            args_code = code[opening:close if close > 0 else opening + 300]
            exprs = [args_bare] + [''.join(e) for e in re.findall(r'\$\{([^}]*)\}|\$(\w+)', args_code)]
            fields = [f for e in exprs if not MASKING.search(e) for f in LOG_FIELD.findall(e)
                      if not NOT_A_VALUE.search(snake(f))] or _log_idents(exprs)
            owner = next((c.name for c in reversed(j.classes) if c.body and c.body[0] < m.start() < c.body[1]),
                         j.name)
            if fields:
                ctx.hit('PII-LOG', j, m.start(), f'{owner}: {", ".join(sorted(set(fields)))}  '
                                                  + j.src.line(j.src.line_at(m.start())).strip()[:90])
            elif SUBJECT_VAR.search(args_bare.replace('\n', ' ')[1:]):
                ctx.hit('PII-LOG', j, m.start(), severity='low',
                        note='logs the whole object - its toString decides what lands in the log')


def _response_hits(ctx):
    fields = {}
    for j in ctx.main:
        for c in j.classes:
            own = [(p.name, p.type) for p in c.params]
            own += [(m.name, m.returns) for m in j.members if m.kind == 'field' and m.owner is c
                    and not re.search(r'\b(static|const|companion)\b', m.sig)]
            fields.setdefault(c.name, own)

    def flagged(cls: str, depth: int = 0) -> list[str]:
        out = []
        cats = {n: classify(snake(n), t.replace('?', '').strip().lower()) for n, t in fields.get(cls, [])}
        person = _subject(snake(cls)) not in (None, 'business') or \
            any(TIER.get(c) == 'identifying' and c != 'tax_number' for c in cats.values())
        for name, typ in fields.get(cls, []):
            cat = cats[name]
            if cat == 'credential' or TIER.get(cat) == 'special' or person and cat in RESPONSE_CATS:
                out.append(f'{name} ({cat})')
            elif depth < 1:
                inner = re.findall(r'\b([A-Z]\w+)', typ)
                out += [f'{name}.{x}' for i in inner if i not in WRAPPERS and i != cls for x in flagged(i, depth + 1)]
        return out

    by_type = defaultdict(list)
    for e in ctx.endpoints:
        for name in re.findall(r'\b([A-Z]\w+)', e.get('returns') or ''):
            if name not in WRAPPERS and name in fields and not SETTINGS.search(name):
                by_type[name].append(e)
    for name, eps in sorted(by_type.items()):
        found = flagged(name)
        if not found:
            continue
        lists = [e for e in eps if re.search(r'\b(List|Page|Set|Collection|Iterable|Slice|Flux)\b', e['returns'])]
        first = (lists or eps)[0]
        ctx.hit('PII-RESPONSE', first['file'], first['line'],
                f'{name}: {", ".join(found[:6])} - {len(eps)} endpoint(s), {len(lists)} of them a list, '
                f'e.g. {first["http"]} {first["path"]}',
                severity='high' if any('credential' in f for f in found) else None,
                names=[f'{e["http"]} {e["path"]}' for e in eps][:20])


def _url_hits(ctx):
    for e in ctx.endpoints:
        m = e.get('_member')
        if not m:
            continue
        bad = [p.name for p in m.params if {'PathVariable', 'RequestParam'} & set(p.annos)
               and (classify(snake(p.name)) in URL_CATS or TIER.get(classify(snake(p.name))) == 'special')]
        if bad:
            ctx.hit('PII-IN-URL', e['file'], e['line'], f'{e["http"]} {e["path"]}: {", ".join(bad)}')


def _seed_hits(repo, hits):
    in_tests = []
    for rel in repo.files:
        low = rel.lower()
        test = is_test_path(rel)
        if not (low.endswith('.sql') or test and low.endswith(('.kt', '.java', '.ts', '.json', '.yml', '.yaml'))
                or re.search(r'(seed|fixture|testdata|mock|sample)', low) and low.endswith(('.json', '.yml', '.yaml'))):
            continue
        text = repo.source(rel).text
        if low.endswith(('package.json', 'tsconfig.json')) or '"realm"' in text and '"users"' in text:
            continue
        mails = sorted({f'{m.group(1)}@{m.group(2)}' for m in FREEMAIL.finditer(text)
                        if not FAKE_LOCAL.search(m.group(1))})
        ibans = []
        for m in IBAN.finditer(text):
            iban = m.group(1).replace(' ', '')
            if iban in SAMPLE_IBANS or IBAN_LENGTH.get(iban[:2]) != len(iban) or \
                    re.search(r'(\d)\1{7}|0123456789|1234567890', iban):
                continue
            if int(''.join(str(int(ch, 36)) for ch in iban[4:] + iban[:4])) % 97 == 1:
                ibans.append(iban)
        if not mails and not ibans:
            continue
        sample = [redact(a.split('@')[0]) + '@' + a.split('@')[1] for a in mails[:3]] + [redact(i) for i in ibans[:2]]
        evidence = f'{len(mails)} address(es) at real mail providers, {len(set(ibans))} IBAN(s) with a valid ' \
                   f'checksum: {", ".join(sample)}'
        if test:
            in_tests.append((rel, evidence))
        else:
            first = mails[0] if mails else ibans[0][:8]
            hits.add('PII-SEED-DATA', rel, text[:text.find(first)].count('\n') + 1, evidence)
    if in_tests:
        hits.add('PII-SEED-DATA', in_tests[0][0], None, f'{len(in_tests)} test file(s); first: {in_tests[0][1]}',
                 severity='low', keep_in_tests=True, files=[r for r, _ in in_tests][:40])


def _storage_hits(repo, hits, workspaces):
    for w in workspaces:
        for rel in w.main_ts:
            src = repo.source(rel)
            for m in STORAGE.finditer(src.bare):
                close = balanced(src.bare, m.end() - 1)
                args = src.code[m.end():close if close > 0 else m.end() + 200]
                if STORAGE_PERSONAL.search(args) and not re.search(r'(?i)token|jwt|auth', args):
                    line = src.line_at(m.start())
                    hits.add('PII-FRONTEND-STORAGE', rel, line, src.line(line).strip())


def _forms(workspaces) -> list[dict]:
    out = []
    for w in workspaces:
        for c in getattr(w, 'ux_comps', []):
            fields = []
            for el in ux._controls(c):
                key = ux._field_key(el)
                cat = classify(snake(key)) if key else None
                if cat:
                    fields.append(f'{key} ({cat})')
            if fields:
                out.append({'file': c.html_rel, 'fields': sorted(set(fields))})
    return out


def _unused_hits(ctx, profiles, workspaces):
    words_back = [(j.rel, set(re.findall(r'\w+', j.src.code))) for j in ctx.main]
    words_front = [(f, set(re.findall(r'\w+', ctx.repo.source(f).code))) for w in workspaces
                   for f in w.main_ts + w.html]
    for p in profiles:
        if not p['entity']:
            continue
        j = p['entity'][0]
        for c in p['columns']:
            if c['category'] not in UNUSED_CATS or c['via'] or not c['prop']:
                continue
            name = c['prop']['name']
            back = [rel for rel, words in words_back if rel != j.rel and name in words]
            front = [rel for rel, words in words_front if name in words]
            if len(back) <= 1 and len(front) <= 1:
                ctx.hit('PII-COLLECTED-UNUSED', j.rel, c['prop']['line'],
                        f'{j.name}.{name} ({c["category"]}): {len(back)} other backend file(s), {len(front)} frontend '
                        f'file(s) name it', names=back + front)


def _loc(where) -> tuple[str | None, int | None]:
    """(file, line) from a column's (file, line) or a table's 'file:line'."""
    if isinstance(where, str):
        where = where.rsplit(':', 1)
    return (where[0], int(where[1])) if where else (None, None)


def _table_hits(hits, p: dict):
    special = [c for c in p['columns'] if c['tier'] == 'special']
    if special:
        hits.add('PII-SPECIAL-CATEGORY', *_loc(special[0]['where'] or p['file']),
                 f'{p["table"]} ({", ".join(p["subjects"])}): ' + ', '.join(
                     f'{x["column"]} {x["category"]}' + (f' via {x["via"]}' if x['via'] else '') for x in special))
    if p['subjects'] == ['business']:
        return
    plain = [c for c in p['columns'] if not c['encrypted']
             and (c['category'] in ('bank', 'gov_id', 'card') or c['tier'] == 'special' and not c['via'])
             and not re.match(r'(bytea|blob|bool)', c['type'], re.I)]
    if plain:
        card = any(x['category'] == 'card' for x in plain)
        free_form = any(x['tier'] == 'special' and TEXT_TYPE.match(x['type']) for x in plain)
        own = p['need'] == 'high (needs reader)'
        hits.add('PII-PLAINTEXT', *_loc(plain[0]['where'] or p['file']),
                 f'{p["table"]}: ' + ', '.join(f'{x["column"]} ({x["category"]})' for x in plain),
                 severity='high' if card or free_form else 'low' if own else None,
                 note='PCI DSS scope' if card else 'no name or address next to it - if this is the business '
                      'account printed on every mail, encryption buys nothing' if own else None)
    if p['entity']:
        j, cls = p['entity']
        generated = 'data class' in cls.sig if j.kotlin else \
            cls.has('Data', 'ToString', 'Value') or getattr(cls, 'kind_detail', '') == 'record'
        shown = [c for c in p['columns'] if c['tier'] in ('special', 'high', 'identifying')
                 and not (c['prop'] and 'ToString.Exclude' in c['prop']['anno_code'])]
        if generated and shown:
            hits.add('PII-TOSTRING', j.rel, cls.line, f'{cls.name}: {", ".join(c["column"] for c in shown[:8])}',
                     severity='medium' if any(c['tier'] in ('special', 'high') for c in shown) else None)
    flags = [c for c in p['all_columns'] if CONSENT.search(c) and not PROOF.search(c) and
             (p['types'].get(c, '').lower().startswith('bool') or
              re.search(r'(?:^|_)(aktiv|active|erlaubt|allowed|accepted|akzeptiert|zugestimmt|agreed)$', c))]
    proof = any(CONSENT.search(c) and PROOF.search(c) or
                re.search(r'(einwillig|consent|bestaetigt|confirmed|opt_?in)\w*_(am|at)$', c) for c in p['all_columns'])
    if flags and not proof:
        hits.add('PII-CONSENT-PROOF', *_loc(p['file']),
                 f'{p["table"]}: {", ".join(flags)} without a timestamp or the consent text')


def _seeded(hits, tables: dict) -> dict[str, str]:
    """table -> seeding class for every insert-if-missing seed another pass found."""
    by_entity = {t['entity'][1].name: n for n, t in tables.items() if t['entity']}
    out = {}
    for h in hits.items:
        if h['check'] == 'SEED-INSERT-ONLY' and h.get('entity'):
            table = by_entity.get(h['entity']) or next((t for t in (snake(h['entity']), h['entity'].lower())
                                                        if t in tables), None)
            if table:
                out.setdefault(table, h['evidence'].split('.')[0])
    return out


def _growing(p: dict) -> str | None:
    """Why the table keeps growing: a creation timestamp, or a name that says log, request or token."""
    if p['log'] or any(GROWING.fullmatch(w) for w in p['table'].split('_')):
        return 'log table' if p['log'] else 'name'
    return next((c for c in p['all_columns'] if CREATED.match(c)
                 and (not p['types'].get(c) or TIME_TYPE.match(p['types'][c]))), None)


def _repo_hits(hits, profiles: list[dict], erasure: dict, jobs: list[str], cleaned: dict, seeded: dict,
               referenced: set[str]):
    free = [f'{p["table"]}.{c["column"]}' for p in profiles for c in p['columns'] if c['category'] == 'free_text']
    if free:
        first = next(p for p in profiles if any(c['category'] == 'free_text' for c in p['columns']))
        hits.add('PII-FREE-TEXT', _loc(first['file'])[0], None, f'{len(free)} column(s): {", ".join(free[:8])}',
                 names=free[:40])
    missing = [p for p in profiles if p['table'] not in erasure and p['subjects'] != ['business'] and not p['log']
               and {c['tier'] for c in p['columns']} & {'special', 'high', 'identifying'}]
    if missing:
        labels = []
        for p in missing:
            soft = next((c for c in p['all_columns'] if SOFT_DELETE.search(c)), None)
            labels.append(p['table'] + (f' (soft delete only: {soft})' if soft else ''))
        back = [f'{t} ({seeded[t]})' for t in (p['table'] for p in missing) if t in seeded]
        hits.add('PII-NO-ERASURE', _loc(missing[0]['file'])[0], None,
                 f'{len(missing)} of {len(profiles)} personal tables: {", ".join(labels[:8])}', names=labels[:40],
                 note=f'seeded on start (insert if missing): {", ".join(back)} - a deleted row comes back with the '
                      'next start' if back else None)
    unmapped = [j for j in jobs if j.endswith('(no table found)')]
    for p in profiles:
        grows = _growing(p)
        # the person record itself ends with the relationship, which the erasure path covers, not with a date
        master = _subject(p['table']) not in (None, 'business') and p['table'] in referenced and p['table'] in erasure
        if p['subjects'] == ['business'] or p['table'] in cleaned or not grows or master:
            continue
        trail = [c['column'] for c in p['columns'] if c['category'] in ('device', 'activity')]
        hits.add('PII-NO-RETENTION', *_loc(p['file']),
                 f'{p["table"]}: {", ".join(c["column"] for c in p["columns"][:5])} - grows ('
                 + (grows if grows in ('log table', 'name') else f'{grows} column') + '), no cleanup job reaches it',
                 severity='medium' if trail else None,
                 note=f'cleanup jobs without a table: {", ".join(j.split(" ")[0] for j in unmapped)}' if unmapped
                 else None)


def _expiry_hits(hits, tables: dict, cleaned: dict):
    for name, t in sorted(tables.items()):
        if SETTINGS.search(name):
            continue
        access = ACCESS_TABLE.search(name)
        tokens = [c for c, v in t['columns'].items() if (TOKEN_COL.search(c) or access and TOKEN_GENERIC.match(c))
                  and not TOKEN_SKIP.search(c) and not NOT_A_VALUE.search(c)
                  and not (NO_VALUE_TYPE.match(v['type']) or NUMERIC.match(v['type']))]
        if not tokens or name in cleaned or any(EXPIRY.search(c) for c in t['columns']):
            continue
        created = next((c for c in t['columns']
                        if CREATED.match(c) or re.search(r'_(?:erstellt|created)(?:_at|_am)?$', c)), None)
        hits.add('TOKEN-NO-EXPIRY', *_loc(t['columns'][tokens[0]]['where'] or t['file']),
                 f'{name}: {", ".join(tokens)} - no expiry column, no cleanup job',
                 note=f'check whether the code limits the age through {created}' if created else None)


def _token_routes(ctx) -> list[str]:
    out = []
    for e in ctx.endpoints:
        names = PATH_VAR.findall(e['path'])
        gated = AUTHORITY_RULE.match(e.get('url_rule') or '') or e.get('auth')
        if any(TOKEN_VAR.match(n) or CODE_VAR.match(n) and not LOOKUP_VAR.match(n) and not gated for n in names):
            out.append(f'{e["http"]} {e["path"]}')
    return out


def _notifiers(ctx, calls: list[dict]) -> set[str]:
    """Classes that send a chat message or a mail, and the interfaces they implement."""
    files = {c['file'] for c in calls if c.get('kind') == 'mail'}
    out = set()
    for j in ctx.main:
        if j.rel in files or NOTIFIER.search(j.src.code):
            for c in j.classes:
                out.update([c.name] + _supertypes(j, c))
    return out


def _uri_hits(ctx, calls: list[dict]):
    routes = _token_routes(ctx)
    if not routes:
        return
    notifiers = _notifiers(ctx, calls)
    for j in ctx.main:
        bare, code = j.src.bare, j.src.code
        if not URI_READ.search(bare):
            continue
        typed = _typed(bare)
        for m in j.methods():
            if not m.body or not URI_READ.search(j.body_text(m)):
                continue
            start, end = m.body
            names = set(re.findall(r'\b(?:val|var|String|final\s+String|let|const)\s+(\w+)\s*(?::\s*String\??\s*)?=\s*'
                                   r'[^;\n]*' + URI_READ.pattern, bare[start:end]))
            uses = re.compile(URI_READ.pattern + (r'|\b(?:' + '|'.join(names) + r')\b' if names else ''))
            sinks = []
            for s in list(LOGGER.finditer(bare, start, end)) + [
                    x for x in CALL.finditer(bare, start, end)
                    if typed.get(x.group(1)) in notifiers or NOTIFY_NAME.search(x.group(1))]:
                opening = s.end() - 1
                close = balanced(bare, opening, *(('{', '}') if bare[opening] == '{' else ('(', ')')))
                args = code[opening:close if close > 0 else opening + 300]
                if uses.search(args):
                    level = re.search(r'\.\s*(?:at)?(\w+)\s*[({]$', s.group()).group(1).lower() \
                        if s.re is LOGGER else 'notify'
                    sinks.append((s.start(), level))
            if sinks:
                kinds = sorted({'notification' if lv == 'notify' else 'log' for _, lv in sinks})
                ctx.hit('SB-TOKEN-IN-LOG', j, sinks[0][0],
                        f'{m.owner.name if m.owner else j.name}.{m.name}: request URI to {" and ".join(kinds)} - '
                        f'{len(routes)} route(s) with a token in the path, e.g. {routes[0]}',
                        severity='low' if all(lv in ('trace', 'debug') for _, lv in sinks) else None,
                        names=routes[:20])


def _recipient_hits(hits, recipients: list[dict], consent_tool: bool):
    for r in recipients:
        seat = 'seat unknown' if r['seat'] == 'unknown' else f'{r["seat"]} company'
        hits.add('PII-THIRD-PARTY', r['where'][0] or None, None,
                 f'{r["name"]} ({r["kind"]}, {seat}): {", ".join(r["where"][:3])}',
                 severity='medium' if r['kind'] == 'ai' else None)
    page_load = [r for r in recipients if r['frontend'] and r['kind'] in PAGE_LOAD]
    if page_load and not consent_tool:
        hits.add('PII-TRACKING-CONSENT', page_load[0]['where'][0], None,
                 ', '.join(f'{r["name"]} ({r["kind"]})' for r in page_load) + ' - no consent manager found',
                 severity=None if any(r['kind'] == 'analytics' for r in page_load) else 'low')


def run(repo, hits, ctx, workspaces, calls: list[dict] | None = None) -> dict:
    calls = calls or []
    tables = _tables(ctx, getattr(ctx, 'migrations', None) or schema.migrations(repo), _enums(ctx)) if ctx else {}
    profiles = profile_tables(tables)
    recipients = _recipients(repo, ctx, workspaces, calls)
    forms = _forms(workspaces)
    if not profiles and not recipients and not forms:
        return {}
    consent_tool = any(CONSENT_TOOL.search(repo.source(f).code) for w in workspaces for f in w.files
                       if f.endswith(('.html', '.ts', 'package.json')) and not is_test_path(f))
    erasure = _erasure(ctx, profiles) if ctx else {}
    jobs, cleaned = _retention(ctx, tables) if ctx else ([], {})
    for p in profiles:
        _table_hits(hits, p)
    _repo_hits(hits, profiles, erasure, jobs, cleaned, _seeded(hits, tables),
               {ref for t in tables.values() for _, ref in t['fk_refs']})
    _recipient_hits(hits, recipients, consent_tool)
    _expiry_hits(hits, tables, cleaned)
    if ctx:
        _log_hits(ctx)
        _uri_hits(ctx, calls)
        _response_hits(ctx)
        _url_hits(ctx)
        _unused_hits(ctx, profiles, workspaces)
    _seed_hits(repo, hits)
    _storage_hits(repo, hits, workspaces)

    tier_count = defaultdict(int)
    subjects = defaultdict(list)
    for p in profiles:
        for c in p['columns']:
            tier_count[c['tier']] += 1
        for s in p['subjects']:
            subjects[s].append(p['table'])
    points = sum(WEIGHT[t] * n for t, n in tier_count.items())
    return {
        'basis': 'tables' if profiles else 'forms only' if forms else 'recipients only',
        'need': profiles[0]['need'] if profiles else None,
        'decided_by': profiles[0]['reason'] if profiles else None,
        'score': round(100 * points / (points + 80)),
        'points': points,
        'columns': {'personal': sum(tier_count.values()), 'total': sum(len(t['columns']) for t in tables.values())},
        'tables': {'personal': len(profiles), 'total': len(tables)},
        'tiers': {t: tier_count.get(t, 0) for t in TIERS},
        'subjects': {s: sorted(t) for s, t in subjects.items()},
        'encrypted_columns': [f'{p["table"]}.{c["column"]}' for p in profiles for c in p['columns'] if c['encrypted']],
        'retention_jobs': jobs,
        'hubs': _hubs(profiles),
        'recipients': recipients,
        'consent_manager': consent_tool,
        'forms': forms,
        'map': [{'table': p['table'], 'subjects': p['subjects'], 'need': p['need'], 'reason': p['reason'],
                 'erasure': erasure.get(p['table'], (None, None))[1], 'cleanup': cleaned.get(p['table']),
                 'file': p['file'],
                 'columns': [{k: c[k] for k in ('column', 'category', 'tier', 'via', 'encrypted')}
                             for c in p['columns']]}
                for p in profiles],
    }
