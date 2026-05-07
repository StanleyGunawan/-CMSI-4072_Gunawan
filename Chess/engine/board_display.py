import pygame
import sys
import ctypes
from engine.board import Board
from engine.board_manager import Board_manager

# --- UI CONSTANTS ---
TILE_SIZE = 64
MARGIN = 24
BOARD_SIZE = 8 * TILE_SIZE
PANEL_WIDTH = 240
SCREEN_WIDTH = BOARD_SIZE + (MARGIN * 2) + PANEL_WIDTH
SCREEN_HEIGHT = BOARD_SIZE + (MARGIN * 2)

# --- COLOR PALETTE (Modern Dark Theme) ---
COLOR_BG = (49, 46, 43)           # Dark charcoal background
COLOR_PANEL = (38, 36, 33)        # Slightly darker sidebar
COLOR_LIGHT_SQ = (238, 238, 210)  # Cream
COLOR_DARK_SQ = (118, 150, 86)    # Chess.com Green
COLOR_TEXT = (200, 200, 200)      # Soft white text
COLOR_HIGHLIGHT = (246, 246, 130, 150) # Soft yellow for selection
COLOR_DOT = (0, 0, 0, 80)         # Semi-transparent black for move hints

# Tell Windows to treat this app as DPI-aware so it doesn't stretch and blur the window
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # Windows 8.1+
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # Windows Vista+
    except Exception:
        pass

