CREATE TABLE USER (
    ID              INTEGER     UNIQUE          PRIMARY KEY     AUTOINCREMENT   NOT NULL,
    USERNAME        TEXT                                                        NOT NULL,
    PASSWORD        TEXT                                                        NOT NULL,
    EMAIL           TEXT                                                        NOT NULL,
    AUTHENTICATED   INT                                                         NOT NULL,
    ACTIVE          INT                                                         NOT NULL
);
CREATE TABLE PAGE (
    ID              INTEGER     UNIQUE          PRIMARY KEY     AUTOINCREMENT   NOT NULL,
    URI             TEXT        UNIQUE                                          NOT NULL,
    TITLE           TEXT                                                        NOT NULL,
    CONTENT         BLOB                                                        NOT NULL,
    DATE_CREATED    TEXT                                                        NOT NULL,
    LAST_EDITED     TEXT                                                        NOT NULL
);
CREATE TABLE TAG (
    ID              INTEGER     UNIQUE          PRIMARY KEY     AUTOINCREMENT   NOT NULL,
    NAME            TEXT                                                        NOT NULL
);
CREATE TABLE CATEGORY (
    ID              INTEGER     UNIQUE          PRIMARY KEY     AUTOINCREMENT   NOT NULL,
    NAME            TEXT                                                        NOT NULL
);
-- A JOIN table responsible for storing the relation between a page and its many tags
CREATE TABLE PAGE_TAGS (
    PAGE_ID         INTEGER,
    TAG_ID          INTEGER,
    FOREIGN KEY (PAGE_ID)   REFERENCES PAGE(ID),
    FOREIGN KEY (TAG_ID)    REFERENCES PAGE(ID)
);
--
