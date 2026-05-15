from abc import ABC, abstractmethod
from game.game import BackgammonGame
from game.board import Player, Board

class ScoringFunction(ABC):
    def __init__(self, name: str):
        self.name = name

    def calculate_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        if not move_success:
            return -8.0
        
        if game_over:
            result = game.get_result()
            assert result is not None
            if result.winner == player:
                return 8.0 * result.points
            else:
                return -8.0 * result.points
            
        return self.custom_reward(game, player, move_success, game_over)

    @abstractmethod
    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        pass

    def _count_blots(self, board: Board, player: Player) -> int:
        blots = 0
        for i in range(24):
            tokens = board.get_tokens(i)
            if player == Player.WHITE:
                if tokens == 1:
                    blots += 1
            else:
                if tokens == -1:
                    blots += 1
        return blots
    
    def _calculate_pip_count(self, board: Board, player: Player) -> int:
        total = 0
        for i in range(24):
            tokens = board.get_tokens(i)
            if player == Player.WHITE:
                if tokens > 0:
                    total += tokens * i
            else:
                if tokens < 0:
                    total += abs(tokens) * (24 - i)
        
        bar_tokens = board.tokens_on_bar(player)
        total += bar_tokens * 25

        return total
        

class WinLossScoring(ScoringFunction):
    def __init__(self):
        super().__init__("winloss")

    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        return 0.01
    
class PipCountScoring(ScoringFunction):
    def __init__(self):
        super().__init__("pipcount")

    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        board = game.get_board()
        opponent = player.opponent()

        player_pips = self._calculate_pip_count(board, player)
        opponent_pips = self._calculate_pip_count(board, opponent)

        pip_diff = opponent_pips - player_pips
        return 0.01 + pip_diff * 0.001
    
class BlotPenaltyScoring(ScoringFunction):
    def __init__(self):
        super().__init__("blotpenalty")

    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        board = game.get_board()
        player_blots = self._count_blots(board, player)
        oppenent_blots = self._count_blots(board, player.opponent())

        blot_diff = player_blots - oppenent_blots

        return 0.01 - blot_diff * 0.1
    
class CombinedScoring(ScoringFunction):
    def __init__(self):
        super().__init__("combined")

    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        board = game.get_board()
        opponent = player.opponent()
        
        # Pip count component
        player_pips = self._calculate_pip_count(board, player)
        opponent_pips = self._calculate_pip_count(board, opponent)
        pip_reward = (opponent_pips - player_pips) / 167.0
        
        # Bearing off component
        tokens_off = board.tokens_off_board(player)
        opponent_off = board.tokens_off_board(opponent)
        bearing_reward = (tokens_off - opponent_off) / 15.0
        
        # Blot penalty component
        player_blots = self._count_blots(board, player)
        opponent_blots = self._count_blots(board, opponent)
        blot_reward = (opponent_blots - player_blots) / 15
        
        # Bar penalty
        bar_penalty = -board.tokens_on_bar(player) / 15
        bar_reward = board.tokens_on_bar(opponent) / 15
        
        total_reward = 0.3 * pip_reward + 0.4 * bearing_reward + 0.2 * blot_reward + 0.05 * bar_penalty + 0.05 * bar_reward
        
        return total_reward
    
