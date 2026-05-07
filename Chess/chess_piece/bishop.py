from .chess_piece import ChessPiece

class Bishop(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "Bishop"

    def can_move_to(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        row = self.get_row()
        column = self.get_column()

        col_i, row_i = column + 1, row + 1
        while col_i <= self.MAXCOL and row_i <= self.MAXROW:
            move = chr(col_i + ord('a') - 1) + str(row_i)
            target = board_module.Board.TileList[row_i][col_i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)
            col_i += 1; row_i += 1

        col_i, row_i = column - 1, row + 1
        while col_i >= 1 and row_i <= self.MAXROW:
            move = chr(col_i + ord('a') - 1) + str(row_i)
            target = board_module.Board.TileList[row_i][col_i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)
            col_i -= 1; row_i += 1

        col_i, row_i = column - 1, row - 1
        while col_i >= 1 and row_i > 0:
            move = chr(col_i + ord('a') - 1) + str(row_i)
            target = board_module.Board.TileList[row_i][col_i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)
            col_i -= 1; row_i -= 1

        col_i, row_i = column + 1, row - 1
        while col_i <= self.MAXCOL and row_i > 0:
            move = chr(col_i + ord('a') - 1) + str(row_i)
            target = board_module.Board.TileList[row_i][col_i]
            if target.is_occupied():
                if self.is_enemy(target.get_piece()):
                    possible_moves.append(move)
                break
            possible_moves.append(move)
            col_i += 1; row_i -= 1

        return possible_moves
