class Tile:
    """
    Represents a single square on the chess board.
    Acts purely as a data structure holding its coordinates and the piece currently on it.
    """
    def __init__(self, x: int, y: int):
        """
        Initializes a tile with 1-based (x, y) board indices (Row, Column).
        Also calculates its algebraic chess notation position (e.g., 'a1', 'e4').
        """
        self.x = x
        self.y = y
        self.position = chr(y + ord('a') - 1) + str(x)
        self.piece = None
        self.possible_move = []

    def set_piece(self, piece):
        """Places a piece on this tile and updates the piece's internal tile tracker."""
        self.piece = piece
        self.piece.set_tile(self)
        self.piece.update_position(self.x, self.y)
        self.piece.set_has_move(False)

    def is_occupied(self) -> bool:
        """Returns True if there is a chess piece on this tile."""
        return self.piece is not None

    def remove(self):
        """Removes the current piece from this tile, leaving it empty."""
        self.piece = None

    def move_piece(self, piece):
        """
        Moves an existing piece to this tile. 
        Differs from set_piece as it triggers piece.can_move_to() to recalculate valid states.
        """
        self.piece = piece
        self.piece.update_position(self.x, self.y)
        self.piece.can_move_to()
        self.piece.set_tile(self)

    def get_piece(self):
        """Returns the piece currently occupying this tile, or None if empty."""
        return self.piece

    @staticmethod
    def move(from_tile, to_tile):
        """
        Static helper method to transfer a piece between two tiles.
        It moves the piece to the target tile, and removes it from the starting tile.
        """
        to_tile.move_piece(from_tile.get_piece())
        from_tile.remove()

    def highlight(self):
        """Hook method for visual highlighting (handled externally in Pygame, kept for compatibility)."""
        pass

    def highlight_self(self):
        """Hook method for highlighting the selected tile."""
        pass

    def highlight_off(self):
        """Hook method for turning off a highlight."""
        pass

    def __str__(self):
        """Returns a string representation of the tile's coordinates."""
        return f"Row: {self.x} Column: {self.y}"
