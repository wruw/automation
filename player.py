from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import time
import sentry_sdk
import redis
from common import *

#spinitron data
spinitron_url = "https://spinitron.com/api/spin/create-v1"
spinitron_token = "EutJCHDPYQ_vCbquLgm_K8Uq"


sentry_sdk.init(
    "https://d8d17174438449c29176c094f748f96a@o116363.ingest.sentry.io/5511662",
    traces_sample_rate=1.0
)

# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

r = redis.Redis()

terminal(['audtool', '--playlist-clear'])
while True:
    #check if the player is either stopped or near the end of the playlist/song
    needsong = False
    status = terminal(['audtool', '--playback-status'])
    if status == 'stopped':
        needsong = True
        terminal(['audtool', '--playlist-clear'])
    else:
        playlistlength = terminal(['audtool', '--playlist-length'])
        currentspot = terminal(['audtool', '--playlist-position'])
        if currentspot == playlistlength:
            songlength = terminal(['audtool', '--current-song-length-seconds'])
            currentspot = terminal(['audtool', '--current-song-output-length-seconds'])
            if songlength - currentspot < 20:
                needsong = True
    if needsong:
        findsong(sql_alchemy_engine)
    if status == 'stopped':
        terminal(['audtool', '--playback-play'])
    time.sleep(10)

