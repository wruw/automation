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
import redis
import subprocess

#spinitron data
spinitron_url = "https://spinitron.com/api/spin/create-v1"
spinitron_token = "ADD SPINITRON TOKEN HERE"


sentry_sdk.init(
    "ADD SENTRY DOMAIN HERE",
    traces_sample_rate=1.0
)

# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

r = redis.Redis(host='localhost',port=6379,db=0)

#what should play wben

announcements = {
    '0000':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0030':['LegalIDs','SafeHarbor','Telethon'],
    '0100':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0130':['LegalIDs','SafeHarbor'],
    '0200':['start','LegalIDs','PSA','Promos','SafeHarbor'],
    '0230':['LegalIDs','SafeHarbor'],
    '0300':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0330':['LegalIDs','SafeHarbor'],
    '0400':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0430':['LegalIDs','SafeHarbor'],
    '0500':['LegalIDs','PSA','Promos','SafeHarbor','LPT'],
    '0530':['LegalIDs','SafeHarbor'],
    '0600':['LegalIDs','PSA','Promos'],
    '0630':['LegalIDs'],
    '0700':['LegalIDs','PSA','Promos'],
    '0730':['LegalIDs'],
    '0800':['LegalIDs','PSA','Promos'],
    '0830':['LegalIDs'],
    '0900':['LegalIDs','PSA','Promos'],
    '0930':['LegalIDs'],
    '1000':['LegalIDs','PSA','Promos'],
    '1030':['LegalIDs'],
    '1100':['LegalIDs','PSA','Promos'],
    '1130':['LegalIDs'],
    '1200':['LegalIDs','PSA','Promos'],
    '1230':['LegalIDs'],
    '1300':['LegalIDs','PSA','Promos'],
    '1330':['LegalIDs'],
    '1400':['LegalIDs','PSA','Promos'],
    '1430':['LegalIDs'],
    '1500':['LegalIDs','PSA','Promos'],
    '1530':['LegalIDs'],
    '1600':['LegalIDs','PSA','Promos','LPT'],
    '1630':['LegalIDs'],
    '1700':['LegalIDs','PSA','Promos'],
    '1730':['LegalIDs'],
    '1800':['LegalIDs','PSA','Promos'],
    '1830':['LegalIDs'],
    '1900':['LegalIDs','PSA','Promos'],
    '1930':['LegalIDs'],
    '2000':['LegalIDs','PSA','Promos'],
    '2030':['LegalIDs'],
    '2100':['LegalIDs','PSA','Promos','LPT'],
    '2130':['LegalIDs'],
    '2200':['LegalIDs','PSA','Promos','SafeHarbor'],
    '2230':['LegalIDs','SafeHarbor'],
    '2300':['LegalIDs','PSA','Promos','SafeHarbor'],
    '2330':['LegalIDs','SafeHarbor'],
}

#the actual player
def playsong(file):
    try:
        with open('C:\\automation\\filename.txt','w') as f:
            f.write(file)
        subprocess.call(['powershell.exe','. .\\playshit.ps1'])
    except Exception as e:
         print(e)

def getlength(file):
    m = mutagen.File(file)
    return m.info.length

def log(text):
    print(text)
    try:
        s = Process(target=logsql, args = (text,))
        s.start()
    except:
        pass

def logsql(text):
    connection = sql_alchemy_engine.connect()
    sql = """INSERT INTO logs (text)
        VALUES (:text)"""
    connection.execute(prepare(sql),{'text':text})

#like a stack, adds to the front
def addtofront(file,override):
    log('adding {} to front'.format(file))
    connection = sql_alchemy_engine.connect()
    sql = """UPDATE queue SET queue=queue+1"""
    connection.execute(prepare(sql))
    sql = """INSERT INTO queue (queue, file, override) VALUES
        (1, :file, :override)
        """
    connection.execute(prepare(sql),{'file':file, 'override':override})

