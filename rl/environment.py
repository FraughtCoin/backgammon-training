import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import Optional, Tuple, Dict, Any
from game.board import Player
from game.game import BackgammonGame
from game.move import Move
from rl.scoring import get_scoring_function

class BackgammonEnv(gym.Env):
    """
    Gymnasium environment for Backgammon game with support for RL training.
    """

    def __init__(self, player: Player, opponent_policy=None, render_mode: Optional[str]=None, scoring_function: str = "winloss") -> None:
        """
        Initialize the Backgammon environment for RL training.
        """
        self.player = player
        self.opponent_policy = opponent_policy
        self.render_mode = render_mode
        self.game = BackgammonGame()
        self.scoring_fn = get_scoring_function(scoring_function)

        # Observation space:
        # 198 features:
        #   - 24 lines * 4 features (our tokens, opponent tokens, our blot, opponent blot) = 96
        #   - 2 bar tokens (ours, opponent)
        #   - 2 off tokens (ours, opponent)
        #   - 4 current dice values (normalized by 6)
        #   - available dice count
        #   - turn indicator
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(106,), dtype=np.float32
        )

        # from_line (0-24, where 24 is bar) * to_line (0-24, wher 24 is bearing off) * die_value (1-6)
        # 25 * 25 * 6 = 3750
        # 1 for skipping
        self.action_space_size = 3751
        self.action_space = spaces.Discrete(self.action_space_size)

        self._actions_to_move_cache = {}
        self._move_to_action_cache = {}
        self._build_action_mapping()

    def _build_action_mapping(self):
        """
        Create maps for converting between actions and moves.
        """
        action_id = 1
        for from_line in range(25):
            for to_line in range(25):
                for die_value in range(1, 7):
                    from_pos = None if from_line == 24 else from_line
                    to_pos = None if to_line == 24 else to_line
                    is_bearing = to_line == 24

                    move = Move(from_pos, to_pos, die_value, is_bearing)
                    self._actions_to_move_cache[action_id] = move

                    move_key = (from_pos, to_pos, die_value, is_bearing)
                    self._move_to_action_cache[move_key] = action_id

                    action_id += 1

    def _move_to_action(self, move: Move) -> int:
        """
        Convert a Move object to an action ID.
        Returns:
            action id (1-3750) or 0 if move is invalid
        """
        move_key = (move.from_line, move.to_line, move.die_value, move.is_bearing)
        return self._move_to_action_cache[move_key]

    def _action_to_move(self, action: int) -> Optional[Move]:
        """
        Convert an action ID to a Move object.
        Returns:
            move object or None if action is skip
        """
        if action == 0:
            return None
        return self._actions_to_move_cache[action]

    def _get_observation(self) -> np.ndarray:
        """
        Get the current observation from the game state.
        """
        obs = np.zeros(106, dtype=np.float32)
        board = self.game.get_board()
        opponent = self.player.opponent()

        idx =  0

        for i in range(24):
            tokens = board.get_tokens(i)
            our_tokens = max(0, tokens) if self.player == Player.WHITE else max(0, -tokens)
            opp_tokens = max(0, -tokens) if self.player == Player.WHITE else max(0, tokens)

            obs[idx] = our_tokens / 15.0
            obs[idx + 1] = opp_tokens / 15.0
            obs[idx + 2] = 1.0 if our_tokens == 1 else 0.0
            obs[idx + 3] = 1.0 if opp_tokens == 1 else 0.0
            idx += 4

        obs[idx] = board.tokens_on_bar(self.player) / 15.0
        obs[idx + 1] = board.tokens_on_bar(opponent) / 15.0
        obs[idx + 3] = board.tokens_off_board(self.player) / 15.0
        obs[idx + 4] = board.tokens_off_board(opponent) / 15.0
        idx += 4

        available_dice = sorted(self.game.get_available_dice())
        for i in range(4):
            obs[idx + i] = available_dice[i] / 6.0 if i < len(available_dice) else 0.0
        idx += 4

        obs[idx] = len(available_dice) / 4.0
        idx += 1

        current_player = self.game.get_current_player()
        obs[idx] = 1.0 if current_player == self.player else 0.0

        idx += 1
        assert idx == 106, f"Observation index {idx} does not match expected size 106"

        return obs

    def action_masks(self) -> np.ndarray:
        """
        Get mask of valid actions (1 = valid, 0 = invalid).
        """
        mask = np.zeros(self.action_space_size, dtype=np.int8)

        current_player = self.game.get_current_player()
        is_game_over = self.game.is_game_over()

        if (current_player != self.player or is_game_over):
            return mask

        legal_moves = self.game.get_legal_single_moves()

        if len(legal_moves) == 0:
            mask[0] = 1
            return mask

        for move in legal_moves:
            action = self._move_to_action(move)
            mask[action] = 1

        return mask

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one move (one step = one die used).
        """

        reward = 0.0

        # No actions available
        if action == 0:
            reward, terminated = self._handle_no_moves()
            obs = self._get_observation()
            info = {
                "skip_action": True,
                "move_success": True,
                "current_player": self.game.get_current_player() if self.game.get_current_player() else None,
                "available_dice": self.game.get_available_dice().copy(),
                "game_over": self.game.is_game_over(),
                "legal_moves_count": len(self.game.get_legal_single_moves())
            }

            return obs, reward, terminated, False, info

        move = self._action_to_move(action)
        assert move is not None
        success = self.game.make_move(move)

        terminated = False
        truncated = False
        info = {
            "move_success": success,
            "move_attempted": str(move),
            "current_player": self.game.get_current_player() if self.game.get_current_player() else None,
            "available_dice": self.game.get_available_dice().copy(),
            "game_over": self.game.is_game_over(),
        }

        if not success:
            reward = self.scoring_fn.calculate_reward(self.game, self.player, False, False)
            info["invalid_move"] = True
            obs = self._get_observation()
            return obs, reward, terminated, truncated, info

        # Check if there are remaining moves
        legal_moves = self.game.get_legal_single_moves()
        if len(legal_moves) == 0:
            reward, terminated = self._handle_no_moves()
        else:
            reward = self.scoring_fn.calculate_reward(self.game, self.player, True, False)

        obs = self._get_observation()
        info["game_over"] = self.game.is_game_over()
        info["winner"] = self.game.get_result().winner.value if self.game.is_game_over() and self.game.get_result() else None # type: ignore
        info["legal_moves_count"] = len(self.game.get_legal_single_moves())

        return obs, reward, terminated, truncated, info

    def _handle_no_moves(self):
        """
        Handle the case when no legal moves are available.
        """
        can_end = self.game.end_turn()
        if not can_end:
            self.game.force_end_turn()

        reward = self.scoring_fn.calculate_reward(self.game, self.player, True, False)
        terminated = False

        if self.game.is_game_over():
            reward = self.scoring_fn.calculate_reward(self.game, self.player, True, True)
            terminated = True
        else:
            # Play oppoenent's turn
            self.game.roll_dice()

            self._play_opponent_turn()
            if self.game.is_game_over():
                reward = self.scoring_fn.calculate_reward(self.game, self.player, True, True)
                terminated = True
            else:
                # Roll the dice for out next turn
                self.game.roll_dice()

        return reward, terminated

    def _play_opponent_turn(self):
        """
        Play the opponent's complete turn (all moves until no legal moves remain).
        """
        move_count = 0

        while True:
            legal_moves = self.game.get_legal_single_moves()

            if len(legal_moves) == 0:
                break

            if self.opponent_policy is not None:
                obs = self._get_observation()
                action_mask = self.action_masks()
                action, _ = self.opponent_policy.predict(obs, action_masks=action_mask)
                action = int(action)
                if action == 0:
                    break
                move = self._action_to_move(action)
            else:
                move = random.choice(legal_moves)

            assert move is not None
            success = self.game.make_move(move)
            move_count += 1

            if not success:
                break

        can_end = self.game.end_turn()
        if not can_end:
            self.game.force_end_turn()

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to initial state.
        Args:
            seed: Random seed
            options: Additional options
        Returns:
            observation: Initial observation
            info: Additional information
        """
        super().reset(seed=seed)
        np.random.seed(seed)
        random.seed(seed)

        self.game.reset()
        first_player = self.game.start_game()

        if first_player != self.player:
            self._play_opponent_turn()
            if not self.game.is_game_over():
                self.game.roll_dice()

        obs = self._get_observation()
        info = {"player": self.player.name}

        return obs, info
