from datetime import date
import requests

d = date.today()

url = "https://traffic.libsyn.com/democracynow/dn{}-{:02d}{:02d}.mp3".format(d.year,d.month,d.day)
r = requests.get(url,allow_redirects=True)
open('C:\Recordings\dn.mp3','wb').write(r.content)
