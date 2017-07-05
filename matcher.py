import re, os
import requests
from xml.etree import ElementTree as ET
from collections import defaultdict
from difflib import SequenceMatcher as SM

#tree = ET.parse('gameboy.xml')
tree = ET.parse('nes.xml')
root = tree.getroot()

roman = {'i':1, 'ii':2, 'iii':3, 'iv':4, 'v':5, 'vi':6, 'vii':7, 'viii':8, 'ix':9, 'x':10}
stopwords = set([ 'the', 'of', 'and' ])
games = {}

wordmap = defaultdict(set)

def cleanname(name):
    result = []
    name = re.sub('-', '', name)
    name = re.sub('[^a-z0-9 ]', ' ', name.lower()).strip()
    for elem in [part.strip() for part in name.split()]:
         if len(elem) < 5 and elem in roman.keys():
             result.append(str(roman[elem]))
         elif len(elem) > 1 and elem not in stopwords:
             result.append(elem)
         elif elem.isdigit():
             result.append(elem)
    return ''.join(result), [str(elem) for elem in result if len(elem) > 3 or elem.isdigit()]

for game in root.findall('Game'):
    id = int(game.find('id').text)
    name = game.find('GameTitle').text
    games[id] = name

    key, words = cleanname(name)
#    print(name+": "+', '.join(words))

    games[key] = id
    for word in words:
        wordmap[word].add(id)

filematch = {}
gamelist = 'nes.lst'
with open(gamelist, 'r') as f:
    for line in f:
        matches = None
        name, ext = os.path.splitext(line)
        key, words = cleanname(name[0:name.find('(')])

        if key in games:
            filematch[line.strip()] = games[key]
            continue

        print(line.strip())
        for word in (set(words) & wordmap.keys()):
            if matches == None:
                matches = wordmap[word]
            else:
                matches = matches & wordmap[word]

        match2 = defaultdict(int)
        for word in set(words) & wordmap.keys():
            value = 0.5 if word.isdigit() else 1
            for id in wordmap[word]:
                match2[id] += value

        sortedm = sorted([m for m in match2 if match2[m] > 0.5], key=lambda x: match2[x], reverse=True)
        for idx, match in enumerate(sortedm):
            score = match2[match] / len(words)
#            score = SM(None, name[0:name.find('(')], games[match]).ratio()
            marker = '*' if score > 0.8 else ''
            print('\t'+str(idx+1)+': '+marker+games[match])
#            print('\t{0}: {1} ({2:.0%})'.format(idx+1, marker+games[match],
#                                                score))

        if matches and len(matches) < 20:
            continue
            print(line.strip())
            sortedmatches = sorted(matches, key=lambda x: len(set(words) & wordmap[x]), reverse=True)
            for idx, match in enumerate(sortedmatches):
                print('\t'+str(idx+1)+': '+games[match])
            selected = input('# or S to skip, Q to quit: ')

            if selected.isdigit() and int(selected) > 0 and int(selected) <= len(sortedmatches):
                filematch[line.strip()] = sortedmatches[int(selected)-1]
            elif selected.lower() == 'q':
                break
        else:
            print(line.strip()+" doesn't match anything")

def convertreleasedate(date):
    parts = date.split('/')
    if len(parts) != 3:
        print('\tError parsing release date: {0}'.format(date))
        return None
    return "{year}{month}{day}T000000".format(year=parts[2],
                                              month=parts[1],
                                              day=parts[0])

def addgame(gamelist, path, name, desc, image, releasedate, developer, publisher, genre, players=None, rating=None):
    game = ET.Element('game')
    ET.SubElement(game, 'path').text = './'+path
    ET.SubElement(game, 'name').text = name
    ET.SubElement(game, 'desc').text = desc
    ET.SubElement(game, 'image').text = image
    ET.SubElement(game, 'releasedate').text = releasedate
    ET.SubElement(game, 'developer').text = developer
    ET.SubElement(game, 'publisher').text = publisher
    ET.SubElement(game, 'genre').text = genre

    if not players is None:
        ET.SubElement(game, 'players').text = players

    if not rating is None:
        ET.SubElement(game, 'rating').text = str(rating)

    gamelist.append(game)

count=0
gamelist = ET.Element('gameList')
outputtree = ET.ElementTree(gamelist)
for path in filematch:
    break
    count = count+1
    filename, ext = os.path.splitext(path)
    response = requests.get('http://thegamesdb.net/api/GetGame.php?id={0}'.format(filematch[path]))
    resptree = ET.fromstring(response.content.decode('utf-8'))
    game = resptree.find('Game')
    baseimgurl = resptree.find('baseImgUrl').text

    print("Processing file {0} of {1}: {2}".format(count, len(filematch), path))

    genres = game.find('Genres')
    overview = game.find('Overview')
    releasedate = game.find('ReleaseDate')
    developer = game.find('Developer')
    publisher = game.find('Publisher')
    players = game.find('Players')
    rating = game.find('Rating')
    images = game.find('Images')

    downloadboxart = False

    # download the image
    if downloadboxart:
        boxartlist = images.findall('boxart')
        imagename = ''
        for boxart in boxartlist:
            if boxart.get('side') == 'front':
                path = boxart.text
                imagename = filename+'-image'+os.path.splitext(path)[1]
                imgresp = requests.get(baseimgurl+path, stream=True)
                print("\tDownloading box art to {0}".format(imagename))
                if imgresp.status_code == 200:
                    with open(imagename, 'wb') as f:
                        for chunk in imgresp.iter_content(1024):
                            f.write(chunk)
                else:
                    print("\tError downloading box art")

                break

    addgame(gamelist,
            path,
            game.find('GameTitle').text,
            overview.text if not overview is None else None,
            '~/.emulationstation/downloaded_images/gb/'+filename+'-image.jpg',
            convertreleasedate(releasedate.text) if not releasedate is None else None,
            developer.text if not developer is None else None,
            publisher.text if not publisher is None else None,
            ', '.join([genre.text for genre in genres.findall('genre')]) if not genres is None else None,
            players.text if not players is None else None,
            float(rating.text)/10.0 if not rating is None else None
           )

outputtree.write('gamelist.xml')
