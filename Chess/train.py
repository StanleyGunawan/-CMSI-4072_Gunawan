import argparse
import random
from datetime import datetime
from engine.board import Board
import engine.ai as ai_module

EVAL_INTERVAL = 100
EVAL_GAMES = 50
TARGET_RANDOM_EVAL_WINRATE = 0.65
EVAL_STABILITY_WINDOW = 3
EVAL_LOG_PATH = "eval_log.txt"
BEST_EVAL_MODEL_PATH = "chess_brain_best_eval.pth"
TRAIN_CHECKPOINT_PATH = BEST_EVAL_MODEL_PATH
STEP_PENALTY = -0.0005
DRAW_PENALTY = -0.05
SAVE_INTERVAL = 200
TARGET_SYNC_INTERVAL = 200
EPSILON_ADAPT_FLOOR = 0.20
MINIMAX_STAGE_ONE_EPISODE = 165000
MINIMAX_STAGE_TWO_EPISODE = 175000
MINIMAX_STAGE_ONE_PROB = 0.20
MINIMAX_STAGE_TWO_PROB = 0.50

def calculate_reward(board_manager, color_is_black=True, moves_played=0, captured_piece_type=None):
    """
    Calculates a consistent reward between -1 and 1 for an AI move.
    """
    # 1. Terminal Rewards (Game Over)
    if not board_manager.in_play:
        if board_manager.white_turn and color_is_black:
            # Black (AI) just moved and captured the King
            return 1.0  #  win reward
        elif not board_manager.white_turn and color_is_black:
            # White just moved and captured Black's King
            return -1.0 #  loss penalty

    #Draw/Stall Penalty
    if moves_played >= 150:
        return DRAW_PENALTY # Discourage dragging the game to a draw

    # Piece Capture Rewards (Material Delta)
    reward = STEP_PENALTY # Small step penalty to encourage efficiency without overpowering terminal rewards
    
    if captured_piece_type:
        piece_values = {
            "Pawn": 0.02,
            "Knight": 0.06,
            "Bishop": 0.06,
            "Rook": 0.10,
            "Queen": 0.18
        }
        # Capture bonus
        reward += piece_values.get(captured_piece_type, 0.0)
        
    return reward

def black_capture_penalty(captured_piece_type):
    """Penalty from Black's perspective when White captures a Black piece."""
    if not captured_piece_type:
        return 0.0
    piece_values = {
        "Pawn": 0.02,
        "Knight": 0.06,
        "Bishop": 0.06,
        "Rook": 0.10,
        "Queen": 0.18
    }
    return -piece_values.get(captured_piece_type, 0.0)

def get_random_white_move():
    """Helper method to generate a random move for white to train against."""
    moves = []
    for r in range(1, 9):
        for c in range(1, 9):
            tile = Board.TileList[r][c]
            if tile.piece and tile.piece.is_white():
                for move_str in tile.piece.can_move_to():
                    row = int(move_str[1])
                    col = ord(move_str[0]) - ord('a') + 1
                    target = Board.TileList[row][col]
                    moves.append((tile, target))
    if moves:
        return random.choice(moves)
    return None, None

def get_white_move(manager, opponent_ai):
    """
    Uses the per-episode White opponent choice for the full game.
    """
    if opponent_ai is not None:
        opponent_ai.manager = manager
        start_tile, end_tile = opponent_ai.get_ai_move()
        if start_tile and end_tile:
            return start_tile, end_tile

    start_tile, end_tile = get_random_white_move()
    return start_tile, end_tile

def get_white_agent(episode):
    """Chooses White's policy once per episode to keep each game consistent."""
    if episode >= MINIMAX_STAGE_TWO_EPISODE:
        minimax_prob = MINIMAX_STAGE_TWO_PROB
    elif episode >= MINIMAX_STAGE_ONE_EPISODE:
        minimax_prob = MINIMAX_STAGE_ONE_PROB
    else:
        minimax_prob = 0.0

    use_minimax = random.random() < minimax_prob
    if use_minimax :
        white_opponent = ai_module.AI(None, depth= 2)
        return white_opponent
    return None

