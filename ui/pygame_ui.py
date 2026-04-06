import pygame
import sys
from typing import Optional
from game import BackgammonGame, Player

class PygameUI:
    """
    Pygame-based user interface for backgammon game.
    """

    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800

    COLOR_BACKGROUND = (255, 204, 153)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BOARD_LIGHT = (153, 204, 153)
    COLOR_BOARD_DARK = (102, 153, 102)

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
        self.screen.fill(self.COLOR_BACKGROUND)

        pygame.draw.rect(self.screen, self.COLOR_BOARD_LIGHT, (100, 100,
                                                               600, 600))
        
        font = pygame.font.Font(None, 36)
        text = font.render("Backgammon", True, self.COLOR_BLACK)
        text_rect = text.get_rect(center=(self.WINDOW_WIDTH // 2, 50))
        self.screen.blit(text, text_rect)

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