def checkduplicates(file):
    exists = r.get(file)
    if exists:
        return False
    r.set(file,'true',ex=60*60*24)
    try:
        eyed3file = eyed3.load(file)
        artist = eyed3file.tag.artist.lower()
        exists = r.get(artist)
        if exists:
            return False
        r.set(artist,'true',ex=60*60*2)
        song = eyed3file.tag.title.lower()
        exists = r.get(song)
        if exists:
            return False
        r.set(song,'true',ex=60*60*2)
    except:
        pass
    return True

#like a queue, adds to the back
def addtoback(file,override):
    log('adding {} to back'.format(file))
    connection = sql_alchemy_engine.connect()
    sql = """SELECT MAX(queue) AS m FROM queue"""
    m = connection.execute(prepare(sql)).fetchone()['m']
    if not m:
        m=0
    sql = """INSERT INTO queue (queue, file, override) VALUES
        (:m, :file, :override)
        """
    connection.execute(prepare(sql),{'file':file,'m':int(m)+1,'override':override})

def empty():
    connection = sql_alchemy_engine.connect()
    sql = """DELETE FROM queue"""
    connection.execute(prepare(sql))

#for the player, grabs the next file
def getnext():  
    connection = sql_alchemy_engine.connect()
    sql = """SELECT file, override FROM queue WHERE
        queue = 1 LIMIT 1"""
    file = connection.execute(prepare(sql))
    for f in file:
        sql = """DELETE FROM queue WHERE queue=1"""
        connection.execute(prepare(sql))
        sql = """UPDATE queue SET queue=queue-1"""
        connection.execute(prepare(sql))
        return f
    return False

def setoverride(override):
    connection = sql_alchemy_engine.connect()
    sql = """UPDATE override SET status=:override"""
    connection.execute(prepare(sql),{'override':override})

def getoverride():
    connection = sql_alchemy_engine.connect()
    sql = """SELECT status FROM override"""
    result = connection.execute(prepare(sql)).fetchone()
    return result['status']

#this submits to spinitron what is playing on a different thread
def submit(file):
    eyed3file = eyed3.load(file.strip())
    data = {}
    try:
        data['sd'] = getlength(file.strip())
    except:
        pass
    try:
        data['aw'] = eyed3file.tag.artist
    except:
        pass
    try:
        data['sn'] = eyed3file.tag.title
    except:
        pass
    try:
        data['dr'] = eyed3file.tag.best_release_date
    except:
        pass
    try:
        data['dn'] = eyed3file.tag.album
    except:
        pass
    data['access-token'] = spinitron_token
    r = requests.get(spinitron_url, params=data)

def addlegalstuff(time,location,override=False):

    timetolookup = "{:02d}".format(time.hour)+"{:02d}".format(time.minute)
    stufftoplay = announcements[timetolookup]
    for item in reversed(stufftoplay):
        folder = "C:\\Productions\\{}".format(item)
        file = "{}\\{}".format(folder,random.choice(os.listdir(folder)))
        log('adding {} as {} to {}'.format(file,item,location))
        if override:
            o=1
        else:
            o=0
        if location=='back':
            addtoback(file,o)
        elif location=='front':
            addtofront(file,o)

