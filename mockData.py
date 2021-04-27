#!/bin/python

import os
import sqlite3
from random import randrange, choices

def createDatabase(conn):
    conn.execute("CREATE VIRTUAL TABLE Names USING spellfix1")

    conn.execute('''CREATE TABLE Students(
        id INTEGER PRIMARY KEY,
        idNumber VARCHAR(8) UNIQUE NOT NULL,
        isIntern BOOLEAN NOT NULL,
        inCampus BOOLEAN NOT NULL DEFAULT 1,
        gradeAndSection VARCHAR(255) NOT NULL,
        address VARCHAR(255) NOT NULL
    );''')

    conn.execute('''CREATE TABLE LeavePass(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        studentID INTEGER,
        type CHAR(4) CHECK( type in ("Home", "Gate") ) DEFAULT "Home",
        destination VARCHAR(255) NOT NULL,
        issuedTime DATETIME DEFAULt CURRENT_TIMESTAMP,
        FOREIGN KEY (studentID) REFERENCES Students(id)
    );''')

    conn.execute('''CREATE TABLE Logout(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leavePassID INTEGER UNIQUE NOT NULL,
        timeout DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (leavePassID) REFERENCES LeavePass(ID)
    );''')

    conn.execute('''CREATE TABLE Login(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logID INTEGER UNIQUE NOT NULL,
        timein DATETIME DEFAULT CURRENT_TIMESTAMP,
        remarks INTEGER DEFAULT 0,
        FOREIGN KEY (logID) REFERENCES Logout(id)
    );''')

def populateStudents(conn, n=50):
    fnames = [
        "Paul", "Mark", "Loyd", "Michael", "Carlo",
        "Mark Anthony", "Rey", "Benedict", "Patrick", "Vincent",
        "Joy", "Grace", "Jessa Mae", "Rose", "Angel Mae",
        "Christine Joy", "Mary Jane", "Trisha Mae", "Rose Ann", "Marry Ann"
    ]
    lnames = [
        "Santos", "Reyes", "Cruz", "Bautista", "Ocampo",
        "Garcia", "Mendoza", "Torres", "Tomas", "Andrada",
        "Castillo", "Rivera", "Flores", "Villanueva", "Navarro",
        "Aquino", "Ramos", "Salazar", "Castro", "Mercado"
    ]

    for i in range(n - 1):
        grade = i % 6 + 7
        section = "SECTION" + str(randrange(1,4))

        idNumber = str(27 - grade) + "-"  + str(i + 1).zfill(5)

        gns = str(grade) + "-" + section
        name = lnames[randrange(0, 20)].upper() + ", " + fnames[randrange(0,20)]+" "+str(i+1)
        add = "Municipality" + str(randrange(0, 5)+1) + ", Province" + str(randrange(0, 3)+1)
        conn.execute("INSERT INTO Names(rowid, word) VALUES(?, ?)", (i + 1, name))
        conn.execute('''INSERT INTO Students
            (id, idNumber, isIntern, gradeAndSection, address)
            VALUES (?, ?, ?, ?, ?)''',
            (i + 1, idNumber, randrange(0,2), gns, add)
        )
        conn.commit()

    conn.execute("INSERT INTO Names(rowid, word) VALUES(?, ?)", (n, "BAYOD, Jerico Wayne Y."))
    conn.execute('''INSERT INTO StudentS
        (id, idNumber, isIntern, gradeAndSection, address)
        VALUES(
            ?,
            "15-01296",
            1,
            "11-ERIDANI",
            "Allacapan, Cagayan"
        )
    ''', (n,))


def populateLogs(conn, epochs=10000, n=50):
    outofcampus = set()
    incampus = set(range(n))

    cur = conn.cursor()
    leavePassCtr = 0
    for i in range(epochs):
        if choices((0,1))[0] and len(incampus) or not len(outofcampus):
            # Someone Leaving
            who = choices(tuple(incampus))[0]
            leavePassCtr += 1
            t = choices((0,1))[0] and "Home" or "Gate"
            cur.execute("SELECT address FROM Students WHERE id=?", (who+1,))
            add = t=="Home" and cur.fetchall()[0][0] or "Bayombong, Nueva Viscaya"
            
            # Get LeavePass
            conn.execute('''INSERT INTO LeavePass(studentId, type, destination) VALUES (?, ?, ?)''',
                (who + 1, t, add)
            )
            # Logout
            conn.execute("INSERT INTO Logout(leavePassID) VALUES(?)", (leavePassCtr,))
            # Update stutus
            conn.execute("UPDATE Students SET inCampus=0 WHERE id=?", (who+1,))

            incampus.remove(who)
            outofcampus.add(who)


        else:
            # Someone Returning
            who = choices(tuple(outofcampus))[0]

            # Get Last Logout ID
            sql = '''
                SELECT Logout.ID FROM Students
                INNER JOIN LeavePass ON LeavePass.studentID=Students.id
                INNER JOIN Logout ON Logout.leavePassID=LeavePass.id
                WHERE Students.id=?
                ORDER BY Logout.id DESC LIMIT 1
            '''
            cur.execute(sql, (who+1,))
            logID = cur.fetchall()[0][0]

            # LogIn
            conn.execute("INSERT INTO Login(logID, remarks) VALUES (?,?)",
                (
                    logID,
                    choices((0,110, 210, 211, 221, 222),(80,4,4,4,4,4))[0]
                )
            )
            # Update Status
            conn.execute("UPDATE Students SET inCampus=1 WHERE id=?", (who+1,))

            outofcampus.remove(who)
            incampus.add(who)
    
    if n - 1 in outofcampus:
        sql = '''
            SELECT Logout.ID FROM Students
            INNER JOIN LeavePass ON LeavePass.studentID=Students.id
            INNER JOIN Logout ON Logout.leavePassID=LeavePass.id
            WHERE Students.id=?
            ORDER BY Logout.id DESC LIMIT 1
        '''
        cur.execute(sql, (n,))
        logID = cur.fetchall()[0][0]

        # LogIn
        conn.execute("INSERT INTO Login(logID, remarks) VALUES (?,?)",
            (
                logID,
                choices((0,110, 210, 211, 221, 222),(80,4,4,4,4,4))[0]
            )
        )
        # Update Status
        conn.execute("UPDATE Students SET inCampus=1 WHERE id=?", (n,))
        
           


    conn.commit()


if __name__ == "__main__":
    # Create New DB
    if os.path.exists("picscan.db"):
        os.remove("picscan.db")

    # Connect to DB and load spellfix extension
    conn = sqlite3.connect("picscan.db")
    conn.enable_load_extension(True)
    conn.load_extension("./spellfix.so")

    createDatabase(conn)
    populateStudents(conn)
    populateLogs(conn)

    conn.close()
