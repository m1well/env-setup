CREATE TABLE patient (
  id uuid PRIMARY KEY,
  vorname varchar(100) NOT NULL,
  nachname varchar(100) NOT NULL,
  email varchar(320),
  geburtsdatum date,
  iban varchar(34),
  diagnose text,
  konfession varchar(20),
  notiz text,
  geloescht boolean NOT NULL DEFAULT false
);
CREATE TABLE newsletter_abonnent (
  id uuid PRIMARY KEY,
  email varchar(320) NOT NULL,
  newsletter boolean NOT NULL DEFAULT false
);
CREATE TABLE login_protokoll (
  id uuid PRIMARY KEY,
  patient_id uuid REFERENCES patient (id) ON DELETE CASCADE,
  ip_adresse varchar(45),
  user_agent varchar(300)
);
INSERT INTO patient (id, vorname, nachname, email, iban)
VALUES ('8b0c5d4e-0000-4000-8000-000000000001', 'Anna', 'Huber', 'anna_huber_1987@gmail.com', 'DE89047118152468013579');
