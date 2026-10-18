CREATE TABLE kunde (
  id uuid PRIMARY KEY,
  name varchar(200) NOT NULL,
  email varchar(320) NOT NULL,
  erstellt_am timestamptz NOT NULL
);
CREATE TABLE anfrage (
  id uuid PRIMARY KEY,
  kunde_id uuid REFERENCES kunde (id) ON DELETE CASCADE,
  email varchar(320) NOT NULL,
  erstellt_am timestamptz NOT NULL
);
CREATE TABLE zahlungsangabe (
  kunde_id uuid PRIMARY KEY REFERENCES kunde (id) ON DELETE CASCADE,
  iban varchar(34)
);
CREATE TABLE zugangslink (
  id uuid PRIMARY KEY,
  kunde_id uuid NOT NULL REFERENCES kunde (id) ON DELETE CASCADE,
  token_hash varchar(64) NOT NULL,
  erstellt_am timestamptz NOT NULL
);
CREATE TABLE einladung (
  id uuid PRIMARY KEY,
  code varchar(32) NOT NULL,
  gueltig_bis timestamptz NOT NULL
);
CREATE TABLE passwort_reset (
  id uuid PRIMARY KEY,
  reset_token varchar(64) NOT NULL,
  erstellt_am timestamptz NOT NULL
);
CREATE TABLE fahrer (
  id bigint PRIMARY KEY,
  username varchar(60) NOT NULL,
  display_name varchar(100)
);
CREATE TABLE verfuegbarkeit (
  id bigint PRIMARY KEY,
  username varchar(60) NOT NULL,
  slot timestamptz NOT NULL,
  erstellt_am timestamptz NOT NULL
);
CREATE TABLE rundenzeit (
  id bigint PRIMARY KEY,
  username varchar(60) NOT NULL,
  millis integer NOT NULL
);
CREATE TABLE aktivitaet_log (
  id bigint PRIMARY KEY,
  erstellt_von varchar(60) NOT NULL,
  nachricht varchar(200) NOT NULL,
  erstellt_am timestamptz NOT NULL
);
