import sqlite3

db = sqlite3.connect("test.db")
cur = db.cursor()

cur.execute("CREATE TABLE if not exists t (b BLOB);")

with open("0.bin", "rb") as f:
    for i in range(10000):
        cur.execute("insert into t values(?)", (sqlite3.Binary(f.read()),))
    db.commit()

cur.execute("select b from t limit 1")
b = cur.fetchone()[0]

with open("00.bin", "wb") as f:
    f.write(b)

db.close()
