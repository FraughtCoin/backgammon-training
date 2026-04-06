from typing import List, Optional
from board import Board, Player

class Move:
    """
    Representation of a single move
    """

    def __init__(self, from_line: Optional[int], to_line: Optional[int],
                 die_value: int, is_bearing: bool = False):
        """
        Constructor
        Args:
            from_line: the line the token is moving from (None if entering
                       from bar)
            to_line: the line the token is moving to (None if bearing off)
            die_value: die value used for the move
            is_bearing: whether this move is bearing off the board
        """
        self.from_line = from_line
        self.to_line = to_line
        self.die_value = die_value
        self.is_bearing = is_bearing

class MoveValidator:
    """
    Validator and generator for backgammon moves
    """

    @staticmethod
    def get_destination_line(from_line: int, die_value: int,
                             player: Player) -> int:
        """
        Calculate destination line for a move.
        Args:
            from_line: starting line number
            die_value: die value used for movement
            player: the player making the move
        Returns:
            destination line number
        """
        if player == Player.WHITE:
            return from_line - die_value
        else:
            return from_line + die_value
        
    @staticmethod
    def get_entry_line(die_value: int, player: Player) -> int:
        """
        Get the entry line for a player entering from the bar.
        Args:
            die_value: die value used for entry
            player: the player entering from the bar
        Returns:
            entry line number
        """
        if player == Player.WHITE:
            return 24 - die_value
        else:
            return die_value - 1
        
    @staticmethod
    def can_bear_off(board: Board, from_line: int, die_value: int,
                     player: Player) -> bool:
        """
        Check if a token can be borne off the board.
        Args:
            board: the game board
            from_line: the line the token is on
            die_value: die value
            player: the player bearing off
        Returns:
            True if the token can be borne off, False otherwise
        """
        if not board.all_in_home_board(player):
            return False
        
        if player == Player.WHITE:
            if from_line > 6:
                return False
            
            if from_line == die_value:
                return True
            
            if die_value > from_line:
                for l in range(from_line + 1, 6):
                    if board.get_tokens(l) > 0:
                        return False
                    return True
            
            return False
        else:
            if from_line < 18:
                return False
            
            if from_line + die_value == 24:
                return True
            
            if from_line + die_value > 24:
                for l in range(18, from_line):
                    if board.get_tokens(l) < 0:
                        return False
                return True
            
            return False
    
    @staticmethod
    def is_valid_move(board: Board, move: Move, player: Player) -> bool:
        """
        Check if a move is valid.
        Args:
            board: the game board
            move: the move to validate
            player: the player making the move
        Returns:
            True if the move is valid, False otherwise
        """
        # Check if entering from bar
        if move.from_line is None:
            if board.tokens_off_board(player) == 0:
                return False
            
            entry_line = move.to_line
            if entry_line is None:
                return False
            
            if board.is_line_blocked(entry_line, player):
                return False
            return True
        
        # Check if bearing off
        if move.is_bearing:
            return MoveValidator.can_bear_off(board, move.from_line,
                                              move.die_value, player)
        
        # Regular move
        if not board.is_line_occupied_by(move.from_line, player):
            return False
        
        to_line = move.to_line
        if to_line is None:
            return False

        if to_line < 0 or to_line > 23:
            return False
        
        if board.is_line_blocked(to_line, player):
            return False
        
        return True
    
    @staticmethod
    def get_all_legal_moves(board: Board, dice_values: List[int],
                            player: Player) -> List[List[Move]]:
        """
        Get all legal move sequences for a player given dice values.
        Args:
            board: the game board
            dice_values: list of die values rolled
            player: the player making moves
        Returns:
            list of list of legal moves (each inner list is a sequence of moves)
        """
        if not dice_values:
            return [[]]
        
        all_sequences = []
        MoveValidator._generate_move_sequences(board.copy(), dice_values.copy(),
                                               player, [], all_sequences)
        if not all_sequences:
            return [[]]
        
        max_moves = max(len(seq) for seq in all_sequences)
        return [seq for seq in all_sequences if len(seq) == max_moves]

    @staticmethod
    def _generate_move_sequences(board: Board, remaining_dice: List[int],
                                 player: Player, current_sequence: List[Move],
                                 all_sequences: List[List[Move]]) -> None:
        """
        Recursively generate all possible move sequences.
        """
        if not remaining_dice:
            all_sequences.append(current_sequence)
            return
        
        found_move = False
        for i, die_value in enumerate(remaining_dice):
            possible_moves =  MoveValidator._get_moves_for_die(board,
                                                               die_value,
                                                               player)
            for move in possible_moves:
                new_board = board.copy()
                MoveValidator.execute_move(new_board, move, player)

                new_dice = remaining_dice[:i] + remaining_dice[i+1:]
                new_sequence = current_sequence + [move]
                MoveValidator._generate_move_sequences(new_board, new_dice,
                                                       player, new_sequence,
                                                       all_sequences)
                found_move = True
            
            if not found_move:
                all_sequences.append(current_sequence.copy())



    @staticmethod
    def _get_moves_for_die(board: Board, die_value: int,
                           player: Player) -> List[Move]:
        """
        Get all possible moves for a given die value.
        Args:
            board: the game board
            die_value: the die value
            player: the player making the move
        Returns:
            list of possible moves for the die value
        """
        moves = []

        # If token on bar, enter first
        if board.tokens_on_bar(player) > 0:
            entry_line = MoveValidator.get_entry_line(die_value, player)
            move = Move(None, entry_line, die_value)
            if MoveValidator.is_valid_move(board, move, player):
                moves.append(move)
            return moves
        
        # Check bear off
        if board.all_in_home_board(player):
            lines = range(0, 6) if player == Player.WHITE else range(18, 24)
            for from_line in lines:
                if board.is_line_occupied_by(from_line, player):
                    if MoveValidator.can_bear_off(board, from_line, die_value,
                                                    player):
                        move = Move(from_line, None, die_value, is_bearing=True)
                        moves.append(move)
        
        # Regular moves
        for from_line in range(24):
            if board.is_line_occupied_by(from_line, player):
                to_line = MoveValidator.get_destination_line(from_line,
                                                                 die_value,
                                                                 player)
                if 0 <= to_line <= 23:
                    move = Move(from_line, to_line, die_value)
                    if MoveValidator.is_valid_move(board, move, player):
                        moves.append(move)
        
        return moves
    
    @staticmethod
    def execute_move(board: Board, move: Move, player: Player) -> bool:
        """
        Execute a move on the board.
        Args:
            board: the game board
            move: the move to execute
            player: the player making the
        Returns:
            True if move was executed successfully, False otherwise
        """
        # starting from bar
        if move.from_line is None:
            if move.to_line is None:
                return False
            
            board.bar[player] -= 1
            if (board.is_token_alone(move.to_line)
                and board.get_line_owner(move.to_line) != player):
                board.hit_token(move.to_line)
            board.add_token(move.to_line, player)
            return True
        
        if move.is_bearing:
            board.remove_token(move.from_line, player)
            board.off[player] += 1
            return True
        
        if move.to_line is None:
            return False

        board.remove_token(move.from_line, player)
        if (board.is_token_alone(move.to_line)
            and board.get_line_owner(move.to_line) != player):
            board.hit_token(move.to_line)
        board.add_token(move.to_line, player)

        return True
                