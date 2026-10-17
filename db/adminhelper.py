from sqlite3 import connect, Row

database = "db/school.db"  

def getrecord(table: str, **kwargs):
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    fields = [f"`{k}`=?" for k in keys]
    flds = " AND ".join(fields)
    sql = f"SELECT * FROM `{table}` WHERE {flds}"

    conn = connect(database)
    conn.row_factory = Row
    cur = conn.cursor()
    cur.execute(sql, vals)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def getall(table: str):
    sql = f"SELECT * FROM `{table}`"
    conn = connect(database)
    conn.row_factory = Row
    cur = conn.cursor()
    cur.execute(sql)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def addrecord(table: str, **kwargs):
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    fields = "`,`".join(keys)
    qmark = ['?'] * len(vals)
    dta = ",".join(qmark)
    sql = f"INSERT INTO `{table}`(`{fields}`) VALUES({dta})"
    
    conn = connect(database)
    cur = conn.cursor()
    cur.execute(sql, vals)
    conn.commit()
    cur.close()
    conn.close()
    return True
