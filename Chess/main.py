from engine.player import Player
from engine.board_display import BoardDisplay

def main():
    player1 = Player()
    player1.set_name()
    player1.read_file()
    print(player1)

    board = BoardDisplay()
    board.start()

    player1.update_line()
    print(player1)
    player1.close_file()

if __name__ == "__main__":
    main()
