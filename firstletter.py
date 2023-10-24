#We changed all the locations of every artist folder to a subfolder of the first letter of the artist's name. This fixes the database.
from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import re

sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = False
)

connection = sql_alchemy_engine.connect()
sql = "SELECT MAX(id) m from songs"
result = connection.execute(sql).fetchone()['m']
for row in range(0,result):
    sql2 = "SELECT * FROM songs where id = :id"
    result2 = connection.execute(prepare(sql2), id=row)
    for row2 in result2:
        song = row2['location']
        print(song[82])
        if song[0:82] == '/run/user/1000/gvfs/smb-share:server=ads.case.edu,share=utech/Shares/WRUW/library/':
            if re.match('[A-Za-z]',song[82]):
                song = song[0:82] + song[82] + '/' + song[82:]
            else:
                song = song[0:82] + '0-9/' + song[82:]
        sql = "UPDATE songs SET location = :song WHERE id = :id"
        connection.execute(prepare(sql), song=song, id=row2['id'])