# automation
Python based automation software for WRUW-FM 91.1 Cleveland. Uses Flask for the website, mysql/sqlalchely for data storage, and ffplay for file playing.

## installation
This is mostly python based, but uses [ffplay](https://ffmpeg.org/ffplay.html) on the command line for actual file playing. So that either needs to be installed in your path or in the root directory. Other than that, you need to install the requirements.txt file via pip and set up mysql with the starter.sql file. You also need to update webapp.py and player.py with the correct mysql settings If using, you also need to enter your spinitron, sentry, and sendgrid api keys where approperate.

## running
There are two parts, the web interface and the player. Set up the web interface via whatever wsgi interface you choose (current files exist for uwsgi) pointed to webapp.py. For the player, you need to keep player.py running continuously. For Windows, that requires running playerdaddy.bat. The only way I could get ffplay to stop playing stuff on cue was to hard close the program, and it required two batch files to restart successfully.
