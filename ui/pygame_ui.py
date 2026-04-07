import pygame
import sys
from typing import Tuple, Optional, List
from game import BackgammonGame, Move, Player
from .board_renderer import BoardRenderer
from .token_renderer import TokenRenderer

class PygameUI:
    """
    Pygame-based user interface for backgammon game.
    """

    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800

    BOARD_MARGIN = 50
    BOARD_WIDTH = 1100
    BOARD_HEIGHT = 700

    LINE_WIDTH = 80
    LINE_HEIGHT = 320
    BAR_WIDTH = 60

    TOKEN_RADIUS = 30
    TOKEN_SPACING = 35
    MAX_TOKENS_DISPLAY = 8
    TOKEN_DELTA = 60

    COLORS = {
        'background': (255, 255, 255),
        'white': (255, 255, 255),
        'dark_gray': (80, 80, 80),
        'black': (0, 0, 0),
        'board_margin': (255, 153, 102),
        'board_background': (255, 204, 153),
        'point_light': (153, 204, 153),
        'point_dark': (102, 153, 102),
        'highlight': (255, 255, 0, 128),
        'legal_destination': (0, 255, 0, 80),
        'text': (0, 0, 0),
    }

    def __init__(self) -> None:
        """
        Initialize pygame UI
        """
        pygame.init()

        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH,
                                               self.WINDOW_HEIGHT))
        pygame.display.set_caption("Backgammon")

        self.clock = pygame.time.Clock()
        self.game = BackgammonGame()
        self.running = True

        self.board_x = self.BOARD_MARGIN
        self.board_y = self.BOARD_MARGIN

        self.selected_line = None
        self.legal_destinations = []

        self.board_renderer = BoardRenderer(
            self.screen, self.board_x, self.board_y,
            self.BOARD_WIDTH, self.BOARD_HEIGHT,
            self.LINE_WIDTH, self.LINE_HEIGHT, self.BAR_WIDTH,
            self.COLORS
        )
        
        self.token_renderer = TokenRenderer(
            self.screen, self.board_x, self.board_y,
            self.BOARD_WIDTH, self.BOARD_HEIGHT,
            self.LINE_WIDTH, self.BAR_WIDTH,
            self.TOKEN_RADIUS, self.TOKEN_SPACING,
            self.MAX_TOKENS_DISPLAY, self.TOKEN_DELTA,
            self.COLORS
        )

    def handle_events(self):
        """
        Handle pygame events
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_click(event.pos)

    def handle_click(self, pos: Tuple[int, int]):
        """
        Handle mouse click events on the board
        Args:
            pos - tuple of (x, y) coordinates of the click
        """
        clicked_line = self.get_line_at_position(pos)
        if clicked_line is not None:
            if self.selected_line is not None and self.selected_line != clicked_line:
                legal_moves = self.get_legal_moves_from_line(self.selected_line)
                for move in legal_moves:
                    if move.to_line == clicked_line:
                        if self.game.make_move(move):
                            self.selected_line = None
                            self.legal_destinations = []

                            if not self.game.get_available_dice():
                                self.game.end_turn()

                            return
                
                self.selected_line = clicked_line
                self.legal_destinations = self.get_legal_destinations(self.selected_line)
            else:
                if self.selected_line == clicked_line:
                    self.selected_line = None
                    self.legal_destinations = []
                else:
                    self.selected_line = clicked_line
                    self.legal_destinations = self.get_legal_destinations(self.selected_line)
        else:
            self.selected_line = None

    def get_line_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """
        Determine which line on the board was clicked
        Args:
            pos - tuple of (x, y) coordinates of the click
        Returns:
            line number (0-23) or None if click is outside board
        """
        x, y = pos
        if not (self.board_x <= x <= self.board_x + self.BOARD_WIDTH 
                 and self.board_y <= y <= self.board_y + self.BOARD_HEIGHT):
            return None
        
        rel_x = x - self.board_x
        rel_y = y - self.board_y
        is_top = rel_y < self.BOARD_HEIGHT / 2

        bar_start = 6 * self.LINE_WIDTH
        bar_end = bar_start + self.BAR_WIDTH
        if bar_start <= rel_x <= bar_end:
            return None

        if rel_x > bar_start:
            rel_x -= self.BAR_WIDTH

        column = int(rel_x / self.LINE_WIDTH)
        if column < 0 or column >= 12:
            return None

        if is_top:
            return 12 + column
        else:
            return 11 - column
        
    def get_legal_moves_from_line(self, from_line: int) -> List[Move]:
        """
        Get all legal moves starting from a specific line.
        Args:
            from_line: starting line number (0-23)
        Returns:
            list of legal destination line numbers
        """
        all_legal_moves = self.game.get_legal_single_moves()
        moves_from_point = [move for move in all_legal_moves
                            if move.from_line == from_line]
        return moves_from_point
    
    def get_legal_destinations(self, from_line: int) -> List[int]:
        """
        Get all legal destination lines from a selected line.
        Args:
            from_line: starting line number (0-23)
        Returns:
            list of legal destination line numbers
        """
        moves = self.get_legal_moves_from_line(from_line)
        destinations = []

        for move in moves:
            if move.to_line is not None:
                destinations.append(move.to_line)
            elif move.is_bearing:
                destinations.append(-1)

        return destinations


    def update(self):
        pass

    def draw(self):
        self.screen.fill(self.COLORS['background'])
        self.board_renderer.draw_board(self.selected_line, self.legal_destinations)
        self.token_renderer.draw_all_tokens(self.game.get_board())
        self.draw_game_info()
        pygame.display.flip()

    def draw_game_info(self):
        """
        """
        info_y = self.board_y + self.BOARD_HEIGHT + 20
        font = pygame.font.Font(None, 32)

        current_player = self.game.get_current_player()
        if current_player:
            player_name = "White" if current_player == Player.WHITE else "Black"
            text = font.render(f"Current Player: {player_name}", True, self.COLORS['text'])
            self.screen.blit(text, (self.board_x, info_y))
        
        dice = self.game.get_current_dice()
        if dice:
            dice_text = f"Dice: [{dice[0]}] [{dice[1]}]"
            text = font.render(dice_text, True, self.COLORS['text'])
            self.screen.blit(text, (self.board_x + 300, info_y))

        available = self.game.get_available_dice()
        if available:
            available_text = f"Available: {available}"
            text = font.render(available_text, True, self.COLORS['text'])
            self.screen.blit(text, (self.board_x + 600, info_y))

    def run(self):
        self.game.start_game()

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

def main():
    ui = PygameUI()
    ui.run()

if __name__ == "__main__":
    main()

