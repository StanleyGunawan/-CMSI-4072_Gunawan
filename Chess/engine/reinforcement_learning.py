import random
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
from engine.board import Board

BOARD_SQUARES = 64
PIECE_PLANES = 12
STATE_PLANES = 18
STATE_SIZE = STATE_PLANES * BOARD_SQUARES
ACTION_SIZE = BOARD_SQUARES * BOARD_SQUARES

PIECE_TO_PLANE = {
    ("white", "Pawn"): 0,
    ("white", "Knight"): 1,
    ("white", "Bishop"): 2,
    ("white", "Rook"): 3,
    ("white", "Queen"): 4,
    ("white", "King"): 5,
    ("black", "Pawn"): 6,
    ("black", "Knight"): 7,
    ("black", "Bishop"): 8,
    ("black", "Rook"): 9,
    ("black", "Queen"): 10,
    ("black", "King"): 11,
}

class ChessDQN(nn.Module):
    """
    A simple Feedforward Neural Network predicting Q-values 
    for every possible theoretical move on the 8x8 board.
    """
    def __init__(self):
        super(ChessDQN, self).__init__()
        self.fc1 = nn.Linear(STATE_SIZE, 512)
        self.fc2 = nn.Linear(512, 256)
        
        # 64 squares for a start piece * 64 squares for an end position = 4096 possible moves
        self.fc3 = nn.Linear(256, ACTION_SIZE)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

