import re, os
from xml.etree import ElementTree as ET
from collections import defaultdict
from difflib import SequenceMatcher as SM
from fuzzywuzzy import process

roman = {'i':1, 'ii':2, 'iii':3, 'iv':4, 'v':5, 'vi':6, 'vii':7, 'viii':8, 'ix':9, 'x':10}
games = {}

def clean_name(name):
    result = []
    name = re.sub('\(.{1,4}\)','', name)
    name = re.sub('\[.*\]','', name)
    name = re.sub('[-:]','',name)
    name = name.lower().strip()
    for elem in [part.strip() for part in name.split()]:
        if elem in roman.keys():
            result.append(str(roman[elem]))
        else:
            result.append(elem)
    return ' '.join(result)

tree = ET.parse('nes.xml')
root = tree.getroot()

for game in root.findall('Game'):
    id = int(game.find('id').text)
    name = game.find('GameTitle').text

    games[clean_name(name)] = (id, name)

outfile = open('nes.csv', 'w')

with open('nes.lst', 'r') as listfile:
    for romfile in listfile:
        romfile = romfile.strip()
        cleaned = clean_name(os.path.splitext(romfile)[0])
        result = process.extract(cleaned, games.keys(), limit=5)

        if result[0][1] > 94:
            match = games[result[0][0]]
            outfile.write('{0},{1}\n'.format(match[0], romfile))
        else:
            print(romfile)
            for idx, res in enumerate(result):
                print('  {0}: {1} [{2}]'.format(idx+1, res[0], res[1]))

            selected = input('# or S to skip, Q to quit: ')

            if selected.isdigit() and int(selected) > 0 and int(selected) <= 5:
                match = games[result[int(selected)-1][0]]
                outfile.write('{0},{1}\n'.format(match[0], romfile))
            elif selected.lower() == 'q':
                break

outfile.close()