class BoardDisplay(Board):
    """
    Subclass of Board that handles all UI rendering via Pygame (MVC View).
    Receives user interactions and routes them to the Board_manager.
    """
    def start(self, manager=None):
        """
        Initializes Pygame, builds the window, loads graphical assets, 
        and houses the main event loop (listening for clicks/exits).
        """
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chess Learning Engine - Training Observer")
        clock = pygame.time.Clock()
        
        # Initialize UI Assets once (MASSIVE performance saver over doing it in the draw loop)
        self.init_fonts()
        images = self.load_images()

        # Use provided manager or create a fresh one
        self.manager = manager if manager else Board_manager()

        running = True
        while running:
            time_delta = clock.get_time() / 1000.0 # Convert ms to seconds
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Map clicking coords to game board indexes
                    x, y = pygame.mouse.get_pos()
                    
                    # Adjust for border margin
                    x -= MARGIN
                    y -= MARGIN
                    
                    if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                        col = (x // TILE_SIZE) + 1
                        row = 8 - (y // TILE_SIZE)
                        
                        if 1 <= row <= 8 and 1 <= col <= 8:
                            self.manager.handle_click(Board.TileList[row][col])
                            
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u: # Undo move
                        self.manager.undo_move()

            # Update timers
            if self.manager.in_play:
                if self.manager.white_turn:
                    self.manager.white_time -= time_delta
                else:
                    self.manager.black_time -= time_delta
                
                # Check for time out
                if self.manager.white_time <= 0 or self.manager.black_time <= 0:
                    self.manager.in_play = False
                    print("Game Over! Time's up!")

            # Render Frame
            screen.fill(COLOR_BG)
            self.draw_board(screen)
            self.draw_coordinates(screen)
            self.draw_highlights(screen)
            self.draw_pieces(screen, images)
            self.draw_sidebar(screen)

            if not self.manager.in_play:    # If a king was captured or time's up
                pygame.display.flip()
                print("Game Over!")
                pygame.time.delay(3000)
                running = False
                break

            pygame.display.flip()
            
            # TRIGGER AI HERE: View has updated the human move, now let AI play
            if not self.manager.white_turn and self.manager.in_play:
                pygame.time.delay(100) # Reduced delay for snappier AI response
                self.manager.play_ai_turn()

            clock.tick(60)
            
        pygame.quit()

    def init_fonts(self):
        """Pre-loads all fonts to prevent framerate drops during rendering."""
        pygame.font.init()
        self.fonts = {
            'coords': pygame.font.SysFont('segoe ui', 14, bold=True),
            'h1': pygame.font.SysFont('segoe ui', 20, bold=True),
            'h2': pygame.font.SysFont('segoe ui', 14, italic=True),
            'body': pygame.font.SysFont('segoe ui', 15),
            'timer': pygame.font.SysFont('consolas', 22, bold=True)
        }

    def _ensure_fonts(self):
        """Initializes fonts when draw methods are used outside the start() path."""
        if not hasattr(self, 'fonts') or not self.fonts:
            self.init_fonts()

    def load_images(self):
        """Loads and pre-scales all PNG piece sprite images from the 'resources' directory."""
        pieces = ['wPawn', 'wRook', 'wKnight', 'wBishop', 'wQueen', 'wKing',
                  'bPawn', 'bRook', 'bKnight', 'bBishop', 'bQueen', 'bKing']
        images = {}
        for piece in pieces:
            try:
                img = pygame.image.load(f"resources/{piece}.png").convert_alpha()
                images[piece] = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
            except Exception as e:
                print(f"Error loading {piece}: {e}")
        return images

    def draw_board(self, screen):
        """Paints the 8x8 checkerboard pattern."""
        colors = [COLOR_LIGHT_SQ, COLOR_DARK_SQ]
        for r in range(1, 9):
            for c in range(1, 9):
                color = colors[((r + c) % 2 == 0)]
                py_y = (8 - r) * TILE_SIZE + MARGIN
                py_x = (c - 1) * TILE_SIZE + MARGIN
                pygame.draw.rect(screen, color, pygame.Rect(py_x, py_y, TILE_SIZE, TILE_SIZE))

    def draw_coordinates(self, screen):
        """Draws the Algebraic Notation labels (a-h, 1-8)."""
        self._ensure_fonts()
        # Draw Ranks (1-8)
        for r in range(1, 9):
            text = self.fonts['coords'].render(str(r), True, COLOR_TEXT)
            py_y = (8 - r) * TILE_SIZE + MARGIN
            screen.blit(text, (MARGIN - 16, py_y + (TILE_SIZE // 2) - 8))
            
        # Draw Files (a-h)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for c in range(1, 9):
            text = self.fonts['coords'].render(files[c-1], True, COLOR_TEXT)
            py_x = (c - 1) * TILE_SIZE + MARGIN
            screen.blit(text, (py_x + (TILE_SIZE // 2) - 4, BOARD_SIZE + MARGIN + 4))

    def draw_highlights(self, screen):
        """Draws modern, semi-transparent overlays for selected pieces and legal moves."""
        # Create a transparent surface for drawing alpha shapes
        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        for r in range(1, 9):
            for c in range(1, 9):
                tile = Board.TileList[r][c]
                py_y = (8 - r) * TILE_SIZE + MARGIN
                py_x = (c - 1) * TILE_SIZE + MARGIN
                
                # Highlight Selected Piece
                if tile == self.manager.selected_tile:
                    overlay.fill(COLOR_HIGHLIGHT)
                    screen.blit(overlay, (py_x, py_y))
                
                # Highlight Possible Moves (Modern Dots)
                elif tile in self.manager.possible_tiles:
                    if tile.piece: # If it's a capture move, add a red border
                        pygame.draw.rect(screen, (200, 50, 50), pygame.Rect(py_x, py_y, TILE_SIZE, TILE_SIZE), 3)
                    else:
                        overlay.fill((0,0,0,0)) # Clear
                        center = (TILE_SIZE // 2, TILE_SIZE // 2)
                        radius = TILE_SIZE // 6
                        pygame.draw.circle(overlay, COLOR_DOT, center, radius)
                    screen.blit(overlay, (py_x, py_y))
                    

    def draw_pieces(self, screen, images):
        """Iterates over the mathematical Board array and blits sprites."""
        for r in range(1, 9):
            for c in range(1, 9):
                piece = Board.TileList[r][c].get_piece()
                if piece:
                    prefix = "w" if piece.is_white() else "b"
                    key_name = prefix + piece.get_type()
                    if key_name in images:
                        py_y = (8 - r) * TILE_SIZE + MARGIN
                        py_x = (c - 1) * TILE_SIZE + MARGIN
                        screen.blit(images[key_name], pygame.Rect(py_x, py_y, TILE_SIZE, TILE_SIZE))

    def draw_sidebar(self, screen):
        """Renders the right-hand panel containing Move History and Timers."""
        panel_x = BOARD_SIZE + (MARGIN * 2)
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, COLOR_PANEL, panel_rect)
        
        # Subtle left border for depth
        pygame.draw.line(screen, (30, 28, 25), (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)
        
        self.draw_move_history(screen, panel_x)
        self.draw_timers(screen, panel_x)

    def draw_move_history(self, screen, panel_x):
        """Displays completed actions from the manager's move_log."""
        self._ensure_fonts()
        title = self.fonts['h1'].render("Move History", True, COLOR_TEXT)
        screen.blit(title, (panel_x + 20, 20))
        
        # Draw column labels
        w_label = self.fonts['h2'].render("White", True, (150, 150, 150))
        b_label = self.fonts['h2'].render("Black", True, (150, 150, 150))
        screen.blit(w_label, (panel_x + 60, 55))
        screen.blit(b_label, (panel_x + 140, 55))
        
        # Divider Line
        pygame.draw.line(screen, (60, 58, 55), (panel_x + 20, 75), (panel_x + PANEL_WIDTH - 20, 75))
        
        moves = getattr(self.manager, 'move_log', [])
        start_y = 85
        line_height = 24
        
        if not moves:
            placeholder = self.fonts['h2'].render("(No moves yet)", True, (100, 100, 100))
            screen.blit(placeholder, (panel_x + 60, start_y + 10))
        else:
            pairs = []
            for i in range(0, len(moves), 2):
                w_move = moves[i]
                b_move = moves[i+1] if i+1 < len(moves) else ""
                pairs.append((w_move, b_move))
                
            # Show up to last 15 rows
            visible_pairs = pairs[-15:] 
            
            for i, (w, b) in enumerate(visible_pairs):
                turn_num = len(pairs) - len(visible_pairs) + i + 1
                
                # Active row highlighting (last move)
                if i == len(visible_pairs) - 1:
                    row_rect = pygame.Rect(panel_x + 10, start_y + i * line_height - 2, PANEL_WIDTH - 20, line_height)
                    pygame.draw.rect(screen, (50, 48, 45), row_rect, border_radius=4)
                
                turn_text = self.fonts['body'].render(f"{turn_num}.", True, (120, 120, 120))
                w_text = self.fonts['body'].render(w, True, COLOR_TEXT)
                b_text = self.fonts['body'].render(b, True, COLOR_TEXT)
                
                y_pos = start_y + i * line_height
                screen.blit(turn_text, (panel_x + 20, y_pos))
                screen.blit(w_text, (panel_x + 60, y_pos))
                if b:
                    screen.blit(b_text, (panel_x + 140, y_pos))

        # Show Hint for Undo at bottom of history
        hint = self.fonts['h2'].render("Press 'U' to Undo", True, (100, 100, 100))
        screen.blit(hint, (panel_x + 60, SCREEN_HEIGHT - 120))

    def draw_timers(self, screen, panel_x):
        """Displays the Chess clocks for each player in modern styled boxes."""
        self._ensure_fonts()
        timer_y = SCREEN_HEIGHT - 90
        
        # Calculate MM:SS
        def format_time(seconds):
            if seconds < 0: seconds = 0
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m:02}:{s:02}"

        white_str = format_time(self.manager.white_time)
        black_str = format_time(self.manager.black_time)
        
        # Highlight active timer
        w_bg = (200, 200, 200) if self.manager.white_turn else (70, 70, 70)
        b_bg = (200, 200, 200) if not self.manager.white_turn else (70, 70, 70)
        
        w_text_color = (0, 0, 0) if self.manager.white_turn else (150, 150, 150)
        b_text_color = (0, 0, 0) if not self.manager.white_turn else (150, 150, 150)

        # White Timer Box
        w_rect = pygame.Rect(panel_x + 20, timer_y, 90, 45)
        pygame.draw.rect(screen, w_bg, w_rect, border_radius=6)
        w_time_surf = self.fonts['timer'].render(white_str, True, w_text_color)
        screen.blit(w_time_surf, w_time_surf.get_rect(center=w_rect.center))

        # Black Timer Box
        b_rect = pygame.Rect(panel_x + 130, timer_y, 90, 45)
        pygame.draw.rect(screen, b_bg, b_rect, border_radius=6)
        b_time_surf = self.fonts['timer'].render(black_str, True, b_text_color)
        screen.blit(b_time_surf, b_time_surf.get_rect(center=b_rect.center))