import os, sys, csv, zipfile, hashlib
from collections import namedtuple

Game = namedtuple('Game', 'sha1, id, platformid, name')
Platform = namedtuple('Platform', 'id, name')

platforms = {
    'nes': Platform(id=7, name='nes'),
    'z64': Platform(id=3, name='n64'),
    'smc': Platform(id=6, name='snes'),
    'gb': Platform(id=4, name='gb'),
    'gba': Platform(id=5, name='gba'),
    'gbc': Platform(id=41, name='gbc'),
    'gen': Platform(id=18, name='genesis')
}

hashes = {}
for game in map(Game._make, csv.reader(open('rom_hashes_sha1.csv', 'r'))):
    hashes[game.sha1] = game

def printsha(sha, filename, platformid = None):
    if ',' in filename:
        filename = '"' + filename + '"'
    if sha in hashes:
        game = hashes[sha]
        print(sha + "," + game.id + "," + game.platformid + "," + filename)
    else:
        print(sha + ",," + str(platformid) + "," + filename)

def shafile(path):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    sha1 = hashlib.sha1()

    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def getExt(filename):
    return os.path.splitext(filename)[1][1:].lower()

for root, _dirs, files in os.walk(sys.argv[1]):
    for file in files:
        ext = getExt(file)
        path = os.path.join(root, file)
        line = None
        if ext == 'zip':
            archive = zipfile.ZipFile(path, 'r')
            for name in [x for x in archive.namelist() if getExt(x) in platforms]:
                ext = getExt(name)
                printsha(hashlib.sha1(archive.read(name)).hexdigest(), file, platforms[ext].id)
        elif ext in platforms:
            printsha(shafile(path), file, platforms[ext].id)
