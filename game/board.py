from typing import List, Optional
from enum import Enum

class Player(Enum):
    WHITE = 1
    BLACK = -1

    def opponent(self):
        return Player.BLACK if self == Player.WHITE else Player.WHITE
    
class Board:
    """
    Backgammon board.

    The board is numbered from 0 to 24, 0 representing the first line in white's
    home board and 23 representing the first line in black's home board.

    The board is saved as a list, and each value represents the number of tokens
    a player has on that line: a positive value means white tokens, a negative
    value means black tokens.
    """

    def __init__(self):
        """Initialize the board with standard backgammon starting position."""
        self.lines: List[int] = [0] * 24
        self.bar = {Player.WHITE: 0, Player.BLACK: 0}
        self.off = {Player.WHITE: 0, Player.BLACK: 0}

        # White pieces
        self.lines[5] = 5
        self.lines[7] = 3
        self.lines[12] = 5
        self.lines[23] = 2

        # Black pieces
        self.lines[0] = -2
        self.lines[11] = -5
        self.lines[16] = -3
        self.lines[18] = -5

    def get_tokens(self, line: int) -> int:
        """
        Get the number of tokens at a specific line.
        Args:
            line: line number
        """
        return self.lines[line]
    
    def set_tokens(self, line: int, value: int):
        """
        Set the number of tokens at a specific line.
        Args:
            line: line number
            value: number of tokens to set
        """
        self.lines[line] = value

    def get_line_owner(self, line: int) -> Optional[Player]:
        """
        Get the player who owns tokens on a specific line.
        Args:
            line: line number
        Returns:
            player
        """
        value = self.get_tokens(line)
        if value > 0:
            return Player.WHITE
        elif value < 0:
            return Player.BLACK
        return None
    
    def get_tokens_count(self, line: int) -> int:
        """
        Get the number of tokens on a line.
        Args:
            line: line number
        Returns:
            number of tokens on the line
        """
        return abs(self.get_tokens(line))
    
    def is_line_occupied_by(self, line: int, player: Player) -> bool:
        """
        Check if a line is occupied by a specific player.
        Args:
            line: line number
            player: player to check
        Returns:
            True if the line is occupied by the player, False otherwise
        """
        value = self.get_tokens(line)
        return ((player == Player.WHITE and value > 0)
                or (player == Player.BLACK and value < 0))
    
    def is_line_blocked(self, line: int, player: Player) -> bool:
        """
        Check if a line is blocked for a player (the opponent has 2+ tokens).
        Args:
            line: line number
            player: player to check
        Returns:
            True if the line is blocked for the player, False otherwise
        """
        value = self.get_tokens(line)
        if player == Player.WHITE:
            return value < -1
        else:
            return value > 1
        
    def is_token_alone(self, line: int) -> bool:
        """
        Check if a line has only one token
        Args:
            line: line number
        Returns:
            True if the line has only one token, False otherwise
        """
        return abs(self.get_tokens(line)) == 1

    def add_token(self, line: int, player: Player):
        """
        Add a token to a specific line for a player.
        Args:
            line: line number
            player: player adding the token
        """
        if player == Player.WHITE:
            self.lines[line] += 1
        else:
            self.lines[line] -= 1

    def remove_token(self, line: int, player: Player):
        """
        Remove a token from a specific line for a player.
        Args:
            line: line number
            player: player removing the token
        """
        if player == Player.WHITE:
            self.lines[line] -= 1
        else:
            self.lines[line] += 1

    def hit_token(self, line: int):
        """
        Hit a token on a specific line (move it to the bar).
        Args:
            line: line number
        """
        value = self.get_tokens(line)
        if abs(value) == 1:
            player = self.get_line_owner(line)
            if player:
                self.remove_token(line, player)
                self.bar[player] += 1
            self.set_tokens(line, 0)

    def tokens_on_bar(self, player: Player) -> int:
        """
        Get the number of tokens on the bar for a player.
        Args:
            player: player to check
        Returns:
            number of tokens on the bar for the player
        """
        return self.bar[player]
    
    def tokens_off_board(self, player: Player) -> int:
        """
        Get the number of tokens off the board for a player.
        Args:
            player: player to check
        Returns:
            number of tokens off the board for the player
        """
        return self.off[player]
    
    def all_in_home_board(self, player: Player) -> bool:
        """
        Check if all tokens of a player are in the home board.
        Args:
            player: player to check
        Returns:
            True if all tokens are in the home board, False otherwise
        """
        if self.tokens_on_bar(player) > 0:
            return False
        
        player_range = range(6, 24) if player == Player.WHITE else range(0, 18)
        for line in player_range:
            if self.is_line_occupied_by(line, player):
                return False
        
        return True
    
    def get_total_tokens(self, player: Player) -> int:
        """
        """
        total = self.tokens_on_bar(player) + self.tokens_off_board(player)
        for line_value in self.lines:
            if player == Player.WHITE and line_value > 0:
                total += line_value
            elif player == Player.BLACK and line_value < 0:
                total += abs(line_value)
        return total
    
    def copy(self) -> 'Board':
        """
        Create a deep copy of the board.
        """
        new_board = Board()
        new_board.lines = self.lines.copy()
        new_board.bar = self.bar.copy()
        new_board.off = self.off.copy()
        return new_board