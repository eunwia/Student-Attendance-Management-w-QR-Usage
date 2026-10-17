'''
	database helper
'''
from sqlite3 import connect,Row

database:str = 'db/school.db'

def getprocess(sql:str,vals:list)->list:
    print(sql)
    conn:any=connect(database)
    conn.row_factory=Row
    cursor:any=conn.cursor()
    cursor.execute(sql,vals)
    data:list=cursor.fetchall()
    cursor.close()
    conn.close()
    return data
    
def postprocess(sql:str,vals:list)->bool:
    print(sql)
    try:
        conn:any=connect(database)
        cursor:any=conn.cursor()
        cursor.execute(sql,vals)
        conn.commit()
    except Exception as e:
        print(f"Error : {e}")
    finally:
        cursor.close()
        conn.close()
        return True if cursor.rowcount>0 else False
    
def getall(table:str)->list:
    sql:str = f"SELECT * FROM `{table}`"
    return getprocess(sql,[])
    
def getrecord(table:str,**kwargs)->list:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    fields:list = []
    for key in keys:
        fields.append(f"`{key}`=?")
    flds:str = " AND ".join(fields)
    sql:str = f"SELECT * FROM `{table}` WHERE {flds}"
    return getprocess(sql,vals)
    
def addrecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    fields:str = "`,`".join(keys)
    qmark:list=['?']*len(vals)
    dta:str = ",".join(qmark)
    sql:str = f"INSERT INTO `{table}`(`{fields}`) VALUES({dta})"
    return postprocess(sql,vals)
    
def deleterecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    fields:list = []
    for key in keys:
        fields.append(f"`{key}`=?")
    flds:str = " AND ".join(fields)
    sql:str = f"DELETE FROM `{table}` WHERE {flds}"
    return postprocess(sql,vals)
    
def updaterecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    newvals:list = []
    fields:list = []
    for index in range(1,len(keys)):
        fields.append(f"`{keys[index]}`=?")
        newvals.append(f"{vals[index]}")
    flds:str = ",".join(fields)
    sql:str = f"UPDATE `{table}` SET {flds} WHERE `{keys[0]}`='{vals[0]}'"
    return postprocess(sql,newvals)