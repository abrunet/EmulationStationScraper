import sys, time, requests
from xml.etree import ElementTree as ET
from collections import defaultdict

def convert_release_date(date):
    parts = date.split('/')
    if len(parts) != 3:
        print('\tError parsing release date: {0}'.format(date))
        return None
    return "{year}{month}{day}T000000".format(year=parts[2],
                                              month=parts[1],
                                              day=parts[0])

def add_game(gamelist, path, name, desc, image, releasedate, developer, publisher, genre, players=None, rating=None):
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

def get_game(gameid, retry=0):
    max_retry = 4
    try:
        response = requests.get('http://thegamesdb.net/api/GetGame.php?id={0}'.format(gameid))
        resptree = ET.fromstring(response.content.decode('utf-8'))
        game = resptree.find('Game')
        baseimgurl = resptree.find('baseImgUrl').text
        if game:
            return game, baseimgurl

    except:
        pass

    if retry < max_retry:
        retry += 1
        print('Sleeping for {0} secs'.format(2**retry))
        time.sleep(2**retry)
        return get_game(gameid, retry)

    raise Exception('Max retries exceeded')


platform = 'nes'
count=0
gamelist = ET.Element('gameList')
outputtree = ET.ElementTree(gamelist)

with open(sys.argv[1], 'r') as csv:
    for line in csv:
        count = count+1
    
        parts = line.strip().split(',', 1)
        filename = path = parts[1]
        try:
            game, baseimgurl = get_game(parts[0])
        except Exception as e:
            print('Skipping {0}, (ID {2}): {1}'.format(filename, e, parts[0]))
            continue

        print("Processing file {0}: {1}".format(count, path))

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

        add_game(gamelist,
                path,
                game.find('GameTitle').text,
                overview.text if not overview is None else None,
                '~/.emulationstation/downloaded_images/'+platform+'/'+filename+'-image.jpg',
                convert_release_date(releasedate.text) if not releasedate is None else None,
                developer.text if not developer is None else None,
                publisher.text if not publisher is None else None,
                ', '.join([genre.text for genre in genres.findall('genre')]) if not genres is None else None,
                players.text if not players is None else None,
                float(rating.text)/10.0 if not rating is None else None
        )

outputtree.write('gamelist.xml')
