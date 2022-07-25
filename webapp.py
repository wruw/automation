from flask import Flask, render_template, request, send_from_directory
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

# SQL Alchemy Test
sql_alchemy_engine = create_engine(
    'mysql+pymysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)

sg = sendgrid.SendGridAPIClient(api_key='ADD_YOUR_API_KEY_HERE')

sentry_sdk.init(
    dsn="ADD SENTRY DOMAIN HERE",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

app = Flask(__name__)

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def sendemail(email, date, time):
    from_email = Email("noreply@wruw.org")
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
    if not allowed_file(file.filename, {'m3u8'}):
        return render_template('message.html',{'message':'Wrong filetype.'})
    file.save(os.path.join('C:\Playlists', 'temp.m3u8'))
    f = open(os.path.join('C:\Playlists', 'temp.m3u8'),'r',encoding='utf-8')
    text = f.readlines()
    #create the rotation, first delete if one exists
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
                l = 'M:\\'+l.replace('/','\\')
                l = l.rstrip()
            else:
                l = line[15:]
                l = 'D:\\nextcloud\\'+l.replace('/','\\')
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
        rotation = {'name':row['name']}
        dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        rotation['day'] = dow[row['day']]
        rotation['time'] = '{}:{} - {}:{}'.format(str(row['starttime'])[:-2].zfill(2),str(row['starttime'])[3:2].zfill(2),str(row['endtime'])[:-2].zfill(2),str(row['endtime'])[3:2].zfill(2))
        rotations.append(rotation)
    return render_template('rotationview.html',rotations=rotations)

@app.route('/rotation/delete/<name>')
def deleterotation(name):
    c = sql_alchemy_engine.connect()
    sql = """DELETE FROM rotations WHERE name = :name"""
    result = c.execute(prepare(sql),{'name':name})
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
        os.remove(os.path.join('C:\Playlists',item['location']))
        sql = """DELETE FROM playlists WHERE id=:id
        """
        c.execute(prepare(sql),{'id':item['id']})
    filename = time.strftime('%m-%d-%Y-%H-%M')+secure_filename(file.filename)
    file.save(os.path.join('C:\Playlists', filename))
    f = open(os.path.join('C:\Playlists', filename),'r',encoding='utf-8')
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
                l = 'M:\\'+l.replace('/','\\')
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
    return send_from_directory('C:\\Playlists',file)

@app.route('/playlist/delete/<file>')
def deleteplaylist(file):
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM playlists WHERE location = :file"""
    result = c.execute(prepare(sql),{'file':file})
    for row in result:
        try:
            os.remove(os.path.join('C:\Playlists',row['location']))
        except:
            pass
        sql = """DELETE FROM playlists WHERE id=:id"""
        c.execute(prepare(sql),{'id':row['id']})
    return render_template('message.html',message='Your file has been deleted')

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
        os.remove(os.path.join('C:\Recordings',item['file1']))
        if item['file2']:
            os.remove(os.path.join('C:\Recordings',item['file2']))
        sql = """DELETE FROM recordings WHERE id=:id
        """
        c.execute(prepare(sql),{'id':item['id']})
    filename1 = time.strftime('%m-%d-%Y-%H-%M')+'-1-'+secure_filename(file1.filename)
    file1.save(os.path.join('C:\Recordings', filename1))
    filename2=None
    if file2:
        filename2 = time.strftime('%m-%d-%Y-%H-%M')+'-2-'+secure_filename(file2.filename)
        file2.save(os.path.join('C:\Recordings', filename2))
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
    return send_from_directory('C:\\Recordings',file)

@app.route('/recording/delete/<file>')
def deleterecording(file):
    c = sql_alchemy_engine.connect()
    sql = """SELECT * FROM recordings WHERE file1 = :file OR file2 = :file"""
    result = c.execute(prepare(sql),{'file':file})
    for row in result:
        try:
            os.remove(os.path.join('C:\Recordings',row['file1']))
        except:
            pass
        if row['file2']:
            try:
                os.remove(os.path.join('C:\Recordings',row['file1']))
            except:
                pass
        sql = """DELETE FROM recordings WHERE id=:id"""
        c.execute(prepare(sql),{'id':row['id']})
    return render_template('message.html',message='your show has been deleted')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)
