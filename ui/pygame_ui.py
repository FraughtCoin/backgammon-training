import pygame
import sys
from typing import Tuple
from game import BackgammonGame
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
    LINE_HEIGHT = 250
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

    def update(self):
        pass

    def draw(self):
        self.screen.fill(self.COLORS['background'])
        self.board_renderer.draw_board()
        self.token_renderer.draw_all_tokens(self.game.get_board())
        pygame.display.flip()

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

