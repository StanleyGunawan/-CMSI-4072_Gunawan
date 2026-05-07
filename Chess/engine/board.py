class Board:
    black_pieces = []
    white_pieces = []
    TileList = [[None for _ in range(9)] for _ in range(9)]
    white_turn = True
    en_passant_target = None

    def __init__(self):
        self.__class__.black_pieces = []
        self.__class__.white_pieces = []
        self.__class__.white_turn = True
        self.__class__.en_passant_target = None
        self.create_pieces()
        self.set_tile()

    def create_pieces(self):
        from chess_piece.rook import Rook
        from chess_piece.knight import Knight
        from chess_piece.bishop import Bishop
        from chess_piece.king import King
        from chess_piece.queen import Queen
        from chess_piece.pawn import Pawn

        self.white_pieces.append(Rook("white"))
        self.white_pieces.append(Knight("white"))
        self.white_pieces.append(Bishop("white"))
        self.white_pieces.append(Queen("white"))
        self.white_pieces.append(King("white"))
        self.white_pieces.append(Bishop("white"))
        self.white_pieces.append(Knight("white"))
        self.white_pieces.append(Rook("white"))
        for _ in range(8):
            self.white_pieces.append(Pawn("white"))

        self.black_pieces.append(Rook("black"))
        self.black_pieces.append(Knight("black"))
        self.black_pieces.append(Bishop("black"))
        self.black_pieces.append(Queen("black"))
        self.black_pieces.append(King("black"))
        self.black_pieces.append(Bishop("black"))
        self.black_pieces.append(Knight("black"))
        self.black_pieces.append(Rook("black"))
        for _ in range(8):
            self.black_pieces.append(Pawn("black"))

    def set_tile(self):
        from engine.tile import Tile
        for i in range(1, 9):
            for j in range(1, 9):
                Board.TileList[i][j] = Tile(i, j)

        for i in range(1, 9):
            Board.TileList[8][i].set_piece(self.black_pieces[i-1])

        for i in range(1, 9):
            Board.TileList[7][i].set_piece(self.black_pieces[i+7])

        for i in range(1, 9):
            Board.TileList[1][i].set_piece(self.white_pieces[i-1])

        for i in range(1, 9):
            Board.TileList[2][i].set_piece(self.white_pieces[i+7])
