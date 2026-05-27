import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from itertools import combinations
from sb3_contrib import MaskablePPO
from environment import BackgammonEnv
from game.board import Player
from game.game import BackgammonGame


MODELS = {
    "winloss": {
        "white": "./models/white_winloss_final",
        "black": "./models/black_winloss_final",
    },
    "advanced": {
        "white": "./models/white_advanced_final",
        "black": "./models/black_advanced_final",
    },
    "pipcount": {
        "white": "./models/white_pipcount_final",
        "black": "./models/black_pipcount_final",
    },
    "blotpenalty": {
        "white": "./models/white_blotpenalty_final",
        "black": "./models/black_blotpenalty_final",
    },
    "combined": {
        "white": "./models/white_combined_final",
        "black": "./models/black_combined_final",
    },
    "combined_cross": {
        "white": "./models/white_combined_cross_final",
        "black": "./models/black_combined_cross_final",
    },
    "combined_league": {
        "white": "./models/white_combined_league_final",
        "black": "./models/black_combined_league_final",
    }
}

NUM_GAMES = 200


def get_observation_for_player(game: BackgammonGame, player: Player) -> np.ndarray:
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
    obs[idx] = 1.0 if game.get_current_player() == player else 0.0
    idx += 1

    return obs


def get_action_masks_for_player(game: BackgammonGame, player: Player, env: BackgammonEnv) -> np.ndarray:
    mask = np.zeros(env.action_space_size, dtype=np.int8)
    if game.get_current_player() != player or game.is_game_over():
        return mask

    legal_moves = game.get_legal_single_moves()
    if len(legal_moves) == 0:
        mask[0] = 1
        return mask

    for move in legal_moves:
        mask[env._move_to_action(move)] = 1
    return mask


def play_games(model_white, model_black, env: BackgammonEnv, num_games: int) -> dict:
    white_wins = 0
    black_wins = 0

    for _ in range(num_games):
        game = BackgammonGame()
        game.reset()
        game.start_game()
        done = False

        while not done:
            current_player = game.get_current_player()
            current_model = model_white if current_player == Player.WHITE else model_black

            obs = get_observation_for_player(game, current_player)
            action_masks = get_action_masks_for_player(game, current_player, env)
            action, _ = current_model.predict(obs, action_masks=action_masks)
            action = int(action)

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
                success = game.make_move(move)

                legal_moves = game.get_legal_single_moves()
                if not success or len(legal_moves) == 0:
                    can_end = game.end_turn()
                    if not can_end:
                        game.force_end_turn()
                    if not game.is_game_over():
                        game.roll_dice()

            done = game.is_game_over()

        result = game.get_result()
        if result:
            if result.winner == Player.WHITE:
                white_wins += 1
            else:
                black_wins += 1

    return {"white_wins": white_wins, "black_wins": black_wins}


def print_matrix(results: dict, agent_names: list):
    col_width = 14
    name_width = 12

    print(f"\n{'='*60}")
    print("Win Rate Matrix (row=white, col=black)")
    print(f"{'='*60}")

    header = f"{'':>{name_width}}"
    for name in agent_names:
        header += f"{name:>{col_width}}"
    print(header)

    for agent_a in agent_names:
        row = f"{agent_a:>{name_width}}"
        for agent_b in agent_names:
            if agent_a == agent_b:
                row += f"{'---':>{col_width}}"
            elif (agent_a, agent_b) in results:
                r = results[(agent_a, agent_b)]
                total = r["white_wins"] + r["black_wins"]
                winrate = r["white_wins"] / total * 100 if total > 0 else 0
                row += f"{winrate:>{col_width}.1f}%"
            else:
                row += f"{'N/A':>{col_width}}"
        print(row)

    print(f"\nOverall Win Rates (across all matchups):")
    for agent in agent_names:
        total_wins = 0
        total_games = 0
        for (a, b), r in results.items():
            if a == agent:
                total_wins += r["white_wins"]
                total_games += r["white_wins"] + r["black_wins"]
            if b == agent:
                total_wins += r["black_wins"]
                total_games += r["white_wins"] + r["black_wins"]
        if total_games > 0:
            print(f"  {agent}: {total_wins}/{total_games} ({total_wins/total_games*100:.1f}%)")


def run_tournament():
    print("Loading models...")
    loaded_models = {}
    available_agents = []

    for name, paths in MODELS.items():
        try:
            loaded_models[name] = {
                "white": MaskablePPO.load(paths["white"]),
                "black": MaskablePPO.load(paths["black"]),
            }
            available_agents.append(name)
            print(f"  Loaded {name}")
        except Exception as e:
            print(f"  Skipping {name}: {e}")

    env = BackgammonEnv(player=Player.WHITE, opponent_policy=None)
    results = {}
    pairs = list(combinations(available_agents, 2))
    total_matchups = len(pairs) * 2

    print(f"\nRunning tournament: {len(available_agents)} agents, {total_matchups} matchups, {NUM_GAMES} games each")
    print(f"Total games: {total_matchups * NUM_GAMES}\n")

    matchup_num = 0
    for agent_a, agent_b in pairs:
        # Agent A as white, Agent B as black
        matchup_num += 1
        print(f"[{matchup_num}/{total_matchups}] {agent_a} (white) vs {agent_b} (black)...")
        r = play_games(
            loaded_models[agent_a]["white"],
            loaded_models[agent_b]["black"],
            env,
            NUM_GAMES
        )
        results[(agent_a, agent_b)] = r
        print(f"  {agent_a} wins: {r['white_wins']} ({r['white_wins']/NUM_GAMES*100:.1f}%) | {agent_b} wins: {r['black_wins']} ({r['black_wins']/NUM_GAMES*100:.1f}%)")

        # Agent B as white, Agent A as black
        matchup_num += 1
        print(f"[{matchup_num}/{total_matchups}] {agent_b} (white) vs {agent_a} (black)...")
        r = play_games(
            loaded_models[agent_b]["white"],
            loaded_models[agent_a]["black"],
            env,
            NUM_GAMES
        )
        results[(agent_b, agent_a)] = r
        print(f"  {agent_b} wins: {r['white_wins']} ({r['white_wins']/NUM_GAMES*100:.1f}%) | {agent_a} wins: {r['black_wins']} ({r['black_wins']/NUM_GAMES*100:.1f}%)")

    print_matrix(results, available_agents)


if __name__ == "__main__":
    run_tournament()
