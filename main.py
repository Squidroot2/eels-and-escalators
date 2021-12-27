import csv
import random
import os
import shutil
import time
import concurrent.futures
import pickle
from statistics import mean, median, mode

# Constants
PLAYER_COUNT = 3
FILE_NAME = 'tiles.csv'
DATA_OUT = 'data.pickle'
GAME_COUNT = 100000
PROCESSES = 12
DO_LOG = False
LOG_FOLDER = os.path.join(os.getcwd(), "logs")

class Tile:
    def __init__(self, num, eel_or_esc=0, dest = 0):
        self.num = num
        self.eel_or_esc = eel_or_esc # Value is -1 for eel, 1 for escalators, and 0 for neither
        self.destination=dest

        if self.eel_or_esc != 0:
            if self.eel_or_esc == 1:
                assert self.destination > self.num
            else:
                assert self.destination < self.num
                assert self.destination > 0
        else:
            self.destination = 0

    def getDestination(self):
        if self.destination == 0:
            return self.num
        else:
            return self.destination


class TileBoard:
    def __init__(self, tilelist):
        self.tilelist = tilelist
        self.size = len(tilelist)

    def find_next(self, eel_or_esc, from_tile=0):
        assert eel_or_esc in (-1,1)
        for tile in range(from_tile, self.size):
            if self.tilelist[tile].eel_or_esc == eel_or_esc:
                return self.tilelist[tile]
        else:
            return None

    @staticmethod
    def createBoardfromCsv(file_location):

        tiles = list([Tile(0,0,0)])
        with open(file_location) as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                tile = Tile(num=int(row[0]), eel_or_esc=int(row[1]),dest=int(row[2]))
                tiles.append(tile)

        return TileBoard(tilelist=tiles)

class Player:
    def __init__(self, location, name):
        self.location = location
        self.name = name
        self.has_won = False

    def playTurn(self, tile_board, log=None):
        result = self._roll_dice()

        # Move to location based on roll
        if result[0] in (1,-1):

            if result[0] == 1:
                rolled = "escalators"
            else:
                rolled = "eels"
            log.append("%s rolled %s" % (self.name, rolled))

            next_tile = tile_board.find_next(result[0], self.location)
            if next_tile:
                self.location = next_tile.num
                log.append("%s moved to %s at tile %d" % (self.name, rolled, self.location))
            else:
                self.location += result[1]
                log.append("%s could not move to %s; moved %d spaces to %d" % (self.name, rolled, result[1], self.location))

        else:
            self.location += result[1]
            log.append("%s rolled a %d; moved to %d" % (self.name, result[1], self.location))

        # Determine if at Finish
        if self.location >= tile_board.size:
            self.has_won = True
            log.append("%s has won!" % self.name)

        # Get eaten by eel or ride up escalator
        else:
            self.location = tile_board.tilelist[self.location].getDestination()
            log.append("%s finished turn at %d" % (self.name, self.location))

    def reset(self):
        self.location = 0
        self.has_won = False

    @staticmethod
    def _roll_dice():
        # Returns a tuple as (eels_or_esc, roll)
        die_1 = random.choice([-1,1])
        die_2 = random.choice([-1,1])

        die_3 = random.randint(1,6)

        if die_1 == die_2:
            result = (die_1, die_3)
        else:
            result = (0, die_3)

        return result

    @staticmethod
    def createNumPlayers(number_of_players):
        player_list = list()
        for num in range(number_of_players):
            player_name = "Player%s" %(num+1)
            player = Player(0, player_name)
            player_list.append(player)

        return player_list


def play_game(player_list, tile_board, log=None):
    turn_count = 0
    no_win = True
    while (no_win):
        turn_count +=1
        log.append("---Start of Turn %d---" % turn_count)
        for player in player_list:
            player.playTurn(tile_board, log)
            if player.has_won:
                no_win = False
                break
    return turn_count

def writeLog(file_name, messages):
    if DO_LOG:
        with open(file_name, 'w') as file:
            for message in messages:
                file.write(message + "\n")

def simulateGames(number_of_games, tile_board):
    turn_count_list = list()
    player_list = Player.createNumPlayers(PLAYER_COUNT)

    for game in range(number_of_games):
        game_number = game + 1
        log_name = "game%d.log" % game_number
        log_file = os.path.join(LOG_FOLDER, log_name)
        logs_to_write = list()

        for player in player_list:
            player.reset()

        logs_to_write.append("Game %d starting" % game_number)

        turn_count = play_game(player_list, tile_board, log=logs_to_write)
        turn_count_list.append(turn_count)

        msg = "Game %d completed on turn %d" % (game_number, turn_count)
        print(msg)
        logs_to_write.append(msg)

        writeLog(log_file, logs_to_write)

    return turn_count_list

def dumpFile(data):
    with open('data.pickle', 'wb') as file:
        pickle.dump(data, file)

def main():
    tile_board = TileBoard.createBoardfromCsv(FILE_NAME)

    # Clear LOG Folder and recreate it
    if os.path.exists(LOG_FOLDER):
        print("Removing old logs folder...")
        shutil.rmtree(LOG_FOLDER)

    if DO_LOG:
        print("Creating new logs folder...")
        os.mkdir(LOG_FOLDER)

    games_per_process = int(GAME_COUNT / PROCESSES)

    start = time.perf_counter()
    total_results = list()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = [executor.submit(simulateGames, games_per_process, tile_board) for _ in range(PROCESSES)]

        for f in concurrent.futures.as_completed(results):
           total_results += f.result()

    finish = time.perf_counter()

    print()
    print("INSTANCES: %d" % len(total_results))
    print("MEAN: %f" % mean(total_results))
    print("MEDIAN: %d" % median(total_results))
    print("MODE: %d" % mode(total_results))
    print("MAX: %d" % max(total_results))
    print("MIN: %d" % min(total_results))
    print("TIME TAKEN: %f" % (finish-start))

    dumpFile(total_results)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()