def player():
    connection = sql_alchemy_engine.connect()
    while True:
        #grab the next thing from the queue to play.
        nextfile = getnext()
        if nextfile:
            #submit to spinitron
            s = Process(target=submit, args = (nextfile['file'],))
            s.start()
            if nextfile['override'] == 1:
                setoverride(1)
            else:
                setoverride(0)
            log('playing {} from queue'.format(nextfile['file']))
            playsong(nextfile['file'])
        #nothing else to play, grab something from the database
        else:
            setoverride(0)
            foundrotation = False
            #first look for a rotation to play
            now = datetime.datetime.now()
            dow = now.weekday()
            time = "{:02d}".format(now.hour)+"{:02d}".format(now.minute)
            sql = """SELECT id FROM rotations WHERE day = :dow
                AND starttime < :time AND endtime > :time
                LIMIT 1"""
            result = connection.execute(prepare(sql),{'dow':dow,'time':time})
            for row in result:
                foundrotation = True
                duplicate = True
                count = 0
                #a show is found, now find a song to play
                #find not a duplicate
                sql = """SELECT location from songs
                    INNER JOIN songs_rotations
                    ON songs_rotations.song_id = songs.id
                    AND songs_rotations.rotation_id = :rid
                    ORDER BY RAND() LIMIT 1"""
                while duplicate:
                    result2 = connection.execute(prepare(sql),{'rid':row['id']})
                    for row2 in result2:
                        if checkduplicates(row2['location']) or count > 5:
                            duplicate=False
                            s = Process(target=submit, args = (row2['location'],))
                            s.start()
                            log('playing {} from rotation'.format(row2['location']))
                            playsong(row2['location'])
                        else:
                            count = count + 1
            if not foundrotation:
                #nothing is found, just grab something
                #first, is it safe harbor?
                if int(time) < 600 or int(time) > 2200:
                    SafeHarbor = 1
                else:
                    SafeHarbor = 0
                #grab a song to play
                sql = """SELECT location FROM songs
                    """
                if not SafeHarbor:
                    sql+="""WHERE clean = 1 AND location not like '%---fcc---%'
                    """
                sql+="""ORDER BY RAND() LIMIT 1"""
                duplicate = True
                count = 0
                while duplicate:
                    result = connection.execute(prepare(sql))
                    for row in result:
                        if checkduplicates(row['location']) or count > 5:
                            duplicate=False
                            s = Process(target=submit, args = (row['location'],))
                            s.start()
                            log('playing {} from random'.format(row['location']))
                            playsong(row['location'])
                        else:
                            count = count + 1

if __name__ == "__main__":
    p = Process(target=player)
    p.start()
    while True:
        connection = sql_alchemy_engine.connect()
        try:
            #find the next file to play
            currenttime = datetime.datetime.now()
            nexttime = currenttime + (datetime.datetime.min - currenttime) % datetime.timedelta(minutes=30)
            log('sleeping for {} seconds'.format(nexttime.timestamp()-currenttime.timestamp()))
            time.sleep(int(nexttime.timestamp()-currenttime.timestamp()))
            newshow = False
            #Democracy now hack
            if nexttime.hour == 16 and nexttime.minute == 00 and nexttime.weekday() < 5:
                newshow = True
                empty()
                addtoback('C:\\productions\\Show Specific\\Democracy Now Show Intro.mp3',1)
                addtoback('C:\Recordings\dn.mp3',1)
            #first look in recordings
            if not newshow:
                sql = """SELECT * FROM recordings WHERE time=:nexttime LIMIT 1"""
                recording = connection.execute(prepare(sql),{'nexttime':nexttime})
                for r in recording:
                    file = 'C:\\Recordings\\'+r['file1']
                    newshow = True
                    empty()
                    addtoback(file,1)
                    if getlength(file) > 15*60:
                        length1 = round(getlength(file)/60/60)
                        addlegalstuff(nexttime+datetime.timedelta(hours=length1),'back',True)
                    if r['file2']:
                        file = 'C:\\Recordings\\'+r['file2']
                        addtoback(file,1)
                        if getlength(file) > 15*60:
                            length2 = round(getlength(file)/60/60)
                            addlegalstuff(nexttime+datetime.timedelta(hours=length1+length2),'back',True)
            if not newshow:
                sql = """SELECT * from playlists where time=:nexttime LIMIT 1"""
                playlist = connection.execute(prepare(sql),{'nexttime':nexttime})
                for p in playlist:
                    newshow = True
                    empty()
                    with open('C:\\Playlists\\'+p['location'],encoding='utf-8') as r:
                        for line in r:
                            if line[0:1]!='#':
                                if line[0:11] == '/mnt/share/':
                                    l = line[11:]
                                    l = 'M:\\'+l.replace('/','\\')
                                    addtoback(l,0)
                                else:
                                    l = line[15:]
                                    l = 'D:\\nextcloud\\'+l.replace('/','\\')
                                    addtoback(l,0)
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
            if getoverride()==0 or newshow:
                addlegalstuff(nexttime,'front')
            if newshow:
                os.kill(os.getpid(),signal.CTRL_C_EVENT)
            time.sleep(60)
        except Exception as e:
            sentry_sdk.capture_exception(e)
