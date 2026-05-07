from engine.tile import Tile
import engine.board as board_module
from engine.player import Player
import engine.ai as ai_module
from engine.reinforcement_learning import ReinforcementLearning

class Board_manager:
    """
    Acts as the main logical controller for the game state (MVC Controller).
    Manages whose turn it is, holds move histories, enforces taking turns,
    and executes the movement of pieces mathematically across the board array.
    """
    def __init__(self, ai_object=None, load_default_ai=True):
        """Initializes the game state tracking variables (turn, selection, history, etc)."""
        self.in_play = True
        self.selected_tile = None
        self.white_turn = True
        board_module.Board.white_turn = self.white_turn
        self.possible_tiles = []
        self.selected = False
        self.move_log = []
        self.history_stack = []
        
        # 10 minutes (600 seconds) timers for each player
        self.white_time = 300
        self.black_time = 300

        self.ai_object = ai_module.AI(self,depth = 3)

    def handle_click(self, tile):
        """
        Receives click input from the UI.
        If a piece isn't selected, it selects a piece of the current player's color.
        If a piece is already selected, it attempts to move it or deselects if the same tile is clicked.
        """
        if not self.in_play:
            return

        current_color = "white" if self.white_turn else "black"

        if not self.selected:
            if tile.get_piece() is not None and tile.piece.get_color() == current_color:
                self.selected_tile = tile
                tile.possible_move = tile.piece.can_move_to()
                for move_str in tile.possible_move:
                    self.possible_tiles.append(self.convert(move_str))
                self.selected = True
        elif self.selected:
            if self.selected_tile == tile:
                self.deselect()
            elif tile in self.possible_tiles:
                self.execute_move(tile)

    def play_ai_turn(self):
        """
        Calculates and executes a move for the AI.
        Extracted into its own function so that Reinforcement Learning 
        scripts can trigger it infinitely without needing Pygame to render.
        """
        if not self.white_turn and self.in_play:
            start_tile, end_tile = self.ai_object.get_ai_move()
            if start_tile and end_tile:
                self.selected_tile = start_tile
                self.execute_move(end_tile)
            else:
                self.in_play = False
                print("Checkmate! Black has no moves.")

    def execute_move(self, target_tile, simulation=False):
        """
        Executes the logical movement and rules calculation from `self.selected_tile` to `target_tile`.
        Handles advanced rules like Castling geometries, En Passant generation/captures, 
        and automatic Pawn promotion to Queen. It then logs the completed move.
        """
        # Save state before making the move for Undo (Only if NOT a simulation move)
        if not simulation:
            self.history_stack.append(self.backup_state())
            if target_tile.piece is not None and target_tile.piece.get_type().lower() == "king":
                self.in_play = False
                Player.increase_wins()
            
        # Handle Castling
        is_castling = False
        if self.selected_tile.piece.get_type() == "King" and abs(target_tile.y - self.selected_tile.y) > 1:
            is_castling = True
            if target_tile.y > self.selected_tile.y: # Kingside
                r_from = board_module.Board.TileList[target_tile.x][8]
                r_to = board_module.Board.TileList[target_tile.x][target_tile.y - 1]
            else: # Queenside
                r_from = board_module.Board.TileList[target_tile.x][1]
                r_to = board_module.Board.TileList[target_tile.x][target_tile.y + 1]
            Tile.move(r_from, r_to)
            r_to.get_piece().set_has_move(True)

        # Handle En Passant Capture
        is_en_passant = False
        if self.selected_tile.piece.get_type() == "Pawn" and target_tile.piece is None and target_tile.y != self.selected_tile.y:
            is_en_passant = True
            cap_row = target_tile.x - 1 if self.white_turn else target_tile.x + 1
            board_module.Board.TileList[cap_row][target_tile.y].remove()

        # Check for Setting En Passant Vulnerability 
        if self.selected_tile.piece.get_type() == "Pawn" and abs(target_tile.x - self.selected_tile.x) == 2:
            board_module.Board.en_passant_target = target_tile
        else:
            board_module.Board.en_passant_target = None
            
        # Log move (Only if NOT a simulation)
        if not simulation:
            start_pos = self.selected_tile.position
            end_pos = target_tile.position
            piece_char = self.selected_tile.piece.get_type()[0]
            if piece_char == "P": piece_char = "" # Pawns usually don't have letters
            
            is_cat = target_tile.piece is not None or is_en_passant
            cap_char = "x" if is_cat else "-"
            
            move_str = f"{piece_char}{start_pos}{cap_char}{end_pos}"
            if is_castling:
                move_str = "O-O" if target_tile.y > self.selected_tile.y else "O-O-O"
            self.move_log.append(move_str)

        Tile.move(self.selected_tile, target_tile)

        # Handle Promotion (Promotes to Queen automatically)
        if target_tile.piece.get_type() == "Pawn":
            if (target_tile.piece.is_white() and target_tile.x == 8) or (not target_tile.piece.is_white() and target_tile.x == 1):
                from chess_piece.queen import Queen
                target_tile.set_piece(Queen(target_tile.piece.get_color()))
        
        self.deselect()
        self.white_turn = not self.white_turn
        board_module.Board.white_turn = self.white_turn
        if target_tile.piece:
            target_tile.piece.set_has_move(True)

    def deselect(self):
        """Clears the current tile selection state and wipes the 'possible moves' highlights."""
        self.selected_tile = None
        self.selected = False
        self.possible_tiles.clear()

    def convert(self, move_str: str) -> 'Tile':
        """Converts an algebraic notation string (e.g., 'e4') back into the corresponding Tile object object ref."""
        row = int(move_str[1])
        column = ord(move_str[0]) - ord('a') + 1
        return board_module.Board.TileList[row][column]
    
    def undo_move(self):
        """
        Pops the previous full board state snapshot from history_stack 
        and perfectly restores it to allow 'Undo' functionality.
        If playing against AI, we revert to the state before White's move.
        In Human vs Human, we revert to the state before the previous move.
        """
        if not self.history_stack:
            print("No history to undo.")
            return

        # Pop the most recent snapshot (this is the state BEFORE the last move made)
        snapshot = self.history_stack.pop()
        
        #Pop once more to get from black turn to white turn.
        if self.white_turn and self.history_stack:
            snapshot = self.history_stack.pop()

        self.restore_state(snapshot)
        self.deselect()
        self.in_play = True 

    def backup_state(self):
        """
        Creates a deep mathematical snapshot of the entire board state.
        This allows MCTS to run thousands of hypothetical future moves
        without permanently destroying the real game visible to the player.
        """
        snapshot = {
            "in_play": self.in_play,
            "white_turn": self.white_turn,
            "move_log_len": len(self.move_log),
            "en_passant_target": getattr(board_module.Board, 'en_passant_target', None),
            "tiles": []
        }
        
        # Save every tile's state
        for r in range(1, 9):
            for c in range(1, 9):
                tile = board_module.Board.TileList[r][c]
                if tile.piece is None:
                    snapshot["tiles"].append((r, c, None))
                else:
                    # Save the essential blueprint to rebuild this exact piece
                    p_type = tile.piece.get_type()
                    p_color = tile.piece.get_color()
                    p_has_moved = tile.piece.get_has_move()
                    snapshot["tiles"].append((r, c, p_type, p_color, p_has_moved))
                    
        return snapshot

    def restore_state(self, snapshot):
        """
        Obliterates the current board state and perfectly reconstructs 
        it from a saved backup snapshot. Used to 'Undo' hypothetical MCTS futures.
        """
        self.in_play = snapshot["in_play"]
        self.white_turn = snapshot["white_turn"]
        board_module.Board.white_turn = self.white_turn
        self.selected = False
        self.selected_tile = None
        self.possible_tiles.clear()
        
        # Only truncate the hypothetical log entries added during MCTS
        self.move_log = self.move_log[:snapshot["move_log_len"]]
        board_module.Board.en_passant_target = snapshot["en_passant_target"]
        
        # We must re-import piece constructors just in time for reconstruction
        from chess_piece.rook import Rook
        from chess_piece.knight import Knight
        from chess_piece.bishop import Bishop
        from chess_piece.queen import Queen
        from chess_piece.king import King
        from chess_piece.pawn import Pawn
        
        piece_classes = {
            "Rook": Rook,
            "Knight": Knight,
            "Bishop": Bishop,
            "Queen": Queen,
            "King": King,
            "Pawn": Pawn
        }

        # Clear and reconstruct every piece
        for tile_data in snapshot["tiles"]:
            r = tile_data[0]
            c = tile_data[1]
            tile = board_module.Board.TileList[r][c]
            
            if tile_data[2] is None:
                if tile.piece is not None:
                    tile.remove()  # Clear pieces that shouldn't be here
            else:
                p_type, p_color, p_has_moved = tile_data[2], tile_data[3], tile_data[4]
                
                new_piece = piece_classes[p_type](p_color)
                # The tile's set_piece will automatically update the piece's internal x, y, and position strings
                tile.set_piece(new_piece) 
                new_piece.set_has_move(p_has_moved)
