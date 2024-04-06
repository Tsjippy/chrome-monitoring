DROP TABLE IF EXISTS "Limits";
DROP TABLE IF EXISTS "History";
DROP TABLE IF EXISTS "Settings";

CREATE TABLE "Limits"(
	"id" 			INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user" 			TEXT,
	"url" 			TEXT,
	"limit" 		INTEGER
);

CREATE TABLE "History"(
	"id" 			INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user" 			TEXT,
	"url" 			TEXT,
	"date"			TEXT,
	"time" 			TEXT,
	"time_spent" 	INTEGER
);

CREATE TABLE "Settings"(
	"id" 				INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"key"				TEXT,
	"value"				TEXT
);

INSERT INTO Settings ('key', 'value') VALUES('default', 30);
INSERT INTO Settings ('key', 'value') VALUES('total', 120);