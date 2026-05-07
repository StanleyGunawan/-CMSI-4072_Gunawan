from .chess_piece import ChessPiece

class King(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "King"

    def can_move_to(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        row = self.get_row()
        column = self.get_column()
        offsets = [
            [1, 0], [0, 1], [-1, 0], [0, -1],
            [1, 1], [-1, 1], [-1, -1], [1, -1]
        ]
        
        for element in offsets:
            temp_row = row + element[0]
            temp_column = column + element[1]
            if 1 <= temp_row <= 8 and 1 <= temp_column <= 8:
                move = chr(temp_column + ord('a') - 1) + str(temp_row)
                target = board_module.Board.TileList[temp_row][temp_column]
                if target.is_occupied():
                    if self.is_enemy(target.get_piece()):
                        possible_moves.append(move)
                    continue 
                possible_moves.append(move)
                
        # Castling
        if not self.get_has_move():
            row = self.get_row()
            # Kingside
            rook_kingside = board_module.Board.TileList[row][8].get_piece()
            if rook_kingside and rook_kingside.get_type() == "Rook" and not rook_kingside.get_has_move():
                if not board_module.Board.TileList[row][6].is_occupied() and not board_module.Board.TileList[row][7].is_occupied():
                    possible_moves.append(chr(7 + ord('a') - 1) + str(row))
            # Queenside
            rook_queenside = board_module.Board.TileList[row][1].get_piece()
            if rook_queenside and rook_queenside.get_type() == "Rook" and not rook_queenside.get_has_move():
                if not board_module.Board.TileList[row][2].is_occupied() and not board_module.Board.TileList[row][3].is_occupied() and not board_module.Board.TileList[row][4].is_occupied():
                    possible_moves.append(chr(3 + ord('a') - 1) + str(row))
                
        return possible_moves
