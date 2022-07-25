from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import requests
import datetime
import eyed3
from multiprocessing import Process
import time
import random
import os
import signal
import mutagen
import sentry_sdk

#spinitron data
spinitron_url = "https://spinitron.com/api/spin/create-v1"
spinitron_token = "EutJCHDPYQ_vCbquLgm_K8Uq"


sentry_sdk.init(
    "https://d8d17174438449c29176c094f748f96a@o116363.ingest.sentry.io/5511662",
    traces_sample_rate=1.0
)

# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = False
)
connection = sql_alchemy_engine.connect()
sql = """SELECT * from playlists where time='2020-11-13 10:30' LIMIT 1"""
playlist = connection.execute(prepare(sql))
for p in playlist:
    newshow = True
    with open('C:\\Playlists\\'+p['location'],encoding='utf-8') as r:
        for line in r:
            if line[0:1]!='#':
                filename = line[11:]
                filename = filename.replace('/','\\')
                filename = filename.rstrip()
                print(filename)
