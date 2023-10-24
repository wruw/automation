#A lot of files got duplicated in the database, this script removes the duplicates and cleans up the database
from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import os

sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

connection = sql_alchemy_engine.connect()
sql = "SELECT MAX(id) m from songs"
result = connection.execute(sql).fetchone()['m']
for row in range(0,result):
    sql2 = "SELECT * FROM songs where id = :id"
    result2 = connection.execute(prepare(sql2), id=row)
    for row2 in result2:
        sql3 = "SELECT * FROM songs where location = :location AND id > :id"
        result3 = connection.execute(prepare(sql3), location=row2['location'], id=row2['id'])
        these = []
        for row3 in result3:
            these.append(str(row3['id']))
        if len(these) > 0:
            sql4 = "UPDATE songs_rotations SET song_id = :song_id WHERE song_id in ('{}')".format("','".join(these))
            connection.execute(prepare(sql4), song_id = row2['id'])
            sql4 = "DELETE FROM songs WHERE id in ('{}')".format("','".join(these))
            connection.execute(prepare(sql4))


sql = "SELECT MAX(id) m from songs_rotations"
result = connection.execute(sql).fetchone()['m']
for row in range(0, result):
    sql2 = "SELECT * FROM songs_rotations where id = :id"
    result2 = connection.execute(prepare(sql2), id=row)
    for row2 in result2:
        sql3 = "DELETE FROM songs_rotations where song_id = :song_id AND rotation_id = :rotation_id AND id > :id"
        connection.execute(prepare(sql3), song_id=row2['song_id'], id=row2['id'], rotation_id=row2['rotation_id'])

sql = "SELECT id, location FROM songs"
result = connection.execute(sql)
for row in result:
    if not os.path.isfile(row['location']):
        sql2 = "DELETE FROM songs WHERE location = :location"
        connection.execute(prepare(sql2), location=row['location'])
        sql2 = "DELETE FROM songs_rotations WHERE song_id = :id"
        connection.execute(prepare(sql2), id=row['id']) 
sql = "SELECT * FROM rotations"
result = connection.execute(sql)
for row in result:
    sql2 = "SELECT COUNT(1) c FROM songs_rotations WHERE rotation_id = :id"
    result2 = connection.execute(prepare(sql2), id=row['id']).fetchone()['c']
    if result2 == 0:
        sql2 = "DELETE FROM rotations WHERE id = :id"
        connection.execute(prepare(sql2), id=row['id'])



connection.close()
