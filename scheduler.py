from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import datetime
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

r = redis.Redis()


while True:
    #find the next file to play
    currenttime = datetime.datetime.now()
    nexttime = currenttime + (datetime.datetime.min - currenttime) % datetime.timedelta(minutes=15)
    sql_alchemy_engine = create_engine(
        'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
        pool_recycle = 3600,
        echo = True
    )
    log('sleeping for {} seconds'.format(nexttime.timestamp()-currenttime.timestamp()),sql_alchemy_engine)
    time.sleep(int(nexttime.timestamp()-currenttime.timestamp()))
    connection = sql_alchemy_engine.connect()
    newshow = False
    #Democracy now hack
    if nexttime.hour == 16 and nexttime.minute == 0 and nexttime.weekday() < 5:
        newshow = True
        addtoback('/Productions/Show Specific/Democracy Now Show Intro.mp3',1,sql_alchemy_engine)
        addtoback('/Recordings/dn.mp3',1,sql_alchemy_engine)
    #first look in recordings
    if not newshow:
        sql = """SELECT * FROM recordings WHERE time=:nexttime LIMIT 1"""
        recording = connection.execute(prepare(sql),{'nexttime':nexttime})
        if recording:
            for r in recording:
                file = '/Recordings/'+r['file1']
                newshow = True
                empty(sql_alchemy_engine)
                addtoback(file,1,sql_alchemy_engine)
                if getlength(file) > 15*60:
                    length1 = round(getlength(file)/60/60)
                    addlegalstuff(nexttime+datetime.timedelta(hours=length1),'back',sql_alchemy_engine,True)
                if r['file2']:
                    file = '/Recordings/'+r['file2']
                    addtoback(file,1,sql_alchemy_engine)
                    if getlength(file) > 15*60:
                        length2 = round(getlength(file)/60/60)
                        addlegalstuff(nexttime+datetime.timedelta(hours=length1+length2),'back',sql_alchemy_engine,True)
    if not newshow:
        sql = """SELECT * from playlists where time=:nexttime LIMIT 1"""
        playlist = connection.execute(prepare(sql),{'nexttime':nexttime})
        for p in playlist:
            newshow = True
            empty(sql_alchemy_engine)
            with open('/Playlists/'+p['location'],encoding='utf-8') as r:
                for line in r:
                    if line[0:1]!='#':
                        if line[0:11] == '/mnt/share/':
                            l = line[11:]
                            l = '/run/user/1000/gvfs/smb-share:server=ads.case.edu,share=utech/Shares/WRUW/'+l
                            addtoback(l,0,sql_alchemy_engine)
                        else:
                            l = line[15:]
                            l = '/run/user/1000/gvfs/smb-share:server=wruw-storage1,share=automation/'+l
                            addtoback(l,0,sql_alchemy_engine)
    #see if there's a new rotation
    if not newshow:
        now = datetime.datetime.now()
        dow = now.weekday()
        timer = "{:02d}".format(now.hour)+"{:02d}".format(now.minute)
        timer = round(int(timer)/10)*10
        sql = """SELECT COUNT(1) c FROM rotations WHERE day = :dow
            AND starttime = :time"""
        result = connection.execute(prepare(sql),{'dow':dow,'time':timer}).fetchone()
        if result['c'] > 0:
            newshow = True
            empty(sql_alchemy_engine)
    if getoverride(sql_alchemy_engine)==0 or newshow:
        addlegalstuff(nexttime,'front',sql_alchemy_engine)
    if newshow:
        terminal(['audtool','--playlist-clear'])
        findsong(sql_alchemy_engine)
        terminal(['audtool','--playback-play'])
    connection.close()
    time.sleep(60)
    """except Exception as e:
        sentry_sdk.capture_exception(e)"""
