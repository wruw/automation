from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import os

sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

connection = sql_alchemy_engine.connect()
#playlists
sql = """SELECT * FROM playlists WHERE time < subdate(current_date,1)"""
results = connection.execute(prepare(sql))
for row in result:
    os.remove(os.path.join('C:\Playlists',row['location']))
    sql = """DELETE FROM playlists WHERE id=:id"""
    connection.execute(prepare(sql),{'id':row['id']})

sql = """SELECT * FROM recordings WHERE time < subdate(current_date,1)"""
results = connection.execute(prepare(sql))
for row in result:
    os.remove(os.path.join('C:\Recordings',row['location']))
    sql = """DELETE FROM recordings WHERE id=:id"""
    connection.execute(prepare(sql),{'id':row['id']})
