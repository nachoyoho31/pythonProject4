# подключаем SQLite
import sqlite3 as sl
# открываем файл с базой данных
con = sl.connect('statistic.db')
with con:
    con.execute("""
        CREATE TABLE skins (
           name STRING,
           price INTEGER,
           own INTEGER,
           equip INTEGER
           

);
    """)