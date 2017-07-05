import requests
from xml.etree import ElementTree

ROM_DIR=''
GAMELIST=''
IMG_DIR=''

#get platform list
response = requests.get('http://thegamesdb.net/api/GetPlatformsList.php')

tree = ElementTree.fromstring(response.content.decode('utf-8'))
platformList = tree.find('Platforms')
ids = []
for platform in platformList.findall('Platform'):

    ids.append(int(platform.find('id').text))
    name = platform.find('name').text
    print(str(len(ids))+': '+name+' ('+str(ids[-1])+')')

selplatform = input('Select platform: ')
print('selected platform id: '+str(ids[int(selplatform)-1]))
