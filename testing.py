import time
from sqlalchemy import create_engine
from sqlalchemy import text as prepare

sql_alchemy_engine = create_engine(
    'mysql://wruw_automation:911-tech@localhost:3306/wruw_automation?charset=utf8&use_unicode=1',
    pool_recycle = 3600,
    echo = True
)
while True:
    connection = sql_alchemy_engine.connect()
    sql = """SELECT location FROM songs ORDER by RAND() LIMIT 1"""
    song = connection.execute(prepare(sql)).fetchone()
    print(song['location'])
    with open(song['location'], 'rb') as f:
        print(f.read(1024))
    connection.close()
    time.sleep(10)
