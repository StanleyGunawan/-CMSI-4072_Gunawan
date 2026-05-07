from .chess_piece import ChessPiece

class Rook(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "Rook"

    def can_move_to(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        row = self.get_row()
        column = self.get_column()

        for i in range(row + 1, self.MAXROW + 1):
            move = chr(column + ord('a') - 1) + str(i)
            target = board_module.Board.TileList[i][column]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)

        for i in range(row - 1, 0, -1):
            move = chr(column + ord('a') - 1) + str(i)
            target = board_module.Board.TileList[i][column]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)

        for i in range(column + 1, self.MAXCOL + 1):
            move = chr(i + ord('a') - 1) + str(row)
            target = board_module.Board.TileList[row][i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)

        for i in range(column - 1, 0, -1):
            move = chr(i + ord('a') - 1) + str(row)
            target = board_module.Board.TileList[row][i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)

        return possible_moves
