import random
from typing import List, Tuple

class Dice:

    @staticmethod
    def roll() -> Tuple[int, int]:
        """
        Rolls two dice
        Returns:
            tuple of two random integers between 1 and 6
        """
        return (random.randint(1, 6), random.randint(1, 6))
    
    @staticmethod
    def get_moves(roll: Tuple[int, int]) -> List[int]:
        """
        Get available moves from a dice roll.
        If doubles, returns 4 moves of the same value.
        Args:
            roll: tuple of two dice values
        Returns:
            list of available moves
        """
        die1, die2 = roll
        if die1 == die2:
            return [die1, die1, die1, die1]
        else:
            return [die1, die2]