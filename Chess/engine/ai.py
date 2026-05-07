import math
import copy
import random
from engine.board import Board

# Advanced Evaluation: Piece-Square Tables (simplified)
PIECE_VALUES = {
    "Pawn": 100,
    "Knight": 320,
    "Bishop": 330,
    "Rook": 500,
    "Queen": 900,
    "King": 20000
}

PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

def evaluate_board():
    score = 0
    for r in range(1, 9):
        for c in range(1, 9):
            tile = Board.TileList[r][c]
            piece = tile.piece
            if piece:
                val = PIECE_VALUES.get(piece.get_type(), 0)
                
                # Add positional bonus
                r_idx = 8 - r if piece.is_white() else r - 1
                c_idx = c - 1
                
                pos_bonus = 0
                if piece.get_type() == "Pawn":
                    pos_bonus = PAWN_TABLE[r_idx][c_idx]
                elif piece.get_type() == "Knight":
                    pos_bonus = KNIGHT_TABLE[r_idx][c_idx]
                
                val += pos_bonus
                
                if piece.is_white():
                    score += val
                else:
                    score -= val
    return score

def get_ordered_moves(manager, is_white):
    color_str = "white" if is_white else "black"
    moves = []
    for r in range(1, 9):
        for c in range(1, 9):
            tile = Board.TileList[r][c]
            if tile.piece and tile.piece.get_color() == color_str:
                for target_str in tile.piece.can_move_to():
                    target_tile = manager.convert(target_str)
                    
                    # Move ordering: prioritize captures
                    score = 0
                    if target_tile.piece:
                        score = 10 * PIECE_VALUES.get(target_tile.piece.get_type(), 0) - PIECE_VALUES.get(tile.piece.get_type(), 0)
                    
                    moves.append((score, tile.position, target_str))
                    
    # Sort moves, highly evaluated moves first
    moves.sort(key=lambda x: x[0], reverse=True)
    return [(m[1], m[2]) for m in moves]

def alpha_beta(manager, depth, alpha, beta, maximizing_player):
    if depth == 0 or not manager.in_play:
        return evaluate_board()
        
    moves = get_ordered_moves(manager, manager.white_turn)
    if not moves:
        return evaluate_board()

    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            snapshot = manager.backup_state()
            start_tile = manager.convert(move[0])
            end_tile = manager.convert(move[1])
            manager.selected_tile = start_tile
            manager.execute_move(end_tile, simulation=True)
            
            eval_val = alpha_beta(manager, depth - 1, alpha, beta, False)
            
            manager.restore_state(snapshot)
            
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            snapshot = manager.backup_state()
            start_tile = manager.convert(move[0])
            end_tile = manager.convert(move[1])
            manager.selected_tile = start_tile
            manager.execute_move(end_tile, simulation=True)
            
            eval_val = alpha_beta(manager, depth - 1, alpha, beta, True)
            
            manager.restore_state(snapshot)
            
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

class AI:
    """
    High-Level Minimax chess engine with Alpha-Beta Pruning 
    and simple move ordering.
    """
    def __init__(self, manager, depth=3):
        self.manager = manager
        self.depth = depth

    def get_ai_move(self):
        is_white = self.manager.white_turn
        moves = get_ordered_moves(self.manager, is_white)
        
        if not moves:
            return None, None

        best_moves = []
        if is_white:
            best_val = -math.inf
            alpha = -math.inf
            beta = math.inf
            for move in moves:
                snapshot = self.manager.backup_state()
                start_tile = self.manager.convert(move[0])
                end_tile = self.manager.convert(move[1])
                self.manager.selected_tile = start_tile
                self.manager.execute_move(end_tile, simulation=True)
                
                move_val = alpha_beta(self.manager, self.depth - 1, alpha, beta, False)
                
                self.manager.restore_state(snapshot)
                
                if move_val > best_val:
                    best_val = move_val
                    best_moves = [move]
                elif move_val == best_val:
                    best_moves.append(move)
                
                alpha = max(alpha, move_val)
        else:
            best_val = math.inf
            alpha = -math.inf
            beta = math.inf
            for move in moves:
                snapshot = self.manager.backup_state()
                start_tile = self.manager.convert(move[0])
                end_tile = self.manager.convert(move[1])
                self.manager.selected_tile = start_tile
                self.manager.execute_move(end_tile, simulation=True)
                
                move_val = alpha_beta(self.manager, self.depth - 1, alpha, beta, True)
                
                self.manager.restore_state(snapshot)
                
                if move_val < best_val:
                    best_val = move_val
                    best_moves = [move]
                elif move_val == best_val:
                    best_moves.append(move)
                
                beta = min(beta, move_val)
                
        if best_moves:
            best_move = random.choice(best_moves)
            return self.manager.convert(best_move[0]), self.manager.convert(best_move[1])
        return None, None
