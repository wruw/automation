from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import requests
import datetime
import eyed3
from multiprocessing import Process
import random
import os
import mutagen
import redis
import subprocess
import time

#spinitron data
spinitron_url = "https://spinitron.com/api/spin/create-v1"
spinitron_token = ""

r = redis.Redis()

def terminal(function):
    p = subprocess.Popen(function,stdout=subprocess.PIPE)
    o, e = p.communicate()
    o = o.decode('utf-8').strip()
    if o.isnumeric():
        return int(o)
    return o

def getlength(file):
    m = mutagen.File(file)
    return m.info.length

def log(text, engine):
    print(text)
    logsql(text, engine)
    """
    try:
        s = Process(target=logsql, args = (text, engine))
        s.start()
    except:
        pass
    """

def logsql(text, engine):
    connection = engine.connect()
    sql = """INSERT INTO logs (text)
        VALUES (:text)"""
    connection.execute(prepare(sql),{'text':text})

#like a stack, adds to the front
def addtofront(file,override,engine):
    log('adding {} to front'.format(file),engine)
    connection = engine.connect()
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
def addtoback(file,override,engine):
    log('adding {} to back'.format(file),engine)
    connection = engine.connect()
    m = 0
    sql = """SELECT MAX(queue) AS m FROM queue"""
    result = connection.execute(prepare(sql))
    if result:
        for i in result:
            if i:
                m = i['m']
    if not m:
        m = 0
    sql = """INSERT INTO queue (queue, file, override) VALUES
        (:m, :file, :override)
        """
    connection.execute(prepare(sql),{'file':file,'m':int(m)+1,'override':override})

def empty(engine):
    connection = engine.connect()
    sql = """DELETE FROM queue"""
    connection.execute(prepare(sql))

#for the player, grabs the next file
def getnext(engine):
    connection = engine.connect()
    sql = """SELECT COUNT(1) AS c FROM queue"""
    result = connection.execute(prepare(sql)).fetchone()
    if result['c'] == 0:
        return False
    sql = """SELECT file, override FROM queue ORDER BY queue ASC LIMIT 1"""
    file = connection.execute(prepare(sql))
    for f in file:
        sql = """DELETE FROM queue WHERE queue=1"""
        connection.execute(prepare(sql))
        sql = """UPDATE queue SET queue=queue-1"""
        connection.execute(prepare(sql))
        return f

def setoverride(override,engine):
    connection = engine.connect()
    sql = """UPDATE override SET currentstatus=:override"""
    connection.execute(prepare(sql),{'override':override} )

def getoverride(engine):
    connection = engine.connect()
    sql = """SELECT currentstatus FROM override"""
    result = connection.execute(prepare(sql)).fetchone()
    return result['currentstatus']

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

def addlegalstuff(time,location,engine,override=False):
    connection = engine.connect()
    timetolookup = "{:02d}".format(time.hour)+"{:02d}".format(time.minute)
    sql = """SELECT * FROM announcements WHERE time=:time AND enabled=1 ORDER BY RAND()"""
    stufftoplay = connection.execute(prepare(sql),{'time':timetolookup})
    for item in stufftoplay:
        folder = "/Productions/{}".format(item['folder'])
        file = "{}/{}".format(folder,random.choice(os.listdir(folder)))
        log('adding {} as {} to {}'.format(file,item,location),engine)
        if override:
            o=1
        else:
            o=0
        if location=='back':
            addtoback(file,o,engine)
        elif location=='front':
            addtofront(file,o,engine)

def findsong(engine):
    connection = engine.connect()
    #grab the next thing from the queue to play.
    nextfile = getnext(engine)
    if nextfile:
        song = nextfile['file'].strip()
        attempttoread(song)
        #submit to spinitron
        s = Process(target=submit, args = (song,))
        s.start()
        if nextfile['override'] == 1:
            setoverride(1,engine)
        else:
            setoverride(0,engine)
        log('playing {} from queue'.format(song),engine)
        #play the song
        terminal(['audtool', '--playlist-addurl', song])
        length = getlength(song)
        #if it's a short song, add another. 
        if length < 20:
            findsong(engine)
    #nothing else to play, grab something from the database
    else:
        setoverride(0,engine)
        foundrotation = False
        #first look for a rotation to play
        now = datetime.datetime.now()
        dow = now.weekday()
        time = "{:02d}".format(now.hour)+"{:02d}".format(now.minute)
        sql = """SELECT id FROM rotations WHERE day = :dow
            AND starttime <= :time AND endtime >= :time
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
                        song = row2['location'].strip()
                        found = False
                        attempttoread(song)
                        s = Process(target=submit, args = (song,))
                        s.start()
                        log('playing {} from rotation'.format(song),engine)
                        terminal(['audtool', '--playlist-addurl', song])
                        length = getlength(song)
                        if length < 20:
                            findsong(engine)
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
                        song = row['location'].strip()
                        attempttoread(song)
                        s = Process(target=submit, args = (song,))
                        s.start()
                        log('playing {} from random'.format(song),engine)
                        terminal(['audtool', '--playlist-addurl', song])
                        length = getlength(song)
                        if length < 20:
                            findsong(engine)
                    else:
                        count = count + 1
    connection.close()

def attempttoread(song):
    found = False
    attempts = 0 
    while not found:
        try:
            open(song)
            found = True
        except:
            attempts += 1
            time.sleep(1)
            if attempts > 5:
                return