class ReinforcementLearning:
    """
    Deep Q-Network (DQN) Agent for playing Chess using PyTorch.
    Replaces basic randomized AI with Neural Network predictions.
    """
    def __init__(
        self,
        color="black",
        epsilon=1.0,
        gamma=0.97,
        learning_rate=0.0003,
        batch_size=128,
        memory_size=50000,
        epsilon_min=0.05,
        epsilon_decay=0.9999,
    ):
        self.color = color
        self.episode = 0 # Track episode count for decay and checkpointing
        
        # Exploration/Exploitation Parameters
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        
        # RL Hyperparameters
        self.gamma = gamma
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        
        # Memory Replay Buffer for Training
        self.memory = deque(maxlen=memory_size)
        
        # PyTorch Setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.using_cuda = self.device.type == "cuda"
        if self.using_cuda:
            # Enable cuDNN auto-tuner for faster fixed-shape workloads.
            torch.backends.cudnn.benchmark = True
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA not available. Training on CPU.")
        self.model = ChessDQN().to(self.device)
        
        # Target Network for stabilizing learning (Moving Target Problem)
        self.target_net = ChessDQN().to(self.device)
        self.target_net.load_state_dict(self.model.state_dict())
        self.target_net.eval() # Target network is strictly for inference
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.SmoothL1Loss() # Huber loss is more stable than MSE for RL

    def get_state(self):
        """
        Encodes the board as flat one-hot planes plus turn, castling, and en passant metadata.
        """
        state = torch.zeros(STATE_SIZE, dtype=torch.float32)

        for r in range(1, 9):
            for c in range(1, 9):
                piece = Board.TileList[r][c].get_piece()
                if piece is None:
                    continue

                plane = PIECE_TO_PLANE[(piece.get_color(), piece.get_type())]
                index = (r - 1) * 8 + (c - 1)
                state[plane * BOARD_SQUARES + index] = 1.0

        self._fill_binary_plane(state, 12, not getattr(Board, "white_turn", True))
        self._fill_binary_plane(state, 13, self._has_castling_right("white", kingside=True))
        self._fill_binary_plane(state, 14, self._has_castling_right("white", kingside=False))
        self._fill_binary_plane(state, 15, self._has_castling_right("black", kingside=True))
        self._fill_binary_plane(state, 16, self._has_castling_right("black", kingside=False))

        en_passant_target = getattr(Board, "en_passant_target", None)
        if en_passant_target is not None:
            ep_index = (en_passant_target.x - 1) * 8 + (en_passant_target.y - 1)
            state[17 * BOARD_SQUARES + ep_index] = 1.0

        return state.to(self.device)

    def _fill_binary_plane(self, state, plane_idx, enabled):
        if enabled:
            start = plane_idx * BOARD_SQUARES
            state[start:start + BOARD_SQUARES] = 1.0

    def _has_castling_right(self, color, kingside):
        home_row = 1 if color == "white" else 8
        king_tile = Board.TileList[home_row][5]
        rook_col = 8 if kingside else 1
        rook_tile = Board.TileList[home_row][rook_col]

        king = king_tile.get_piece()
        rook = rook_tile.get_piece()

        if king is None or rook is None:
            return False
        if king.get_type() != "King" or rook.get_type() != "Rook":
            return False
        if king.get_color() != color or rook.get_color() != color:
            return False

        return not king.get_has_move() and not rook.get_has_move()

    def _move_to_index(self, start_tile, target_tile):
        """
        Maps a chess move from structured Tiles into a unique [0, 4095] mathematical class.
        """
        start_idx = (start_tile.x - 1) * 8 + (start_tile.y - 1)
        target_idx = (target_tile.x - 1) * 8 + (target_tile.y - 1)
        return start_idx * 64 + target_idx

    def get_ai_move(self):
        """
        Evaluates the PyTorch neural network to predict the highest Q-value action.
        """
        current_state = self.get_state()
        valid_moves = self._get_all_valid_moves()

        if not valid_moves:
            return None, None # Checkmate

        # Epsilon-Greedy Exploration
        if random.random() < self.epsilon:
            best_move = random.choice(valid_moves)
            return best_move
        else:
            # Exploit Model Predictions
            with torch.no_grad():
                q_values = self.model(current_state)
                
            best_move = None
            max_q = float('-inf')
            
            # Filter network's 4096 outputs to ONLY currently legal moves
            for move in valid_moves:
                action_idx = self._move_to_index(move[0], move[1])
                q_val = q_values[action_idx].item()
                if q_val > max_q:
                    max_q = q_val
                    best_move = move
                    
            return best_move

    def _get_all_valid_moves(self):
        """Builds a mathematical list of all strictly legal chess moves."""
        moves = []
        for r in range(1, 9):
            for c in range(1, 9):
                tile = Board.TileList[r][c]
                if tile.piece and tile.piece.get_color() == self.color:
                    for move_str in tile.piece.can_move_to():
                        row = int(move_str[1])
                        col = ord(move_str[0]) - ord('a') + 1
                        target = Board.TileList[row][col]
                        moves.append((tile, target))
        return moves

    def memorize(self, state, action, reward, next_state, done, next_valid_action_indices=None):
        """Stores experience tuples into replay memory for training."""
        if action[0] is None or action[1] is None:
            return # Don't memorize invalid actions
        if next_valid_action_indices is None:
            next_valid_action_indices = []
        action_idx = self._move_to_index(action[0], action[1])
        self.memory.append((state, action_idx, reward, next_state, done, next_valid_action_indices))

    def _batched_double_dqn_next_q(self, next_states, next_valid_actions):
        """
        Double DQN target calculation over legal actions only.
        The online network selects the best legal action and the target network evaluates it.
        """
        batch_size = next_states.size(0)

        with torch.no_grad():
            online_q_all = self.model(next_states)
            target_q_all = self.target_net(next_states)

            legal_mask = torch.zeros_like(target_q_all, dtype=torch.bool, device=self.device)
            has_legal = torch.zeros(batch_size, dtype=torch.bool, device=self.device)

            for i, valid_actions in enumerate(next_valid_actions):
                if valid_actions:
                    idx_tensor = torch.tensor(valid_actions, dtype=torch.long, device=self.device)
                    legal_mask[i, idx_tensor] = True
                    has_legal[i] = True

            masked_online_q = online_q_all.masked_fill(~legal_mask, float("-inf"))
            best_next_actions = masked_online_q.argmax(dim=1, keepdim=True)
            selected_target_q = target_q_all.gather(1, best_next_actions).squeeze(1)
            max_next_q = torch.where(has_legal, selected_target_q, torch.zeros_like(selected_target_q))

            return max_next_q

    def train(self):
        """
        Samples a mini-batch from experience memory and applies gradient 
        descent backpropagation via Bellman Equation Loss.
        """
        if len(self.memory) < self.batch_size:
            return # Wait until enough random interactions exist
            
        batch = random.sample(self.memory, self.batch_size)
        
        states, actions, rewards, next_states, dones, next_valid_actions = zip(*batch)
        
        states = torch.stack(states)
        actions = torch.tensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        next_states = torch.stack(next_states)
        dones = torch.tensor(dones, dtype=torch.float32).to(self.device)
        
        # Get Q-values for actions that were actually taken
        current_q = self.model(states).gather(1, actions).squeeze(1)
        
        # Double DQN target over legal actions only.
        max_next_q = self._batched_double_dqn_next_q(next_states, next_valid_actions)
        expected_q = rewards + self.gamma * max_next_q * (1 - dones)
            
        # Calculate Loss and Backpropagate Error
        loss = self.criterion(current_q, expected_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

    def decay_epsilon(self):
        """Decays exploration once per episode instead of once per gradient step."""
        if self.epsilon > self.epsilon_min:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def update_target_network(self):
        """Hard copies the Policy Network weights to the Target Network."""
        self.target_net.load_state_dict(self.model.state_dict())

    def save_model(self, path="chess_brain.pth"):
        """Saves the neural network weights, optimizer, and epsilon to a file."""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episode': self.episode
        }
        torch.save(checkpoint, path)

    def load_model(self, path="chess_brain.pth", load_training_state=False):
        """
        Loads the neural network weights from a file.
        If load_training_state=True, also restores optimizer (momentum) and epsilon.
        Use True for TRAINING and False for PLAYING/EVALUATION.
        """
        try:
            checkpoint = torch.load(path, map_location=self.device)
            # 1. Always load the weights
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.target_net.load_state_dict(checkpoint['model_state_dict'])
            
            # 2. Optionally load training progress
            if load_training_state:
                if 'optimizer_state_dict' in checkpoint:
                    self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                if 'epsilon' in checkpoint:
                    self.epsilon = checkpoint['epsilon']
                if 'episode' in checkpoint:
                    self.episode = checkpoint['episode']
                self.model.train()
                print(f"Loaded FULL training state from {path} (Epsilon: {self.epsilon:.3f}) (Episode: {self.episode})")
            else:
                self.model.eval() # Set to evaluation mode for playing
                # print(f"Loaded WEIGHTS ONLY from {path} (Pure Playing Mode)")

        except FileNotFoundError:
            print(f"No existing model found at {path}. Starting from scratch.")
        except Exception as e:
            print(f"Error loading checkpoint: {e}. Starting from scratch.")
