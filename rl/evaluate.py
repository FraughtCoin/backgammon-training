import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from environment import BackgammonEnv
from game.board import Player
from game.game import BackgammonGame


def mask_fn(env):
    return env.action_masks()


def get_observation_for_player(game: BackgammonGame, player: Player) -> np.ndarray:
    """
    Get observation from a specific player's perspective.
    """
    obs = np.zeros(106, dtype=np.float32)
    board = game.get_board()
    opponent = player.opponent()

    idx = 0

    for i in range(24):
        tokens = board.get_tokens(i)
        our_tokens = max(0, tokens) if player == Player.WHITE else max(0, -tokens)
        opp_tokens = max(0, -tokens) if player == Player.WHITE else max(0, tokens)

        obs[idx] = our_tokens / 15.0
        obs[idx + 1] = opp_tokens / 15.0
        obs[idx + 2] = 1.0 if our_tokens == 1 else 0.0
        obs[idx + 3] = 1.0 if opp_tokens == 1 else 0.0
        idx += 4

    obs[idx] = board.tokens_on_bar(player) / 15.0
    obs[idx + 1] = board.tokens_on_bar(opponent) / 15.0
    obs[idx + 2] = board.tokens_off_board(player) / 15.0
    obs[idx + 3] = board.tokens_off_board(opponent) / 15.0
    idx += 4

    available_dice = sorted(game.get_available_dice())
    for i in range(4):
        obs[idx + i] = available_dice[i] / 6.0 if i < len(available_dice) else 0.0
    idx += 4

    obs[idx] = len(available_dice) / 4.0
    idx += 1

    current_player = game.get_current_player()
    obs[idx] = 1.0 if current_player == player else 0.0

    idx += 1
    assert idx == 106, f"Observation index {idx} does not match expected size 106"

    return obs


def get_action_masks_for_player(game: BackgammonGame, player: Player, env: BackgammonEnv) -> np.ndarray:
    """
    Get action masks for a specific player.
    """
    mask = np.zeros(env.action_space_size, dtype=np.int8)

    current_player = game.get_current_player()
    is_game_over = game.is_game_over()
    
    if current_player != player or is_game_over:
        return mask
    
    legal_moves = game.get_legal_single_moves()

    if len(legal_moves) == 0:
        mask[0] = 1
        return mask
    
    for move in legal_moves:
        action = env._move_to_action(move)
        mask[action] = 1
    
    return mask

def evaluate_models(white_model_path: str, black_model_path: str, num_games: int = 100):
    """
    Evaluate two trained models against each other.
    Args:
        white_model_path: Path to white player model
        black_model_path: Path to black player model
        num_games: Number of games to play
    """
    
    print("Loading models")
    model_white = MaskablePPO.load(white_model_path)
    model_black = MaskablePPO.load(black_model_path)
    
    # Create a dummy environment just for action mapping
    env = BackgammonEnv(player=Player.WHITE, opponent_policy=None)
    
    white_wins = 0
    black_wins = 0
    total_points_white = 0
    total_points_black = 0
    
    normal_wins = {"white": 0, "black": 0}
    gammon_wins = {"white": 0, "black": 0}
    backgammon_wins = {"white": 0, "black": 0}
    
    white_starts_wins = 0
    black_starts_wins = 0
    white_starts_count = 0
    black_starts_count = 0
    
    total_moves = []
    
    print(f"Starting evaluation for {num_games} games\n")
    
    for game_num in range(num_games):
        game = BackgammonGame()
        game.reset()
        first_player = game.start_game()
        
        if first_player == Player.WHITE:
            white_starts_count += 1
        else:
            black_starts_count += 1
        
        done = False
        move_count = 0
        
        while not done:
            current_player = game.get_current_player()
            assert current_player is not None
            
            if current_player == Player.WHITE:
                current_model = model_white
            else:
                current_model = model_black
            
            obs = get_observation_for_player(game, current_player)
            action_masks = get_action_masks_for_player(game, current_player, env)
            action, _ = current_model.predict(obs, action_masks=action_masks)
            action = int(action)
            
            # Skip action
            if action == 0:
                legal_moves = game.get_legal_single_moves()
                if len(legal_moves) == 0:
                    can_end = game.end_turn()
                    if not can_end:
                        game.force_end_turn()
                    
                    if not game.is_game_over():
                        game.roll_dice()

            else:
                move = env._action_to_move(action)
                assert move is not None
                success = game.make_move(move)
                
                if not success:
                    # Force skip on invalid move
                    legal_moves = game.get_legal_single_moves()
                    if len(legal_moves) == 0:
                        can_end = game.end_turn()
                        if not can_end:
                            game.force_end_turn()
                        if not game.is_game_over():
                            game.roll_dice()
                else:
                    # Check if turn should end
                    legal_moves = game.get_legal_single_moves()
                    if len(legal_moves) == 0:
                        can_end = game.end_turn()
                        if not can_end:
                            game.force_end_turn()
                        if not game.is_game_over():
                            game.roll_dice()
            
            move_count += 1
            done = game.is_game_over()

        total_moves.append(move_count)
        
        # Check winner
        result = game.get_result()
        if result:
            winner = result.winner
            if winner == Player.WHITE:
                white_wins += 1
                total_points_white += result.points
                if first_player == Player.WHITE:
                    white_starts_wins += 1
                
                if result.is_backgammon:
                    backgammon_wins["white"] += 1
                elif result.is_gammon:
                    gammon_wins["white"] += 1
                else:
                    normal_wins["white"] += 1
            else:
                black_wins += 1
                total_points_black += result.points
                if first_player == Player.BLACK:
                    black_starts_wins += 1
                
                if result.is_backgammon:
                    backgammon_wins["black"] += 1
                elif result.is_gammon:
                    gammon_wins["black"] += 1
                else:
                    normal_wins["black"] += 1
        
        if (game_num + 1) % 10 == 0:
            print(f"Games played: {game_num + 1}/{num_games} - White: {white_wins}, Black: {black_wins}")
    
    print(f"\n{'='*60}")
    print(f"Evaluation Results ({num_games} games)")
    print(f"{'='*60}")
    print(f"White wins: {white_wins} ({white_wins/num_games*100:.1f}%)")
    print(f"Black wins: {black_wins} ({black_wins/num_games*100:.1f}%)")
    print(f"\nWin Types:")
    print(f"  White - Normal: {normal_wins['white']}, Gammon: {gammon_wins['white']}, Backgammon: {backgammon_wins['white']}")
    print(f"  Black - Normal: {normal_wins['black']}, Gammon: {gammon_wins['black']}, Backgammon: {backgammon_wins['black']}")
    print(f"\nStarter Advantage:")
    print(f"  White started: {white_starts_count} games, won: {white_starts_wins}")
    print(f"  Black started: {black_starts_count} games, won: {black_starts_wins}")
    print(f"\nPoints:")
    print(f"  White total: {total_points_white} (avg: {total_points_white/num_games:.2f})")
    print(f"  Black total: {total_points_black} (avg: {total_points_black/num_games:.2f})")
    print(f"\nGame Length:")
    print(f"  Average moves: {np.mean(total_moves):.1f}")
    print(f"  Min moves: {np.min(total_moves)}")
    print(f"  Max moves: {np.max(total_moves)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    evaluate_models(
        white_model_path="./models/white_advanced_final",
        black_model_path="./models/black_winloss_final",
        num_games=100
    )