def evaluate(agent, num_games=EVAL_GAMES, max_moves=250, show_gui=False):
    """
    Runs evaluation-only games with epsilon forced to 0.0.
    Tests against two opponents: Pure Random and Minimax Depth 2.
    """
    original_epsilon = agent.epsilon
    agent.epsilon = 0.0
    
    # We split games 50/50 between Random and Minimax for evaluation
    games_per_type = num_games // 2
    results = {
        "random": {"wins": 0, "losses": 0, "draws": 0},
        "minimax": {"wins": 0, "losses": 0, "draws": 0}
    }
    total_steps = 0

    for opponent_type in ["random", "minimax"]:
        white_opponent = ai_module.AI(None, depth=2) if opponent_type == "minimax" else None
        
        for games in range(games_per_type):     
            Board()
            from engine.board_manager import Board_manager

            manager = Board_manager(ai_object=agent, load_default_ai=False)
            moves_played = 0

            #Enables GUI
            display = None
            images = None
            screen = None
            if show_gui:
                import pygame
                from engine.board_display import BoardDisplay, SCREEN_WIDTH, SCREEN_HEIGHT

                pygame.init()
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                pygame.display.set_caption(f"Training Observer - Episode {games}")
                display = BoardDisplay()
                display.manager = manager
                images = display.load_images()

            while manager.in_play and moves_played < max_moves:
                if show_gui:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return 
                if manager.white_turn:
                    start_tile, end_tile = get_white_move(manager, white_opponent)
                    if start_tile and end_tile:
                        manager.selected_tile = start_tile
                        manager.execute_move(end_tile)
                    else:
                        manager.in_play = False
                else:
                    start_tile, end_tile = agent.get_ai_move()
                    if start_tile and end_tile:
                        manager.selected_tile = start_tile
                        manager.execute_move(end_tile)
                    else:
                        manager.in_play = False
                moves_played += 1
                if show_gui:
                    pygame.event.pump() 
                    screen.fill((220, 220, 220))
                    display.draw_board(screen)
                    display.draw_coordinates(screen)
                    display.draw_highlights(screen)
                    display.draw_pieces(screen, images)
                    display.draw_sidebar(screen)
                    pygame.display.flip()
                    pygame.time.delay(100) 

            total_steps += moves_played
            if not manager.in_play:
                if manager.white_turn: results[opponent_type]["wins"] += 1
                else: results[opponent_type]["losses"] += 1
            else:
                results[opponent_type]["draws"] += 1

    agent.epsilon = original_epsilon

    # Combined stats for backward compatibility
    total_wins = results["random"]["wins"] + results["minimax"]["wins"]
    total_games = num_games
    
    return {
        "random": results["random"],
        "minimax": results["minimax"],
        "winrate_random": results["random"]["wins"] / games_per_type,
        "winrate_minimax": results["minimax"]["wins"] / games_per_type,
        "winrate": total_wins / total_games,
        "avg_steps": total_steps / total_games,
        "games": total_games,
    }

