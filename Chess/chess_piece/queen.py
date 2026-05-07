from .chess_piece import ChessPiece

class Queen(ChessPiece):
    def __init__(self, color: str):
        super().__init__(color)

    def get_type(self) -> str:
        return "Queen"

    def can_move_to(self) -> list[str]:
        from .bishop import Bishop
        from .rook import Rook
        b = Bishop(self.get_color())
        r = Rook(self.get_color())
        possible_moves = []
        r.set_position(self.get_position())
        b.set_position(self.get_position())
        possible_moves.extend(r.can_move_to())
        possible_moves.extend(b.can_move_to())
        return possible_moves
