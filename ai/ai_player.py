import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from sb3_contrib import MaskablePPO
from game import Move, Player, BackgammonGame
from game.board import Board

class AIPlayer(ABC):
    """
    Abstract base class for AI players.
    """
    
    def __init__(self, player: Player):
        """
        Constructor
        Args:
            player: the player color (WHITE or BLACK) this AI controls
        """
        self.player = player
    
    @abstractmethod
    def select_move(self, game: BackgammonGame) -> Optional[Move]:
        """
        Select a single move given the current game state.
        Args:
            game: the current game state
        Returns:
            move to make, or None if no moves available
        """
        pass

class MaskablePPOPlayer(AIPlayer):
    """
    AI player that uses a trained MaskablePPO model to select moves.
    """
    
    def __init__(self, player: Player, model_path: str):
        """
        Constructor
        Args:
            player: the player color this AI controls
            model_path: path to the trained model file (without extension)
        """
        super().__init__(player)
        self.model_path = model_path
        self.model = self._load_model(model_path)
        
        # Build action mapping (same as in environment)
        self._actions_to_move_cache = {}
        self._move_to_action_cache = {}
        self._build_action_mapping()
    
    def _load_model(self, model_path: str) -> MaskablePPO:
        """
        Load the trained MaskablePPO model from file.
        Args:
            model_path: path to model file
        Returns:
            loaded MaskablePPO model
        """
        try:
            model = MaskablePPO.load(model_path)
            print(f"Successfully loaded model from {model_path}")
            return model
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            raise
    
    def _build_action_mapping(self):
        """
        Build the action-to-move mapping (same as BackgammonEnv).
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
    
    def _action_to_move(self, action: int) -> Optional[Move]:
        """
        Convert action ID to Move object.
        Args:
            action: action ID
        Returns:
            Move object or None for skip action
        """
        if action == 0:
            return None
        return self._actions_to_move_cache.get(action)
    
    def _move_to_action(self, move: Move) -> int:
        """
        Convert Move object to action ID.
        Args:
            move: Move object
        Returns:
            action ID
        """
        move_key = (move.from_line, move.to_line, move.die_value, move.is_bearing)
        return self._move_to_action_cache[move_key]
    
    def _get_observation(self, game: BackgammonGame) -> np.ndarray:
        """
        Get observation from game state (same format as BackgammonEnv).
        Args:
            game: current game state
        Returns:
            observation array
        """
        obs = np.zeros(106, dtype=np.float32)
        board = game.get_board()
        opponent = self.player.opponent()

        idx = 0

        # Board state (24 lines * 4 features)
        for i in range(24):
            tokens = board.get_tokens(i)
            our_tokens = max(0, tokens) if self.player == Player.WHITE else max(0, -tokens)
            opp_tokens = max(0, -tokens) if self.player == Player.WHITE else max(0, tokens)

            obs[idx] = our_tokens / 15.0
            obs[idx + 1] = opp_tokens / 15.0
            obs[idx + 2] = 1.0 if our_tokens == 1 else 0.0
            obs[idx + 3] = 1.0 if opp_tokens == 1 else 0.0
            idx += 4

        # Bar and off tokens
        obs[idx] = board.tokens_on_bar(self.player) / 15.0
        obs[idx + 1] = board.tokens_on_bar(opponent) / 15.0
        obs[idx + 2] = board.tokens_off_board(self.player) / 15.0
        obs[idx + 3] = board.tokens_off_board(opponent) / 15.0
        idx += 4

        # Available dice
        avail_dice = sorted(game.get_available_dice())
        for i in range(4):
            obs[idx + i] = avail_dice[i] / 6.0 if i < len(avail_dice) else 0.0
        idx += 4

        # Dice count
        obs[idx] = len(avail_dice) / 4.0
        idx += 1

        # Turn indicator
        current_player = game.get_current_player()
        obs[idx] = 1.0 if current_player == self.player else 0.0
        idx += 1

        assert idx == 106, f"Observation index {idx} does not match expected size 106"

        return obs
    
    def _get_action_mask(self, game: BackgammonGame) -> np.ndarray:
        """
        Get mask of valid actions for current game state.
        Args:
            game: current game state
        Returns:
            action mask array (1 = valid, 0 = invalid)
        """
        mask = np.zeros(3751, dtype=np.int8)

        current_player = game.get_current_player()
        is_game_over = game.is_game_over()
        
        if current_player != self.player or is_game_over:
            return mask
        
        legal_moves = game.get_legal_single_moves()

        if len(legal_moves) == 0:
            mask[0] = 1  # Skip action
            return mask
        
        for move in legal_moves:
            action = self._move_to_action(move)
            mask[action] = 1

        return mask
    
    def select_move(self, game: BackgammonGame) -> Optional[Move]:
        """
        Select a single move using the trained model.
        Args:
            game: the current game state
        Returns:
            move to make, or None if no moves available
        """
        # Check if it's our turn
        if game.get_current_player() != self.player:
            return None
        
        # Get legal moves
        legal_moves = game.get_legal_single_moves()
        
        if len(legal_moves) == 0:
            return None
        
        # Get observation and action mask
        obs = self._get_observation(game)
        action_mask = self._get_action_mask(game)
        
        # Predict action using model
        action, _states = self.model.predict(
            obs, 
            action_masks=action_mask,
            deterministic=True  # Use deterministic policy for gameplay
        )
        
        # Convert action to move
        action = int(action)
        move = self._action_to_move(action)
        
        return move

class RandomAIPlayer(AIPlayer):
    """
    AI player that selects random legal moves (for testing).
    """
    
    def __init__(self, player: Player):
        """
        Constructor
        Args:
            player: the player color this AI controls
        """
        super().__init__(player)
    
    def select_move(self, game: BackgammonGame) -> Optional[Move]:
        """
        Select a random legal move.
        Args:
            game: the current game state
        Returns:
            random move, or None if no moves available
        """
        import random
        
        if game.get_current_player() != self.player:
            return None
        
        legal_moves = game.get_legal_single_moves()
        
        if len(legal_moves) == 0:
            return None
        
        return random.choice(legal_moves)