def append_eval_log(message):
    """Appends a timestamped evaluation message to the evaluation log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(EVAL_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def train(show_gui=True, max_episodes=None):
    print("Initializing RL Agent...")

    from engine.reinforcement_learning import ReinforcementLearning
    
    agent = ReinforcementLearning(epsilon=1.0)
    agent.load_model(load_training_state=True) # Load model AND training state (including epsilon)
    episode = agent.episode
    
    print(f"Starting Training Session with Epsilon: {agent.epsilon:.3f}")
    
    num_episodes = (episode + max_episodes) if max_episodes is not None else (100000 + episode)
    
    wins = 0
    losses = 0
    draws = 0
    eval_history = []
    best_eval_winrate = -1.0
    
    while episode < num_episodes:
        # Update the agent's episode count so it gets saved correctly
        Board() # Resets the global Board.TileList
        from engine.board_manager import Board_manager

        manager = Board_manager(ai_object=agent, load_default_ai=False)
        white_opponent = get_white_agent(episode)
        base_epsilon = agent.epsilon

        if white_opponent is not None:   # minimax episode
            agent.epsilon = max(base_epsilon, 0.20)
        else:                            # random episode
            agent.epsilon = base_epsilon
        show_gui = bool(show_gui)
        display = None
        images = None
        screen = None

        if show_gui:
            import pygame
            from engine.board_display import BoardDisplay, SCREEN_WIDTH, SCREEN_HEIGHT

            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption(f"Training Observer - Episode {episode}")
            display = BoardDisplay()
            display.manager = manager
            images = display.load_images()

        moves_played = 0
        pending_ai_experience = None
        if agent.epsilon < EPSILON_ADAPT_FLOOR:
            agent.epsilon = EPSILON_ADAPT_FLOOR
        
        while manager.in_play and moves_played < 250:
            if show_gui:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return 

            if manager.white_turn:
                # White's turn (Minimax Opponent)
                captured_piece = None
                captured_type = None
                
                # Update the AI's manager before calling the function 
                start_tile, end_tile = get_white_move(manager, white_opponent)
                if start_tile and end_tile:
                    # Look ahead to see if White is about to capture an AI piece
                    captured_piece = end_tile.piece
                    captured_type = captured_piece.get_type() if captured_piece else None
                    
                    manager.selected_tile = start_tile
                    manager.execute_move(end_tile)
                else:
                    manager.in_play = False 

                # Finalize the pending Black transition after White responds.
                if pending_ai_experience:
                    state, action, reward = pending_ai_experience
                    reward += black_capture_penalty(captured_type)
                    done = not manager.in_play
                    if done:
                        # If it's White's turn and game ended, Black caused terminal win on previous move.
                        reward += 1.0 if manager.white_turn else -1.0

                    next_state = agent.get_state()
                    if done:
                        next_valid_action_indices = []
                    else:
                        next_valid_action_indices = [
                            agent._move_to_index(mv[0], mv[1]) for mv in agent._get_all_valid_moves()
                        ]

                    agent.memorize(state, action, reward, next_state, done, next_valid_action_indices)
                    agent.train()
                    pending_ai_experience = None
            else:
                # AI's turn (Black)
                state = agent.get_state()
                start_tile, end_tile = agent.get_ai_move()
                
                if start_tile and end_tile:
                    captured_piece = end_tile.piece
                    captured_type = captured_piece.get_type() if captured_piece else None
                    
                    manager.selected_tile = start_tile
                    manager.execute_move(end_tile)
                    
                    ai_reward = calculate_reward(manager, color_is_black=True, moves_played=moves_played, captured_piece_type=captured_type)
                    done = not manager.in_play

                    if done:
                        # Black ended the game with this move.
                        # ai_reward += 1.0 if manager.white_turn else -1.0
                        next_state = agent.get_state()
                        agent.memorize(state, (start_tile, end_tile), ai_reward, next_state, True, [])
                        agent.train()
                    else:
                        # Hold transition until White makes a response.
                        pending_ai_experience = (state, (start_tile, end_tile), ai_reward)
                else:
                    # Black has no legal move (treated as terminal loss for Black).
                    manager.in_play = False
                    if pending_ai_experience:
                        s, a, r = pending_ai_experience
                        next_state = agent.get_state()
                        agent.memorize(s, a, r - 1.0, next_state, True, [])
                        agent.train()
                        pending_ai_experience = None

            # Update GUI Rendering
            if show_gui:
                pygame.event.pump() 
                screen.fill((220, 220, 220))
                display.draw_board(screen)
                display.draw_coordinates(screen)
                display.draw_highlights(screen)
                display.draw_pieces(screen, images)
                display.draw_sidebar(screen)
                pygame.display.flip()
                pygame.time.delay(300) 
            moves_played += 1
            
        # If game loop exits due move cap, finalize any pending transition as draw-like outcome.
        if pending_ai_experience:
            s, a, r = pending_ai_experience
            next_state = agent.get_state()
            draw_penalty = DRAW_PENALTY if manager.in_play else 0.0
            agent.memorize(s, a, r + draw_penalty, next_state, not manager.in_play, [])
            agent.train()
            pending_ai_experience = None
            
        # Tally the results
        if not manager.in_play:
            if manager.white_turn:
                # Black (AI) just made a move that ended the game
                wins += 1
                result = "Win"
            else:
                # White (Random) just made a move that ended the game
                losses += 1
                result = "Loss"
        else:
            # Hit the 150 move limit limit (Stalemate)
            draws += 1
            result = "Draw"
            
        print(f"Ep {episode+1:03d} | Result: {result:<4} | Epsilon: {agent.epsilon:.3f} | Steps: {moves_played:<3} | Record: {wins}W - {losses}L - {draws}D | White Opponent: {'Minimax' if white_opponent else 'Random'}")

        if base_epsilon:
            agent.epsilon = base_epsilon
        agent.decay_epsilon()
        agent.episode = episode
        episode += 1

        # Save periodically
        if (episode + 1) % SAVE_INTERVAL == 0:
            agent.save_model()
            print(">>> Saved checkpoint!")
            
        # Sync network every 10 episode 
        if (episode + 1) % TARGET_SYNC_INTERVAL == 0:
            agent.update_target_network()
            print("--- Target Network Synced ---")

        # Periodic evaluation (epsilon=0) for clean, non-training strength signal.
        if (episode + 1) % EVAL_INTERVAL == 0:
            eval_stats = evaluate(agent, num_games=EVAL_GAMES)
            eval_history.append(eval_stats["winrate"]) 

            append_eval_log(
                f"[EVAL] Ep {episode+1:04d} | Total Games: {eval_stats['games']} | "
                f"WR_RAND: {eval_stats['winrate_random']:.3f} | WR_MINIMAX: {eval_stats['winrate_minimax']:.3f} | "
                f"AvgSteps: {eval_stats['avg_steps']:.1f}"
            )

            if len(eval_history) >= EVAL_STABILITY_WINDOW:
                rolling_eval = sum(eval_history[-EVAL_STABILITY_WINDOW:]) / EVAL_STABILITY_WINDOW
                if rolling_eval < TARGET_RANDOM_EVAL_WINRATE:
                    append_eval_log(
                        f"[EVAL NOTICE] Rolling win rate ({rolling_eval:.3f}) < target ({TARGET_RANDOM_EVAL_WINRATE:.2f})."
                    )

            if eval_stats["winrate"] >= best_eval_winrate:
                best_eval_winrate = eval_stats["winrate"]
                agent.save_model(path=BEST_EVAL_MODEL_PATH)
                append_eval_log(
                    f"[EVAL BEST] Saving to {BEST_EVAL_MODEL_PATH} (Overall WR: {best_eval_winrate:.3f})"
                )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the chess agent.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Disable the GUI during training")
    parser.add_argument("-e", "--episodes", type=int, default=None, help="Number of training episodes to run this session")
    args = parser.parse_args()

    train(show_gui=not args.quiet, max_episodes=args.episodes)

