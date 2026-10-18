CREATE TABLE tenant (id uuid PRIMARY KEY, name text NOT NULL);

CREATE TABLE project (
    id        uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    name      text NOT NULL
);
ALTER TABLE project ENABLE ROW LEVEL SECURITY;
ALTER TABLE project FORCE ROW LEVEL SECURITY;
CREATE POLICY project_tenant ON project USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE TABLE task (
    id         uuid PRIMARY KEY,
    tenant_id  uuid NOT NULL REFERENCES tenant (id),
    project_id uuid NOT NULL REFERENCES project (id),
    title      text NOT NULL
);
ALTER TABLE task ENABLE ROW LEVEL SECURITY;
CREATE POLICY task_tenant ON task USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE TABLE invoice (
    id        uuid PRIMARY KEY,
    tenant_id uuid REFERENCES tenant (id),
    number    text NOT NULL,
    UNIQUE (number)
);

-- Without RLS on purpose: the platform admin reads every tenant's entries.
CREATE TABLE audit_entry (
    id        uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    action    text NOT NULL
);
