from .chess_piece import ChessPiece

class Pawn(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "Pawn"

    def can_move_to(self) -> list[str]:
        if self.is_white():
            return self.white_move()
        return self.black_move()

    def white_move(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        offsets = [[1, 1], [1, -1]]

        if not self.get_has_move():
            row = self.get_row() + 2
            column = self.get_column()
            if 0 < row < 9 and 0 < column < 9:
                move = chr(column + ord('a') - 1) + str(row)
                if not board_module.Board.TileList[row][column].is_occupied() and not board_module.Board.TileList[row-1][column].is_occupied():
                    possible_moves.append(move)

        row = self.get_row() + 1
        column = self.get_column()
        if 0 < row < 9 and 0 < column < 9:
            move = chr(column + ord('a') - 1) + str(row)
            if not board_module.Board.TileList[row][column].is_occupied():
                possible_moves.append(move)

        for element in offsets:
            row = self.get_row() + element[0]
            column = self.get_column() + element[1]
            if 0 < row < 9 and 0 < column < 9:
                move = chr(column + ord('a') - 1) + str(row)
                target_tile = board_module.Board.TileList[row][column]
                if target_tile.is_occupied():
                    if self.is_enemy(target_tile.get_piece()):
                        possible_moves.append(move)
                else:
                    ep = getattr(board_module.Board, 'en_passant_target', None)
                    if ep and ep.x == self.get_row() and ep.y == column:
                        if ep.get_piece() and self.is_enemy(ep.get_piece()):
                            possible_moves.append(move)
        return possible_moves

    def black_move(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        offsets = [[-1, 1], [-1, -1]]

        if not self.get_has_move():
            row = self.get_row() - 2
            column = self.get_column()
            if 0 < row < 9 and 0 < column < 9:
                move = chr(column + ord('a') - 1) + str(row)
                if not board_module.Board.TileList[row][column].is_occupied() and not board_module.Board.TileList[row+1][column].is_occupied():
                    possible_moves.append(move)

        row = self.get_row() - 1
        column = self.get_column()
        if 0 < row < 9 and 0 < column < 9:
            move = chr(column + ord('a') - 1) + str(row)
            if not board_module.Board.TileList[row][column].is_occupied():
                possible_moves.append(move)

        for element in offsets:
            row = self.get_row() + element[0]
            column = self.get_column() + element[1]
            if 0 < row < 9 and 0 < column < 9:
                move = chr(column + ord('a') - 1) + str(row)
                target_tile = board_module.Board.TileList[row][column]
                if target_tile.is_occupied():
                    if self.is_enemy(target_tile.get_piece()):
                        possible_moves.append(move)
                else:
                    ep = getattr(board_module.Board, 'en_passant_target', None)
                    if ep and ep.x == self.get_row() and ep.y == column:
                        if ep.get_piece() and self.is_enemy(ep.get_piece()):
                            possible_moves.append(move)
        return possible_moves
