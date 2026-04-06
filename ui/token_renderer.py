import pygame
from game import Player
from typing import Tuple


class TokenRenderer:
    def __init__(self, screen, board_x, board_y, board_width, board_height,
                 point_width, bar_width, token_radius, token_spacing, 
                 max_tokens_display, token_delta, colors):
        self.screen = screen
        self.board_x = board_x
        self.board_y = board_y
        self.board_width = board_width
        self.board_height = board_height
        self.point_width = point_width
        self.bar_width = bar_width
        self.token_radius = token_radius
        self.token_spacing = token_spacing
        self.max_tokens_display = max_tokens_display
        self.token_delta = token_delta
        self.colors = colors
    
    def draw_all_tokens(self, board):
        """
        Draw all tokens on the board.
        """
        self._draw_tokens_on_points(board)
        self._draw_bar_tokens(board)
        self._draw_borne_tokens(board)
    
    def _draw_tokens_on_points(self, board):
        """
        Draw tokens on all points.
        """
        for line in range(24):
            token_count = abs(board.get_tokens_count(line))
            if token_count > 0:
                owner = board.get_line_owner(line)
                if owner:
                    self._draw_tokens_on_line(line, owner, token_count)
    
    def _draw_tokens_on_line(self, line, player, count):
        """
        Draw tokens on a specific line.
        """
        line_x, line_y, is_top = self._get_line_position(line)
        tokens_to_draw = min(count, self.max_tokens_display)
        
        for i in range(tokens_to_draw):
            if is_top:
                y = line_y + self.token_delta + (i * self.token_spacing)
            else:
                y = line_y - self.token_delta - (i * self.token_spacing)
            
            self._draw_token(line_x, y, player)
        
        if count > self.max_tokens_display:
            if is_top:
                y = line_y + self.token_delta + ((self.max_tokens_display - 1) * 
                                                 self.token_spacing)
            else:
                y = line_y - self.token_delta - ((self.max_tokens_display - 1) * 
                                                 self.token_spacing)
            
            font = pygame.font.Font(None, 28)
            color = (self.colors['white'] if player == Player.BLACK 
                    else self.colors['black'])
            text = font.render(f"+{count - self.max_tokens_display}", True, color)
            text_rect = text.get_rect(center=(line_x, y))
            self.screen.blit(text, text_rect)
    
    def _draw_bar_tokens(self, board):
        """
        Draw tokens on the bar.
        """
        white_bar = board.tokens_on_bar(Player.WHITE)
        black_bar = board.tokens_on_bar(Player.BLACK)
        
        bar_x = self.board_x + (6 * self.point_width) + self.bar_width // 2
        
        if white_bar > 0:
            for i in range(min(white_bar, 3)):
                y = (self.board_y + self.board_height - 100 - 
                     (i * self.token_spacing))
                self._draw_token(bar_x, y, Player.WHITE)
            
            if white_bar > 3:
                y = self.board_y + self.board_height - 100 - (2 * self.token_spacing)
                font = pygame.font.Font(None, 28)
                text = font.render(f"+{white_bar - 3}", True, self.colors['black'])
                text_rect = text.get_rect(center=(bar_x, y))
                self.screen.blit(text, text_rect)
        
        if black_bar > 0:
            for i in range(min(black_bar, 3)):
                y = self.board_y + 100 + (i * self.token_spacing)
                self._draw_token(bar_x, y, Player.BLACK)
            
            if black_bar > 3:
                y = self.board_y + 100 + (2 * self.token_spacing)
                font = pygame.font.Font(None, 28)
                text = font.render(f"+{black_bar - 3}", True, self.colors['white'])
                text_rect = text.get_rect(center=(bar_x, y))
                self.screen.blit(text, text_rect)
    
    def _draw_borne_tokens(self, board):
        """
        Draw borne-off tokens.
        """
        white_off = board.tokens_off_board(Player.WHITE)
        black_off = board.tokens_off_board(Player.BLACK)
        
        offset_x = self.board_x + self.board_width - self.point_width // 2
        
        if white_off > 0:
            tokens_to_draw = min(white_off, self.max_tokens_display)
            for i in range(tokens_to_draw):
                y = (self.board_y + self.board_height - self.token_delta - 
                     (i * self.token_spacing))
                self._draw_token(offset_x, y, Player.WHITE)
            
            if white_off > self.max_tokens_display:
                y = (self.board_y + self.board_height - self.token_delta - 
                     ((self.max_tokens_display - 1) * self.token_spacing))
                font = pygame.font.Font(None, 28)
                text = font.render(f"+{white_off - self.max_tokens_display}", 
                                 True, self.colors['black'])
                text_rect = text.get_rect(center=(offset_x, y))
                self.screen.blit(text, text_rect)
        
        if black_off > 0:
            tokens_to_draw = min(black_off, self.max_tokens_display)
            for i in range(tokens_to_draw):
                y = self.board_y + self.token_delta + (i * self.token_spacing)
                self._draw_token(offset_x, y, Player.BLACK)
            
            if black_off > self.max_tokens_display:
                y = (self.board_y + self.token_delta + 
                     ((self.max_tokens_display - 1) * self.token_spacing))
                font = pygame.font.Font(None, 28)
                text = font.render(f"+{black_off - self.max_tokens_display}", 
                                 True, self.colors['white'])
                text_rect = text.get_rect(center=(offset_x, y))
                self.screen.blit(text, text_rect)
    
    def _draw_token(self, x, y, player):
        """
        Draw a single token.
        """
        color = (self.colors['white'] if player == Player.WHITE 
                else self.colors['dark_gray'])
        
        pygame.draw.circle(self.screen, color, (x, y), self.token_radius)
        pygame.draw.circle(self.screen, self.colors['black'], (x, y), 
                          self.token_radius, 2)
    
    def _get_line_position(self, line) -> Tuple[int, int, bool]:
        """
        Get the center position of a line.
        """
        if line > 11:
            is_top = True
            visual_index = line - 12
            x_offset = visual_index * self.point_width
            
            if visual_index >= 6:
                x_offset += self.bar_width
            
            x = self.board_x + x_offset + self.point_width // 2
            y = self.board_y
        else:
            is_top = False
            visual_index = 11 - line
            x_offset = visual_index * self.point_width
            
            if visual_index >= 6:
                x_offset += self.bar_width
            
            x = self.board_x + x_offset + self.point_width // 2
            y = self.board_y + self.board_height
        
        return x, y, is_top
