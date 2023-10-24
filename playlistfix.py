#A program that will fix a playlist file. We changed all the locations of every artist folder to a subfolder of the first letter of the artist's name.
from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import re
import os

sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = False
)
connection = sql_alchemy_engine.connect()

for file in os.listdir('/Playlists'):
    o = open('/Playlists/' + file, 'r')
    newfile = []
    for line in o:
        if line[0] == '#':
            newfile.append(line)
        else:
            if line[0:19] == '/mnt/share/library/':
                song = '%' + line[19:-1]
                sql = "SELECT location FROM songs WHERE location LIKE :song"
                result = connection.execute(prepare(sql), song=song)
                for row in result:
                    print(row['location'][84:])
                    if re.match('[A-Za-z]',row['location'][84]):
                        newfile.append('/mnt/share/library/' + row['location'][84] + '/' + row['location'][84:])
                    else:
                        newfile.append('/mnt/share/library/0-9/' + row['location'][84:])
            else:
                newfile.append(line)
    o.close()
    print(newfile)
    o = open('/Playlists/' + file, 'w')
    o.write('\n'.join(newfile))
    o.close()