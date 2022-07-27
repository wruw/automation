# automation
Python based automation software for WRUW-FM 91.1 Cleveland. Uses Flask for the website, mysql/sqlalchely for data storage, and powershell for file playing.

## History
Like most of the world in March of 2020, our radio statuion had to go fully remote on a very short notice. In order to stay on the air in some capacity, I started researching and playing with off the shelf radio automation software, but everything was too complicated for our usecase, and there was no easy way for our DJ's to upload their own shows to it. I was able to hack together some software and a Google Form, but this required daily interaction from my part to put shows in the right place. So eventually once I realized that 1. The pandemic wasn't going away any time soon and 2. Even if it did, having a simple (at least from the end user) automation software allowed us better programming opportunites, I wrote this.

## What the softare can actually do
To put it simply, schedule and play shows. But it allows multiple types of shows, and has fallbacks so if something isn't scheduled, it will still be playling something. It also plays required legal announcements and uploads currently playing songs to Subsonic (our playlist entry service). Shows are uploaded via a web site by our DJ's where they will uplaod their file(s) and what time it should be played. Below are the type of shows that we have
1. Recoeding. This is the most common type of show where someone will record their show in its entiriey at home and upload it as an audio file to be played at the right time. Before a show starts, it will play the required announcements (legal ID, PSA, station promo, safe harbor announcemnts, etc). Since most of our shows are two hours long, there's the option to upload in two halves so it will play the legal annoucements in the middle. This is done instead of uploading two "shows" so that if the first hour is slightly too long, it won't cut it off in the middle of a song to go into the next hour.
2. Playlist. We have around 1.3 million songs in our digital library that is accessable via [Subsonic](http://www.subsonic.org/pages/index.jsp). Our DJ's are able to create playlists inside the web interace, export those playlists, then upload those files to the website to play in order. This will also put required announcements in the right place. Also all uploaded songs are then placed in our default library and tagged as safe harbor or not, but more on that later. We also have an instance of NextCloud running on the same computer that runs this software. This allows people to upload their own music to add to a playlist.
3. Rotation. Very similar to playlist, but this is for a much larger uploaded playlist. Rotations are not uploaded to a specific date and time, but to a day of week and time. So you can create a very large playlist, upload it to when your show would play, then every week, it will play stuff randomly from that rotation.
4. Democracy now. Every weekday at 4, we play [Democracy Now](https://www.democracynow.org/). For that to work, we have a scheduled job to download the show at 2 for playing at 4. The software plays our starting announcement, then runs the downloaded show.
5. Random. If nothing is scheduled to be played, then it will just grab something at random. Every time a playlist or show is uploaded, it will take those songs and add them to a table. Following FCC rules, we are allowed to play indecent (materials with swearing) between 10PM and 6AM, so when someone uploads their show, they will mark if the material is safe or not for playing during the day. So during the day, it will only play things that are safe, but at night, it will play anything. 

## Installation
I currently have it written to work on Windows, but with a little work could easily run on your \*nix environment. The only reason it's on Windows is we use an Axia/Livewire setup for audio routing over IP, and the only audio drivers are for Windows. There's a requirements file that will need installed (`pip install -r requirements.txt`) and a Mysql file with the relevant tables. You also need a few directories, one for playlists and one for recordings. There is also a need to install and connect to Redis. Redis is used when in rotations or random to prevent duplicate plays of the same song or artist.

## running
There are two parts, the web interface and the player. Set up the web interface via whatever wsgi interface you choose (current files exist for uwsgi) pointed to webapp.py. For the player, you need to keep player.py running continuously. For Windows, that requires running playerdaddy.bat (note you can't just run the python script since the only way I could figure out how to stop a file playing was to kill the script and restart it).
