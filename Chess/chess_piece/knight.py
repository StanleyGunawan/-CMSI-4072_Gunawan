from .chess_piece import ChessPiece

class Knight(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "Knight"

    def can_move_to(self) -> list[str]:
        import engine.board as board_module
        possible_moves = []
        row = self.get_row()
        column = self.get_column()
        offsets = [
            [-2, 1], [-1, 2], [1, 2], [2, 1],
            [2, -1], [1, -2], [-1, -2], [-2, -1]
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
                
        return possible_moves
