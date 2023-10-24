from tkinter.filedialog import askopenfilenames
import re

files = askopenfilenames()
for file in files:
    f = open(file,'r',encoding='utf-8')
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
    f.close()
    f = open(file,'w',encoding='utf-8')
    f.write(totaltext)
    f.close()