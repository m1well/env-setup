CREATE TABLE app_user (
    id       uuid        PRIMARY KEY,
    username varchar(60) NOT NULL UNIQUE
);

CREATE TABLE project (
    id          uuid         PRIMARY KEY,
    owner_id    uuid         NOT NULL REFERENCES app_user (id),
    customer_id uuid,
    name        varchar(100) NOT NULL,
    -- the comparison in the CHECK must not swallow the next column into this one
    budget      integer      CHECK (budget > 0),
    lead_id     uuid         REFERENCES app_user (id),
    UNIQUE (owner_id, name)
);

CREATE TABLE project_member (
    id         uuid        PRIMARY KEY,
    project_id uuid        NOT NULL REFERENCES project (id),
    username   varchar(60) NOT NULL,
    UNIQUE (project_id, username)
);

CREATE TABLE team_member (
    id   uuid         PRIMARY KEY,
    name varchar(100) NOT NULL
);

CREATE TABLE document (
    id          uuid         PRIMARY KEY,
    project_id  uuid         NOT NULL REFERENCES project (id),
    owner_id    uuid         NOT NULL REFERENCES app_user (id),
    customer_id uuid,
    title       varchar(200) NOT NULL,
    version     varchar(36)  NOT NULL,
    lock        bigint       NOT NULL
);
CREATE INDEX document_project ON document (project_id);
CREATE INDEX document_owner ON document (owner_id, title);

CREATE TABLE invite (
    id         uuid        PRIMARY KEY,
    project_id uuid        NOT NULL REFERENCES project (id),
    token      varchar(36) NOT NULL
);
CREATE INDEX invite_project ON invite (project_id);

CREATE TABLE report (
    id         uuid         PRIMARY KEY,
    owner_name varchar(60)  NOT NULL,
    title      varchar(200) NOT NULL
);
