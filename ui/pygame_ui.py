import pygame
import sys
from typing import Tuple, Optional, List
from game import BackgammonGame, Move, Player
from .board_renderer import BoardRenderer
from .token_renderer import TokenRenderer
from .button import Button

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
        'light_gray':  (140, 140, 140),
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

        button_spacing = 20
        button_width = 150
        button_height = 40
        button_y = self.board_y - button_height

        self.roll_button = Button(
            self.board_x, button_y,
            button_width, button_height,
            "Roll Dice", self.COLORS['dark_gray'],
            self.COLORS['white'], self.COLORS['light_gray'])
        
        self.undo_button = Button(
            self.board_x + button_width + button_spacing, button_y,
            button_width, button_height,
            "Undo", self.COLORS['dark_gray'],
            self.COLORS['white'], self.COLORS['light_gray'])
        
        self.end_turn_button = Button(
            self.board_x + 2 * (button_width + button_spacing), button_y,
            button_width, button_height,
            "End Turn", self.COLORS['dark_gray'],
            self.COLORS['white'], self.COLORS['light_gray'])
        
        self.new_game_button = Button(
            self.board_x + 3 * (button_width + button_spacing), button_y,
            button_width, button_height,
            "New Game", self.COLORS['dark_gray'],
            self.COLORS['white'], self.COLORS['light_gray'])


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
                    if self.roll_button.handle_event(event):
                        self.handle_roll_dice()
                    if self.undo_button.handle_event(event):
                        self.handle_undo()
                    if self.end_turn_button.handle_event(event):
                        self.handle_end_turn()
                    if self.new_game_button.handle_event(event):
                        self.handle_new_game()
                    else:
                        self.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.roll_button.handle_event(event)
                self.undo_button.handle_event(event)
                self.end_turn_button.handle_event(event)
                self.new_game_button.handle_event(event)

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
                    if clicked_line == -1 and move.is_bearing:
                        if self.game.make_move(move):
                            self.selected_line = None
                            self.legal_destinations = []
                            return

                    if move.to_line == clicked_line:
                        if self.game.make_move(move):
                            self.selected_line = None
                            self.legal_destinations = []
                            return
                
                if clicked_line != -1:
                    self.selected_line = clicked_line
                    self.legal_destinations = self.get_legal_destinations(self.selected_line)
            else:
                if clicked_line == -1:
                    return
                
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
            return -2
        
        bear_off_start = 12 * self.LINE_WIDTH + self.BAR_WIDTH
        bear_off_end = bear_off_start + self.LINE_WIDTH
        if bear_off_start <= rel_x <= bear_off_end:
            return -1

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

        if from_line == -2:
            moves_from_bar = [move for move in all_legal_moves if move.from_line is None]
            return moves_from_bar

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
        if self.game.get_available_dice() and not self.game.get_legal_single_moves():
            self.game.force_end_turn()

        can_roll = ((not self.game.get_current_dice() or not self.game.get_available_dice())
                    and not self.game.can_undo())
        self.roll_button.set_enabled(can_roll and not self.game.is_game_over())

        self.undo_button.set_enabled(self.game.can_undo() and not self.game.is_game_over())

        can_end_turn = (self.game.get_current_dice() is not None and 
                        len(self.game.get_available_dice()) == 0)
        self.end_turn_button.set_enabled(can_end_turn and not self.game.is_game_over())
        
        self.new_game_button.set_enabled(True)

    def draw(self):
        self.screen.fill(self.COLORS['background'])
        self.board_renderer.draw_board(self.selected_line, self.legal_destinations)
        self.token_renderer.draw_all_tokens(self.game.get_board())
        self.draw_game_info()

        self.roll_button.draw(self.screen)
        self.undo_button.draw(self.screen)
        self.end_turn_button.draw(self.screen)
        self.new_game_button.draw(self.screen)

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

    def handle_roll_dice(self):
        """
        """
        if not self.game.get_current_dice() or not self.game.get_available_dice():
            self.game.roll_dice()

    def handle_undo(self):
        """
        """
        if self.game.undo_last_move():
            self.selected_line = None
            self.legal_destinations = []

    def handle_end_turn(self):
        """
        """
        if self.game.end_turn():
            self.selected_line = None
            self.legal_destinations = []

    def handle_new_game(self):
        self.game.reset()
        self.game.start_game()
        self.selected_line = None
        self.legal_destinations = []

def main():
    ui = PygameUI()
    ui.run()

if __name__ == "__main__":
    main()

