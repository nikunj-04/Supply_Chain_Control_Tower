import os
import sqlite3

path = './data/tms.db'
print('exists', os.path.exists(path))
print('abs', os.path.abspath(path))
conn = sqlite3.connect(path)
print(conn.execute("select name from sqlite_master where type='table'").fetchall())
conn.close()
