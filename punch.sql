CREATE TABLE employee (
    employeeId INTEGER PRIMARY KEY AUTOINCREMENT,
    accessCode TEXT
    employeeName TEXT
);

CREATE TABLE card (
    cardId INTEGER PRIMARY KEY AUTOINCREMENT,
    employeeId INTEGER,
    punchIn TEXT,
    punchOut TEXT
);
