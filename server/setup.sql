DROP TABLE IF EXISTS "Limits";
DROP TABLE IF EXISTS "History";
DROP TABLE IF EXISTS "Settings";

CREATE TABLE "Limits"(
	"id" 			INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"url" 			TEXT,
	"limit" 		INTEGER
);

CREATE TABLE "History"(
	"id" 			INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
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

INSERT INTO Limits ('url', 'limit') VALUES('default', 30);
INSERT INTO Limits ('url', 'limit') VALUES('total', 120);