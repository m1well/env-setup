# Privacy - personal data, protection need, purpose

The scanner draws the map: `--show privacy` lists every table that holds personal data, whom it is
about, its protection need, how a row gets erased, which columns a single join reaches, the third
parties and the forms. Whether the data belongs in this app at all is the reader's question - and
the one that matters most.

## Reading the map

- **Protection need** follows BSI 200-2: `normal`, `high`, `very high`. The highest column decides
  (Maximumprinzip); bank data, an id number and a birth date next to a name raise a table to
  `very high` together (Kumulationseffekt). Special categories (Art. 9) and criminal records
  (Art. 10) are always `very high`.
- **Score** = 100 · p / (p + 80), with p = 20 per special-category column, 6 per high-risk column
  (bank, card, id number, credential, location, income), 2 per identifying, 1 per quasi-identifier
  and free text. 50 means 80 points. It exists to compare runs, not repos.
- **Subjects** come from table names and foreign keys. `employees` only where employment data exists
  (salary, contract, sick days, vacation); otherwise `users`, and the works council duties do not
  apply. When the purpose shows they are employees after all, say so.
- **`high (needs reader)`**: one bank column alone, often the business's own account printed in
  every mail. Decide whose account it is before the table counts as `high`.
- **Hubs**: the person table a single join connects to the most personal tables - over foreign
  keys and over same-named columns without one (`username` in four tables). That join is what an
  attacker with read access, a careless export or a support query gets in one step.
- **Cleanup** per table: `--show privacy` names the job that deletes from it, or a cascade.
  `PII-NO-RETENTION` fires per growing table no job reaches; a retention duty sets an end date, it
  does not remove the need for one.
- **Recipients** come from the outbound calls and the hosts in the configuration. A host the
  scanner cannot place is listed with seat `unknown` - name the provider.
- **No schema** (a frontend repo): the profile comes from the forms only, and the protection need
  is not computable. Say so instead of leaving the section empty.
- **`via value KRANK`**: the column is an enum or a CHECK list with a health value. The value is the
  health data, even when the column is called `art`.

## What only a reader sees

1. **Purpose.** Name the app's purpose in one sentence from modules, routes and tables. Then ask for
   every `high` and `very high` table and every column that looks odd for that purpose: does the
   purpose need exactly this? Usual answers:

   | purpose | justifies | does not justify |
   |---|---|---|
   | invoice, offer | name, address, VAT id, items | birth date, phone as a required field |
   | newsletter | email, consent proof | name as required, birth date, address |
   | time tracking | start, end, break, absence type | location, diagnosis, device data |
   | appointment | name, one contact channel, time | the reason, when the practice is medical |
   | customer account | email, name, what the service needs | gender, nationality, a free "notes" field |

   "Nice to have" is not a purpose. A field nobody reads (`PII-COLLECTED-UNUSED`) is pure liability.
2. **Legal basis for special categories.** Employment (sick days for continued pay) Art. 9(2)(b),
   health care Art. 9(2)(h) with §22 BDSG, explicit consent Art. 9(2)(a) - which one, and does the
   code store more than that basis covers (a diagnosis where the sick day suffices)?
3. **Who sees it.** For every special-category column: which endpoints return it, which role reaches
   them, and does a list or team view ship it for everyone (`PII-RESPONSE` with a list)? Bulk
   exports (CSV, PDF, DATEV) and support or admin views count too.
4. **Erasure against retention.** Invoices and other accounting documents are kept 8 years (§147 AO
   since 2025), books and annual accounts 10. That justifies a restriction flag and a deletion
   date (§35(3) BDSG), not keeping the customer record forever. A soft delete is not erasure.
5. **Free text.** Notes next to sick days, appointments or customer records collect diagnoses and
   opinions. A hint in the form, and the notes belong into every access request (Art. 15).
6. **Recipients.** Per provider: which personal fields reach it (follow the call), a processing
   agreement (Art. 28), for a US company the Data Privacy Framework listing or SCCs. An AI API
   receives whatever goes into the prompt - check whether customer data is part of it.
7. **Consent.** Email marketing needs consent with proof (UWG §7, Art. 7(1)): timestamp, text,
   double opt-in confirmation. Tracking and third-party assets in the browser need it before they
   load (TDDDG §25).

## Consequences - name the ones this repo triggers

- **Breach:** a dump or a leaked backup of a `high` or `very high` database means notifying the
  authority within 72 hours (Art. 33) and, at high risk, every person concerned (Art. 34).
  Non-material damages need no threshold of seriousness (CJEU C-300/21).
- **DPIA (Art. 35):** special categories on a large scale, systematic monitoring of employees,
  scoring. The DSK list of mandatory DPIAs is the German reference.
- **Records and contracts:** every purpose an entry in the record of processing (Art. 30), every
  processor an agreement (Art. 28).
- **Employees:** a system that can show behaviour or performance (time stamps, logins, location)
  needs the works council's consent where one exists (§87(1) Nr. 6 BetrVG).
- **Professional secrecy:** doctors, therapists, lawyers, tax advisors - every service provider
  with access must be bound to secrecy (§203(3), (4) StGB), or disclosure is a criminal offence.
- **Children:** under 16 consent comes from the parents (Art. 8); data about children is `very high`.
- **Card data:** storing a card number puts the system into PCI DSS scope; the CVV must never be
  stored after authorisation.
- **Fines:** up to 20 million euros or 4 % of turnover for a breach of principles or Art. 9
  (Art. 83(5)). Rarely the real risk for a small company - notification duties, damages and lost
  trust are.

## False positives

| check | usually harmless when | a finding when |
|---|---|---|
| `PII-SPECIAL-CATEGORY` | the column is a config code (a payroll key for sick pay) | it describes a person |
| `PII-PLAINTEXT` | the controller's own IBAN printed on every invoice | a customer's or employee's IBAN, a diagnosis |
| `PII-RESPONSE` | the screen shows exactly this field to the person it belongs to | a list or team view ships it for everyone |
| `PII-LOG` | the value is a server address or a template name | an email, a name or an IBAN of a person |
| `PII-SEED-DATA` | an invented name at a real provider in a unit test | a copied production record, a valid IBAN |
| `PII-NO-ERASURE` | the delete runs through code the name match missed | no path at all, or a soft delete only |
| `PII-NO-RETENTION` | the rows are deleted with their owner, or a job outside the repo cleans up | the table only grows |
| `TOKEN-NO-EXPIRY` | the token is single-use and deleted on use | it stays valid until someone deletes it |
| `SB-TOKEN-IN-LOG` | only debug logs, off in production | the URI with the token reaches a production log or a chat channel |
| `PII-THIRD-PARTY` | the SDK is only a dependency of a disabled feature | personal fields reach the provider |
