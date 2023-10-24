from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import os
import datetime

sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

connection = sql_alchemy_engine.connect()
#playlists
sql = """DELETE FROM playlists WHERE time < subdate(current_date,1)"""
connection.execute(prepare(sql))
sql = """DELETE FROM recordings WHERE time < subdate(current_date,1)"""
connection.execute(prepare(sql))

today = datetime.datetime.now()

playlists = os.listdir('/Playlists')
for playlist in playlists:
    try:
        playlistdate = datetime.datetime.strptime(playlist[:10],'%m-%d-%Y')
        if today - playlistdate > datetime.timedelta(days=2):
            os.remove(os.path.join('/Playlists',playlist))
    except:
        pass

recordings = os.listdir('/Recordings')
for recording in recordings:
    try:
        recordingdate = datetime.datetime.strptime(recording[:10],'%m-%d-%Y')
        if today - recordingdate > datetime.timedelta(days=2):
            os.remove(os.path.join('/Recordings',recording))
    except:
        pass
