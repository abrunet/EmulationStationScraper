import requests
import multiprocessing as mp
from collections import namedtuple

Game = namedtuple('Game', 'sha1, id, platformid, name')

def clean_name(filename):
    return filename

def download_metadata(game, prompt_queue, write_queue):
    cleanname = clean_name(game.name)
    #response = requests()

    matches = {
        'game': game,
        'results': []
    }
    if len(matches['results']) == 0:
        write_queue.put((matches['game'], None))
    elif len(matches['results']) == 1:
        write_queue.put((matches['game'], matches['results'].id))
    else:
        prompt_queue.put(matches)

def read_csv(csv_file, prompt_queue, write_queue):
    download_pool = mp.Pool()

    for game in map(Game._make, csv.reader(open(csv_file, 'r'))):
        if game.id is None:
            download_pool.apply_async(download_metadata, (game, prompt_queue, write_queue))
        else:
            write_queue.put((game, game.id))

    download_pool.close()
    download_pool.join()

    #poison the prompt_queue
    prompt_queue.put(None)

def write_csv(output_file, write_queue):
    with open(output_file, 'wb') as csvFile:
        csvWriter = csv.writer(csvFile)
        while True:
            game, gameId = write_queue.get()

            if game is None:
                break

            csvWriter.writerow([game.sha1, gameId, game.platformid, game.name])

def main():
    prompt_queue = mp.Queue
    write_queue = mp.Queue

    csv_reader = Process(target=read_csv, args=(filename, prompt_queue, write_queue))
    csv_writer = Process(target=write_csv, args=(output_file, write_queue))

    isQuitting = False

    while True:
        matches = prompt_queue.get()

        if matches is None:
            #poison the write_queue
            write_queue.put((None, None))
            break

        if isQuitting:
            write_queue.put((matches['game'], None))
        else:
            print('\n{0}'.format(matches['game'].name))
            for idx, match in enumerate(matches['results']):
                print('\t' + str(idx + 1) + ': ' + match.name)
            selection = input('# or Q to quit: ')

            if selection.isdigit() and int(selection) > 0 and int(selection) <= len(matches['results']):
                write_queue.put((
                    matches['game'],
                    matches['results'][int(selection)-1].id))
            elif selection.lower() == 'q':
                isQuitting = True

    csv_reader.join()
    write_queue.join()

if __name__ == '__main__':
    main()
