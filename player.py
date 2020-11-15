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
spinitron_token = ""


sentry_sdk.init(
    "",
    traces_sample_rate=1.0
)

# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

#what should play wben

announcements = {
    '0000':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0030':['LegalIDs','SafeHarbor'],
    '0100':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0130':['LegalIDs','SafeHarbor'],
    '0200':['start','LegalIDs','PSA','Promos','SafeHarbor'],
    '0230':['LegalIDs','SafeHarbor'],
    '0300':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0330':['LegalIDs','SafeHarbor'],
    '0400':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0430':['LegalIDs','SafeHarbor'],
    '0500':['LegalIDs','PSA','Promos','SafeHarbor'],
    '0530':['LegalIDs','SafeHarbor'],
    '0600':['LegalIDs','PSA','Promos'],
    '0630':['LegalIDs'],
    '0700':['LegalIDs','PSA','Promos','LPT'],
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
    '1600':['LegalIDs','PSA','Promos'],
    '1630':['LegalIDs'],
    '1700':['LegalIDs','PSA','Promos'],
    '1730':['LegalIDs'],
    '1800':['LegalIDs','PSA','Promos','LPT'],
    '1830':['LegalIDs'],
    '1900':['LegalIDs','PSA','Promos'],
    '1930':['LegalIDs'],
    '2000':['LegalIDs','PSA','Promos'],
    '2030':['LegalIDs'],
    '2100':['LegalIDs','PSA','Promos'],
    '2130':['LegalIDs'],
    '2200':['LegalIDs','PSA','Promos','SafeHarbor'],
    '2230':['LegalIDs','SafeHarbor'],
    '2300':['LegalIDs','PSA','Promos','SafeHarbor','LPT'],
    '2330':['LegalIDs','SafeHarbor'],
}

#the actual player
def playsong(file):
    try:
        os.system('cmd /c "ffplay -autoexit -loglevel quiet \"{}\""'.format(file))
    except:
        pass

def getlength(file):
    m = mutagen.File(file)
    return m.info.length

#like a stack, adds to the front
def addtofront(file,override):
    print('adding {} to front'.format(file))
    connection = sql_alchemy_engine.connect()
    sql = """UPDATE queue SET queue=queue+1"""
    connection.execute(prepare(sql))
    sql = """INSERT INTO queue (queue, file, override) VALUES
        (1, :file, :override)
        """
    connection.execute(prepare(sql),{'file':file, 'override':override})

#like a queue, adds to the back
def addtoback(file,override):
    print('adding {} to back'.format(file))
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
    eyed3file = eyed3.load(file)
    data = {}
    try:
        data['sd'] = getlength(file)
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
        data['dr'] = eyed3file.tag.original_release_date
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
        print('adding {} as {} to {}'.format(file,item,location))
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
            print('playing {} from queue'.format(nextfile['file']))
            playsong(nextfile['file'])
        #nothing else to play, grab something from the database
        else:
            setoverride(0)
            #first look for a rotation to play
            now = datetime.datetime.now()
            dow = now.weekday()
            time = "{:02d}".format(now.hour)+"{:02d}".format(now.minute)
            sql = """SELECT id FROM rotations WHERE day = :dow
                AND starttime < :time AND endtime > :time
                LIMIT 1"""
            result = connection.execute(prepare(sql),{'dow':dow,'time':time})
            for row in result:
                #a show is found, now find a song to play
                sql = """SELECT location from songs
                    INNER JOIN songs_rotations
                    ON songs_rotations.song_id = songs.id
                    AND songs_rotations.rotation_id = :rid
                    ORDER BY RAND() LIMIT 1"""
                result2 = connection.execute(prepare(sql),{'rid':row['id']})
                for row2 in result2:
                    s = Process(target=submit, args = (row2['file'],))
                    s.start()
                    print('playing {} from rotation'.format(row2['file']))
                    playsong(row2['file'])
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
                sql+="""WHERE clean = 1
                """
            sql+="""ORDER BY RAND() LIMIT 1"""
            result = connection.execute(prepare(sql))
            for row in result:
                s = Process(target=submit, args = (row['location'],))
                s.start()
                print('playing {} from random'.format(row['location']))
                playsong(row['location'])

if __name__ == "__main__":
    p = Process(target=player)
    p.start()
    connection = sql_alchemy_engine.connect()
    while True:
        try:
            #find the next file to play
            currenttime = datetime.datetime.now()
            nexttime = currenttime + (datetime.datetime.min - currenttime) % datetime.timedelta(minutes=30)
            print('sleeping for {} seconds'.format(nexttime.timestamp()-currenttime.timestamp()))
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
                    length1 = round(getlength(file)/60/60)
                    addlegalstuff(nexttime+datetime.timedelta(hours=length),'back',True)
                    if r['file2']:
                        file = 'C:\\Recordings\\'+r['file2']
                        addtoback(file,1)
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
                                filename = line[11:]
                                filename = filename.replace('/','\\')
                                filename = filename.rstrip()
                                addtoback('M:\\'+filename,0)
            #see if there's a new rotation
            if not newshow:
                now = datetime.datetime.now()
                dow = now.weekday()
                timer = "{:02d}".format(now.hour)+"{:02d}".format(now.minute)
                timer = round(int(timer)/10)*10
                sql = """SELECT COUNT(1) c FROM rotations WHERE day = :dow
                    AND starttime < :time AND endtime > :time"""
                result = connection.execute(prepare(sql),{'dow':dow,'time':timer}).fetchone()
                if result['c'] > 0:
                    newshow = True
            if getoverride()==0:
                addlegalstuff(nexttime,'front')
            if newshow:
                os.kill(os.getpid(),signal.CTRL_BREAK_EVENT)
            time.sleep(60)
        except Exception as e:
            sentry_sdk.capture_exception(e)
