from abc import ABC, abstractmethod

class ChessPiece(ABC):
    """
    Abstract base class representing a generic chess piece.
    All specific piece types (e.g., Pawn, King) inherit from this class.
    """
    def __init__(self, color: str):
        """Initializes a chess piece with a given color ('white' or 'black')."""
        self.color = color
        self.has_move = False
        self.current_position = ""
        self.tile = None
        self.MAXROW = 8
        self.MAXCOL = 8

    def update_position(self, row: int, column: int):
        """Converts board indices (row, col) into algebraic notation (e.g., 1,1 -> 'a1') and updates the piece."""
        self.current_position = chr(column + ord('a') - 1) + str(row)

    def set_tile(self, tile):
        """Links the piece to the Tile object it currently occupies."""
        self.tile = tile

    def set_has_move(self, has_move: bool):
        """Sets the flag indicating whether this piece has moved yet (critical for Castling and Pawn initial jumps)."""
        self.has_move = has_move

    def set_position(self, coordinates: str):
        """Directly sets the piece's algebraic position (e.g., 'e4')."""
        self.current_position = coordinates

    @abstractmethod
    def can_move_to(self) -> list[str]:
        """Calculates and returns a list of valid target algebraic coordinates (e.g., ['e5', 'e6']) for this piece."""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Returns the piece's type as a string (e.g., 'Pawn', 'King')."""
        pass

    def get_position(self) -> str:
        """Returns the current algebraic position of the piece."""
        return self.current_position

    def is_white(self) -> bool:
        """Checks if the piece is white."""
        return self.color == "white"

    def is_enemy(self, piece: 'ChessPiece') -> bool:
        """Determines if the given piece belongs to the opposing player."""
        return self.is_white() != piece.is_white()


    def get_row(self) -> int:
        """Extracts the 1-based integer row from the algebraic position (e.g., 'e4' -> 4)."""
        return int(self.current_position[1])

    def get_column(self) -> int:
        """Extracts the 1-based integer column from the algebraic position (e.g., 'e4' -> 5 ('e'))."""
        return ord(self.current_position[0]) - ord('a') + 1

    def get_tile(self):
        """Returns the Tile object this piece is currently situated on."""
        return self.tile

    def get_color(self) -> str:
        """Returns the color string ('white' or 'black') of the piece."""
        return self.color

    def get_has_move(self) -> bool:
        """Returns True if the piece has moved at least once in the game."""
        return self.has_move
