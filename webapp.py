from flask import Flask, render_template, request, send_from_directory, Response
from sqlalchemy import create_engine
from sqlalchemy import text as prepare
import requests
import datetime
from werkzeug.utils import secure_filename
import os
import sendgrid
import os
from sendgrid.helpers.mail import *
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration
import string
import random
import hashlib
import re
# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

sg = sendgrid.SendGridAPIClient(api_key='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')

sentry_sdk.init(
    dsn="https://63f20c25c4364fa0ab1872c17fc23e94@o116363.ingest.sentry.io/5511687",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

app = Flask(__name__)

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def sendemail(email, date, time):
    from_email = Email("idn2@case.edu")
    to_email = To(email)
    subject = "Your show has been scheduled"
    content = Content("text/plain", "Your show has been scheduled for {} at {}".format(date,time))
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/rotation",methods=["GET","POST"])
def rotation():
    if request.method=="GET":
        return render_template('rotation.html')
    c = sql_alchemy_engine.connect()
    name = request.form['name']
    email = request.form['email']
    day = request.form['day']
    starttime = request.form['starttime']
    endtime = request.form['endtime']
    file = request.files['file']
    clean = request.form.get('clean')
    replace = request.form.get('replace')
    if not allowed_file(file.filename, {'m3u8'}):
        return render_template('message.html',{'message':'Wrong filetype.'})
    file.save(os.path.join('/Playlists', 'temp.m3u8'))
    f = open(os.path.join('/Playlists', 'temp.m3u8'),'r',encoding='utf-8')
    text = f.readlines()
    #create the rotation, first delete if one exists
    if replace == 'replace':
        sql="""DELETE from rotations
            WHERE day=:day
            AND starttime=:starttime
            AND endtime=:endtime
        """
        c.execute(prepare(sql),{'day':day,'starttime':starttime,'endtime':endtime})
    sql = """INSERT INTO rotations
        (day,starttime,endtime,name,email) VALUES
        (:day, :starttime, :endtime, :name, :email)
    """
    c.execute(prepare(sql),{'day':day,'starttime':starttime,'endtime':endtime,'name':name,'email':email})
    sql = """SELECT LAST_INSERT_ID() AS lid
    """
    id = c.execute(prepare(sql)).fetchone()['lid']
    for line in text:
        if line[0:1]!='#':
            if line[0:11] == '/mnt/share/':
                l = line[11:]
                l = '/run/user/1000/gvfs/smb-share:server=ads.case.edu,share=utech/Shares/WRUW/'+l
                l = l.rstrip()
            else:
                l = line[15:]
                l = '/run/user/1000/gvfs/smb-share:server=wruw-storage1,share=automation/'+l
                l = l.rstrip()
            sql = """SELECT id
                FROM songs WHERE location=:location
            """
            songids = c.execute(prepare(sql),{'location':l})
            for songid in songids:
                sql = """INSERT INTO songs_rotations
                    (song_id, rotation_id) VALUES
                    (:songid, :id)
                """
                c.execute(prepare(sql),{'songid':songid['id'],'id':id})
            else:
                if clean=='clean':
                    cid = 1
                else:
                    cid = 0
                sql = """INSERT INTO songs
                    (location, clean) VALUES
                    (:location, :clean)
                """
                c.execute(prepare(sql),{'location':l,'clean':cid})
                sql = """SELECT LAST_INSERT_ID() as lid"""
                lid = c.execute(prepare(sql)).fetchone()['lid']
                sql = """INSERT INTO songs_rotations
                    (song_id, rotation_id) VALUES
                    (:songid, :id)
                """
                c.execute(prepare(sql),{'songid':lid,'id':id})
    c.close()
    sendemail(request.form['email'],request.form['day'],request.form['starttime'])
    return render_template('message.html',message='Your rotation has been created.')

@app.route('/rotation/view')
def rotationview():
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM rotations ORDER BY day, starttime"""
    rotations = []
    result = c.execute(prepare(sql))
    for row in result:
        rotation = {'name':row['name'], 'id':row['id']}
        dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        rotation['day'] = dow[row['day']]
        rotation['time'] = '{}:{} - {}:{}'.format(str(row['starttime'])[:-2].zfill(2),str(row['starttime'])[3:2].zfill(2),str(row['endtime'])[:-2].zfill(2),str(row['endtime'])[3:2].zfill(2))
        rotations.append(rotation)
    return render_template('rotationview.html',rotations=rotations)

@app.route('/rotation/<id>')
def rotationdownload(id):
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM songs_rotations WHERE rotation_id = :id"""
    result = c.execute(prepare(sql),{'id':id})
    text = '#EXTM3U\n'
    for row in result:
        sql = """SELECT location FROM songs WHERE id = :id"""
        song = c.execute(prepare(sql),{'id':row['song_id']}).fetchone()['location']
        if song[0:74] == '/run/user/1000/gvfs/smb-share:server=ads.case.edu,share=utech/Shares/WRUW/':
            song = song[74:]
            song = '/mnt/share/'+song
            song = song.rstrip()
        else:
            song = song[67:]
            song = '/mnt/storage'+song
            song = song.rstrip()
        text += song+'\n'
    return Response(text,mimetype='text/plain',headers={"Content-Disposition":"attachment;filename=rotation.m3u8"})


@app.route('/rotation/delete/<id>')
def deleterotation(id):
    c = sql_alchemy_engine.connect()
    sql = """DELETE FROM rotations WHERE id = :id"""
    result = c.execute(prepare(sql),{'id':id})
    return render_template('message.html',message='Your show has been deleted')

@app.route("/playlist",methods=["GET","POST"])
def playlist():
    if request.method=="GET":
        return render_template('playlist.html')
    c = sql_alchemy_engine.connect()
    name = request.form['name']
    email = request.form['email']
    time = datetime.datetime.fromisoformat(request.form['date']+'T'+request.form['time'])
    file = request.files['file']
    clean = request.form.get('clean')
    if not allowed_file(file.filename, {'m3u8'}):
        return render_template('message.html',message='Wrong filetype.')
    #delete playlist if it exists
    sql="""SELECT id, location from playlists
        WHERE time=:time
    """
    items = c.execute(prepare(sql),{'time':time})
    for item in items:
        os.remove(os.path.join('/Playlists',item['location']))
        sql = """DELETE FROM playlists WHERE id=:id
        """
        c.execute(prepare(sql),{'id':item['id']})
    filename = time.strftime('%m-%d-%Y-%H-%M')+secure_filename(file.filename)
    file.save(os.path.join('/Playlists', filename))
    f = open(os.path.join('/Playlists', filename),'r',encoding='utf-8')
    text = f.readlines()
    sql = """INSERT INTO playlists
        (time,location,name,email) VALUES
        (:time, :location, :name, :email)
    """
    c.execute(prepare(sql),{'time':time,'location':filename,'name':name,'email':email})
    for line in text:
        if line[0:1]!='#':
            if line[0:11] == '/mnt/share/':
                l = line[11:]
                l = '/run/user/1000/gvfs/smb-share:server=ads.case.edu,share=utech/Shares/WRUW/'+l
                l = l.rstrip()
                sql = """SELECT COUNT(1) AS c
                    FROM songs WHERE location=:location
                """
                count = c.execute(prepare(sql),{'location':l}).fetchone()['c']
                if count==0:
                    if clean=='clean':
                        cid = 1
                    else:
                        cid = 0
                    sql = """INSERT INTO songs
                        (location, clean) VALUES
                        (:location, :clean)
                    """
                    c.execute(prepare(sql),{'location':l,'clean':cid})
        f.close()
    c.close()
    sendemail(request.form['email'],request.form['date'],request.form['time'])
    return render_template('message.html',message='Your playlist has been imported.')

@app.route('/playlist/view')
def playlistview():
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM playlists ORDER BY time"""
    playlists = []
    result = c.execute(prepare(sql))
    for row in result:
        playlist = {'location':row['location'],'name':row['name']}
        playlist['time'] = row['time'].strftime('%m/%d/%Y %I:%M %p')
        playlists.append(playlist)
    return render_template('playlistview.html',playlists=playlists)

@app.route('/playlist/<file>')
def downloadplaylist(file):
    return send_from_directory('/Playlists',file)

@app.route('/playlist/delete/<file>')
def deleteplaylist(file):
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM playlists WHERE location = :file"""
    result = c.execute(prepare(sql),{'file':file})
    for row in result:
        try:
            os.remove(os.path.join('/Playlists',row['location']))
        except:
            pass
        sql = """DELETE FROM playlists WHERE id=:id"""
        c.execute(prepare(sql),{'id':row['id']})
    return render_template('message.html',message='Your file has been deleted')

@app.route("/playlistfix",methods=["GET","POST"])
def playlistfix():
    if request.method=="GET":
        return render_template('playlistfix.html')
    file = request.files['file']
    if not allowed_file(file.filename, {'m3u8'}):
        return render_template('message.html',{'message':'Wrong filetype.'})
    file.save(os.path.join('/Playlists', 'temp.m3u8'))
    f = open(os.path.join('/Playlists', 'temp.m3u8'),'r',encoding='utf-8')
    text = f.readlines()
    newtext = []
    for line in text:
        if line[0:1]=='#':
            newtext.append(line)
        else:
            if line[0:19] == '/mnt/share/library/':
                l = line[19:]
                firstchar = l[0:1]
                if re.match('[a-zA-Z]',firstchar):
                    l = '/mnt/share/library/{}/{}'.format(firstchar,l)
                else:
                    l = '/mnt/share/library/0-9/{}'.format(l)
                newtext.append(l)
            else:
                newtext.append(line)
    totaltext = ''.join(newtext)
    return Response(totaltext,mimetype='text/plain',headers={"Content-Disposition":"attachment;filename={}".format(file.filename)})


@app.route("/recording",methods=["GET","POST"])
def recording():
    if request.method=="GET":
        return render_template('recording.html')
    c = sql_alchemy_engine.connect()
    name = request.form['name']
    email = request.form['email']
    time = datetime.datetime.fromisoformat(request.form['date']+'T'+request.form['time'])
    file1 = request.files['file1']
    file2 = request.files.get('file2')
    if not allowed_file(file1.filename, {'mp3','m4a','wav'}) or file2 and not allowed_file(file2.filename, {'mp3','m4a','wav'}):
        return render_template('message.html',message='Wrong filetype.')
    #delete files if it exists
    sql="""SELECT id, file1, file2 from recordings
        WHERE time=:time
    """
    items = c.execute(prepare(sql),{'time':time})
    for item in items:
        os.remove(os.path.join('/Recordings',item['file1']))
        if item['file2']:
            os.remove(os.path.join('/Recordings',item['file2']))
        sql = """DELETE FROM recordings WHERE id=:id
        """
        c.execute(prepare(sql),{'id':item['id']})
    filename1 = time.strftime('%m-%d-%Y-%H-%M')+'-1-'+secure_filename(file1.filename)
    file1.save(os.path.join('/Recordings', filename1))
    filename2=None
    if file2:
        filename2 = time.strftime('%m-%d-%Y-%H-%M')+'-2-'+secure_filename(file2.filename)
        file2.save(os.path.join('/Recordings', filename2))
    sql = """INSERT INTO recordings
        (time,file1,file2,name,email) VALUES
        (:time, :file1, :file2, :name, :email)
    """
    c.execute(prepare(sql),{'time':time,'file1':filename1,'file2':filename2,'name':name,'email':email})
    c.close()
    sendemail(request.form['email'],request.form['date'],request.form['time'])
    return render_template('message.html',message='Your show has been imported.')

@app.route('/recording/view')
def recordingview():
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM recordings ORDER BY time"""
    recordings = []
    result = c.execute(prepare(sql))
    for row in result:
        recording = {'file1':row['file1'],'file2':row['file2'],'name':row['name']}
        recording['time'] = row['time'].strftime('%m/%d/%Y %I:%M %p')
        recordings.append(recording)
    return render_template('recordingview.html',recordings=recordings)

@app.route('/recording/<file>')
def downloadrecording(file):
    return send_from_directory('/Recordings',file)

@app.route('/recording/delete/<file>')
def deleterecording(file):
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM recordings WHERE file1 = :file OR file2 = :file"""
    result = c.execute(prepare(sql),{'file':file})
    for row in result:
        try:
            os.remove(os.path.join('/Recordings',row['file1']))
        except:
            pass
        if row['file2']:
            try:
                os.remove(os.path.join('/Recordings',row['file1']))
            except:
                pass
        sql = """DELETE FROM recordings WHERE id=:id"""
        c.execute(prepare(sql),{'id':row['id']})
    return render_template('message.html',message='your show has been deleted')

@app.route("/jukebox",methods=["GET","POST"])
def jukebox():
    if request.method=="GET":
        return render_template('jukebox.html')
    username = request.form['username']
    if not username:
        username = request.form['email']
    email = request.form['email']
    password = request.form['password']
    salt = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=8))
    myusername = 'idn2@case.edu'
    mypassword = '6*Z8E1tsUXIKcK$T'
    params = {'u':myusername,'t':hashlib.md5((mypassword+salt).encode('utf-8')).hexdigest(),'s':salt,'v':'1.16.1','c':'createaccount','username':username,'password':password,'email':email}
    requests.get('https://jukebox.wruw.org/rest/createUser',params=params)
    from_email = Email("idn2@case.edu")
    to_email = To(email)
    subject = "Your account has been created"
    content = Content("text/plain", "Your account has been created. Log in at https://jukebox.wruw.org with the username {} and your chosen password.".format(username))
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return render_template('message.html',message="Your account has been created. Log in at https://jukebox.wruw.org with the username {} and your chosen password.".format(username))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)
