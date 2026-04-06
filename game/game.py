from typing import List, Optional, Tuple
from .board import Board, Player
from .dice import Dice
from .move import Move, MoveValidator

class GameResult:
    """
    Represents the result of a completed game.
    """

    def __init__(self, winner: Player, is_gammon: bool = False,
                 is_backgammon: bool = False):
        """
        Constructor
        Args:
            winner: the player who won the game
            is_gammon: whether the winner won by gammon
            is_backgammon: whether the winner won by backgammon
        """
        self.winner = winner
        self.is_gammon = is_gammon
        self.is_backgammon = is_backgammon
        self.points = 3 if is_backgammon else (2 if is_gammon else 1)
        pass

class BackgammonGame:
    """
    Game controller.
    """

    def __init__(self):
        """
        Constructor
        """
        self.board = Board()
        self.current_player: Optional[Player] = None
        self.current_dice: Optional[Tuple[int, int]] = None
        self.available_dice: List[int] = []
        self.current_moves: List[Move] = [] # Moves made (keep track for undo)
        self.game_started = False
        self.game_over = False
        self.result: Optional[GameResult] = None
        # (move, board_state_before)
        self.move_history: List[Tuple[Move, Board]] = [] 

    def start_game(self) -> Player:
        """
        Start a new game.
        Retrurns:
            the player who goes first (white by default)
        """
        self.current_player = Player.WHITE

        roll = Dice.roll()
        # Normally, both players roll the dice and the higher one starts the
        # game (doubles are worth more than singles). This way, a (1, 2) dice
        # roll can never start the game.
        while roll == (2, 1) or roll == (1,2):
            roll = Dice.roll()

        self.current_dice = roll
        self.available_dice = Dice.get_moves(roll)
        self.game_started = True

        return self.current_player
    
    def roll_dice(self) -> Tuple[int, int]:
        """
        Roll the dice for the current player. Can be called only at the start
        of a turn.
        Returns:
            the dice roll as a tuple of two integers
        """
        if not self.game_started:
            raise RuntimeError("Game has not started yet")
        
        if self.game_over:
            raise RuntimeError("Game is over")
        
        if self.available_dice:
            raise RuntimeError("Current turn is not finished yet")
        
        self.current_dice = Dice.roll()
        self.available_dice = Dice.get_moves(self.current_dice)
        self.current_moves = []
        self.move_history = []

        return self.current_dice
    
    def get_current_dice(self) -> Optional[Tuple[int, int]]:
        """
        Get the current dice roll.
        Returns:
            the current dice roll or None if no roll has been made
        """
        return self.current_dice
    
    def get_available_dice(self) -> List[int]:
        """
        Get the available dice values that can still be used.
        Returns:
            list of available dice values 
        """
        return self.available_dice.copy()
    
    def get_legal_move_sequence(self) -> List[List[Move]]:
        """
        Get all possible legal move sequences for current dice.
        Returns:
            list of posible move sequences
        """
        if not self.available_dice or self.current_player is None:
            return [[]]
        
        return MoveValidator.get_all_legal_moves(self.board,
                                                 self.available_dice,
                                                 self.current_player)
    
    def get_legal_single_moves(self) -> List[Move]:
        """
        Get all legal moves for an individual die.
        Returns:
            list of legal moves that can be made with available dice
        """
        if not self.available_dice or self.current_player is None:
            return []
        
        all_moves = []
        for die_value in set(self.available_dice):
            moves = MoveValidator._get_moves_for_die(self.board, die_value,
                                                     self.current_player)
            all_moves.extend(moves)
        
        return all_moves
    
    def make_move(self, move: Move) -> bool:
        """
        Make a single move.
        Args:
            move: the move to make
        Returns:
            True if the move was made successfully, False otherwise
        """
        if not self.available_dice or self.current_player is None:
            return False
        
        if move.die_value not in self.available_dice:
            return False
        
        if not MoveValidator.is_valid_move(self.board, move,
                                           self.current_player):
            return False
        
        board_copy = self.board.copy()
        self.move_history.append((move, board_copy))

        MoveValidator.execute_move(self.board, move, self.current_player)
        self.current_moves.append(move)

        self.available_dice.remove(move.die_value)

        if self.board.tokens_off_board(self.current_player) == 15:
            self._end_game()

        return True
    
    def make_moves(self, moves: List[Move]) -> bool:
        """
        Make a sequence of moves.
        Args:
            moves: list of moves to make
        Returns:
            True if all moves were made successfully, False otherwise
        """
        if self.current_player is None:
            return False
        
        temp_board = self.board.copy()
        temp_dice = self.available_dice.copy()

        for move in moves:
            if move.die_value not in temp_dice:
                return False
            
            if not MoveValidator.is_valid_move(temp_board, move,
                                               self.current_player):
                return False
            
            MoveValidator.execute_move(temp_board, move, self.current_player)
            temp_dice.remove(move.die_value)
        
        for move in moves:
            self.make_move(move)
        
        return True

    def undo_last_move(self) -> bool:
        """
        Undo the lasy move made in the current turn.
        Returns:
            True if a move was undone, False if there are no moves to undo
        """
        if not self.move_history:
            return False
        
        move, board_state = self.move_history.pop()
        self.board = board_state
        self.available_dice.append(move.die_value)
        self.current_moves.pop()

        return True
    
    def can_undo(self) -> bool:
        """
        Check if there are moves to undo.
        Returns:
            True if there are moves to undo, False otherwise
        """
        return len(self.move_history) > 0
    
    def get_current_turn_moves(self) -> List[Move]:
        """
        Get all moves made in the current turn.
        Returns:
            list of moves made in current turn
        """
        return self.current_moves.copy()
    
    def end_turn(self) -> bool:
        """
        End the current turn and switch the player.
        Returns:
            True if the turn was ended successfully, False if there are
            remaining dice
        """
        if self.game_over:
            return True
        
        if self.available_dice:
            legal_moves = self.get_legal_move_sequence()
            if legal_moves and legal_moves[0]:
                return False
            
        self.current_player = self.current_player.opponent() # type: ignore
        self.current_dice = None
        self.available_dice = []
        self.current_moves = []
        self.move_history = []

        return True
    
    def force_end_turn(self):
        """
        Force end turn without checking for remaining legal moves.
        """
        if self.game_over:
            return
        
        self.current_player = self.current_player.opponent() # type: ignore
        self.current_dice = None
        self.available_dice = []
        self.current_moves = []
        self.move_history = []

    def _end_game(self):
        """
        End the game and calculate result.
        """
        self.game_over = True
        assert self.current_player is not None
        winner = self.current_player
        loser = winner.opponent()

        loser_off = self.board.tokens_off_board(loser)
        is_backgammon = False
        if loser_off == 0:
            if self.board.tokens_on_bar(loser) > 0:
                is_backgammon = True
            else:
                winner_range = (range(6)
                                if winner == Player.WHITE
                                else range(18, 24))
                for i in winner_range:
                    if self.board.get_line_owner(i) == loser:
                        is_backgammon = True
                        break
        
        is_gammon = loser_off == 0 and not is_backgammon
        self.result = GameResult(winner, is_gammon, is_backgammon)

    def is_game_over(self) -> bool:
        """
        Check if the game is over.
        Returns:
            True if the game is over, False otherwise
        """
        return self.game_over
    
    def get_result(self) -> Optional[GameResult]:
        """
        Get the game result.
        Returns:
            game result if the game is over, None otherwise
        """
        return self.result if self.game_over else None
    
    def get_current_player(self) -> Optional[Player]:
        """
        Get the current player.
        Returns:
            current player if the game is not over, None otherwise
        """
        return self.current_player
    
    def get_board(self) -> Board:
        """
        Get the current board state.
        Returns:
            current board
        """
        return self.board
    
    def reset(self):
        """
        Reset the game to initial state.
        """
        self.__init__()