class AdvancedScoring(ScoringFunction):
    def __init__(self):
        super().__init__("advanced")

    def custom_reward(self, game: BackgammonGame, player: Player, move_success: bool, game_over: bool) -> float:
        board = game.get_board()
        opponent = player.opponent()

        player_weighted_pips = self._calculate_weighted_pip_count(board, player)
        opponent_weighted_pips = self._calculate_weighted_pip_count(board, opponent)
        pip_reward = (opponent_weighted_pips - player_weighted_pips) / 250.0

        tokens_off = board.tokens_off_board(player)
        opponent_off = board.tokens_off_board(opponent)
        bearing_reward = (tokens_off - opponent_off) / 15.0

        prime_reward = self._calculate_prime_strength(board, player) / 10.0

        back_token_penalty = self._calculate_back_token_penalty(board, player)

        escape_bonus = self._calculate_escape_bonus(board, player)

        player_blots = self._count_blots(board, player)
        opponent_blots = self._count_blots(board, opponent)
        blot_reward = (opponent_blots - player_blots) / 15.0

        bar_penalty = -board.tokens_on_bar(player) / 15.0
        bar_reward = board.tokens_on_bar(opponent) / 15.0

        total_reward = (
            0.25 * pip_reward + 
            0.25 * bearing_reward + 
            0.15 * prime_reward + 
            0.15 * back_token_penalty + 
            0.1 * escape_bonus +
            0.05 * blot_reward +
            0.025 * bar_penalty +
            0.025 * bar_reward)

        return total_reward
    
    def _calculate_weighted_pip_count(self, board: Board, player: Player):
        total = 0

        for i in range(24):
            tokens = board.get_tokens(i)
            
            if player == Player.WHITE:
                if tokens > 0:
                    distance = i
                    if i >= 18:
                        weight = 2.0
                    elif i >= 12:
                        weight = 1.5
                    elif i >= 6:
                        weight = 1.2
                    else:
                        weight = 1.0
                    
                    total += tokens * distance * weight
            else:
                if tokens < 0:
                    distance = 23 - i
                    if i <= 5:
                        weight = 2.0
                    elif i <= 11:
                        weight = 1.5
                    elif i <= 17:
                        weight = 1.2
                    else:
                        weight = 1.0
                    
                    total += abs(tokens) * distance * weight
        
        bar_tokens = board.tokens_on_bar(player)
        total += bar_tokens * 25 * 2.0

        return total
    
    def _calculate_prime_strength(self, board: Board, player: Player) -> float:
        max_consecutive = 0
        current_consecutive = 0
        prime_value = 0

        for i in range(24):
            if board.is_line_occupied_by(i, player) and board.get_tokens(i) >= 2:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        if max_consecutive >= 2:
            prime_value = (max_consecutive - 1) * max_consecutive / 2.0
        
        if max_consecutive >= 6:
            prime_value += 5

        return prime_value
    
    def _calculate_back_token_penalty(self, board: Board, player: Player):
        penalty = 0.0

        if player == Player.WHITE:
            for i in range(18, 24):
                if board.get_tokens(i) > 0:
                    tokens = board.get_tokens(i)
                    distance = (i - 17) / 6.0
                    penalty -= tokens * distance
        else:
            for i in range(0, 6):
                if board.get_tokens(i) < 0:
                    tokens = abs(board.get_tokens(i))
                    distance = (6 - i) / 6.0
                    penalty -= tokens * distance

        return penalty
    
    def _calculate_escape_bonus(self, board: Board, player: Player):
        escaped_tokens = 0
        total_back_tokens = 0

        if player == Player.WHITE:
            for i in range(18, 24):
                if board.get_tokens(i) > 0:
                    total_back_tokens += board.get_tokens(i)
            
        else:
            for i in range(0, 6):
                if board.get_tokens(i) < 0:
                    total_back_tokens += abs(board.get_tokens(i))

        if total_back_tokens == 0 and board.tokens_on_bar(player) == 0:
            return 1.0
        
        escaped_tokens = 15 - total_back_tokens  - board.tokens_on_bar(player)
        return escaped_tokens / 15.0

# Registry of available scoring functions
SCORING_FUNCTIONS = {
    "winloss": WinLossScoring,
    "pipcount": PipCountScoring,
    "blotpenalty": BlotPenaltyScoring,
    "combined": CombinedScoring,
    "advanced": AdvancedScoring
}


def get_scoring_function(name: str) -> ScoringFunction:
    """Get a scoring function by name."""
    if name not in SCORING_FUNCTIONS:
        raise ValueError(f"Unknown scoring function: {name}. Available: {list(SCORING_FUNCTIONS.keys())}")
    return SCORING_FUNCTIONS[name]()