import pygame
import sys
from typing import Tuple
from game import BackgammonGame, Player

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

    COLOR_BACKGROUND = (255, 255, 255)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BOARD_MARGIN = (255, 153, 102)
    COLOR_BOARD_BACKGROUND = (255, 204, 153)
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

        self.board_x = self.BOARD_MARGIN
        self.board_y = self.BOARD_MARGIN

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
        self.draw_board()
        pygame.display.flip()

    def draw_board(self):
        """
        Draw the board.
        """
        pygame.draw.rect(self.screen, self.COLOR_BOARD_BACKGROUND,
                         (self.board_x, self.board_y,
                          self.BOARD_WIDTH, self.BOARD_HEIGHT))
        
        
        self.draw_lines()
        self.draw_bar()
        
        pygame.draw.rect(self.screen, self.COLOR_BLACK,
                        (self.board_x, self.board_y, self.BOARD_WIDTH, self.BOARD_HEIGHT), 3)

    def draw_lines(self):
        """
        Draw all 24 points on the board.
        """
        # Top lines (13-24)
        for i in range(12):
            point_index = 13 + i
            x_offset = i * self.LINE_WIDTH
            
            # Skip the bar space
            if i >= 6:
                x_offset += self.BAR_WIDTH
            
            color = (self.COLOR_BOARD_LIGHT
                     if i % 2 == 0
                     else self.COLOR_BOARD_DARK)
            
            self.draw_triangle_down(
                self.board_x + x_offset,
                self.board_y,
                self.LINE_WIDTH,
                self.LINE_HEIGHT,
                color,
                point_index
            )
        
        # Bottom lines (12-1)
        for i in range(12):
            point_index = 12 - i
            x_offset = i * self.LINE_WIDTH
            
            # Skip the bar space
            if i >= 6:
                x_offset += self.BAR_WIDTH
            
            color = (self.COLOR_BOARD_DARK
                     if i % 2 == 0
                     else self.COLOR_BOARD_LIGHT)
            
            self.draw_triangle_up(
                self.board_x + x_offset,
                self.board_y + self.BOARD_HEIGHT,
                self.LINE_WIDTH,
                self.LINE_HEIGHT,
                color,
                point_index
            )
    
    def draw_triangle_down(self, x: int, y: int, width: int, height: int, 
                          color: Tuple[int, int, int], line_num: int):
        """
        Draw a triangle pointing down.
        Args:
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: width of the triangle base
            height: height of the triangle
            color: RGB color tuple
            line_num: line number
        """
        points = [
            (x, y),
            (x + width, y),
            (x + width // 2, y + height)
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.COLOR_BLACK, points, 1)
        
        font = pygame.font.Font(None, 24)
        text = font.render(str(line_num), True, self.COLOR_WHITE)
        text_rect = text.get_rect(center=(x + width // 2, y + 15))
        self.screen.blit(text, text_rect)
    
    def draw_triangle_up(self, x: int, y: int, width: int, height: int,
                        color: Tuple[int, int, int], line_num: int):
        """
        Draw a triangle pointing up.
        Args:
            x: X coordinate of the bottom-left corner
            y: Y coordinate of the bottom-left corner
            width: width of the triangle base
            height: height of the triangle
            color: RGB color tuple
            line_num: line number
        """
        points = [
            (x, y),
            (x + width, y),
            (x + width // 2, y - height)
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.COLOR_BLACK, points, 1)
        
        font = pygame.font.Font(None, 24)
        text = font.render(str(line_num ), True, self.COLOR_WHITE)
        text_rect = text.get_rect(center=(x + width // 2, y - 15))
        self.screen.blit(text, text_rect)
    
    def draw_bar(self):
        """
        Draw the bar in the middle of the board.
        """
        bar_x = self.board_x + (6 * self.LINE_WIDTH)
        bar_y = self.board_y
        
        pygame.draw.rect(self.screen, self.COLOR_BOARD_MARGIN,
                        (bar_x, bar_y, self.BAR_WIDTH, self.BOARD_HEIGHT))
        pygame.draw.rect(self.screen, self.COLOR_BLACK,
                        (bar_x, bar_y, self.BAR_WIDTH, self.BOARD_HEIGHT), 2)

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

