from sqlalchemy import create_engine
from sqlalchemy import text as prepare

import tkinter as tk
from tkinter import filedialog
import os
root = tk.Tk()
root.withdraw()

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
sql = """UPDATE queue SET queue=queue+1"""
connection.execute(prepare(sql))
path = filedialog.askopenfilename()
sql = """INSERT INTO queue (queue, file, override) VALUES
    (1, :path, 1)
    """
connection.execute(prepare(sql),{'file':file, 'override':override})
