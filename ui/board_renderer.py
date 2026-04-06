import pygame
from typing import Tuple


class BoardRenderer:
    def __init__(self, screen, board_x, board_y, board_width, board_height,
                 point_width, point_height, bar_width, colors):
        self.screen = screen
        self.board_x = board_x
        self.board_y = board_y
        self.board_width = board_width
        self.board_height = board_height
        self.point_width = point_width
        self.point_height = point_height
        self.bar_width = bar_width
        self.colors = colors
    
    def draw_board(self):
        """
        Draw the complete board.
        """
        self._draw_background()
        self._draw_points()
        self._draw_bar()
        self._draw_border()
    
    def _draw_background(self):
        """
        Draw board background.
        """
        pygame.draw.rect(self.screen, self.colors['board_background'],
                        (self.board_x, self.board_y, 
                         self.board_width, self.board_height))
    
    def _draw_border(self):
        """
        Draw board border.
        """
        pygame.draw.rect(self.screen, self.colors['black'],
                        (self.board_x, self.board_y, 
                         self.board_width, self.board_height), 3)
    
    def _draw_points(self):
        """
        Draw all 24 points.
        """
        # Top points
        for i in range(12):
            point_index = 13 + i
            x_offset = i * self.point_width

            if i >= 6:
                x_offset += self.bar_width
            
            color = (self.colors['point_light'] if i % 2 == 0 
                    else self.colors['point_dark'])
            
            self._draw_triangle_down(
                self.board_x + x_offset,
                self.board_y,
                self.point_width,
                self.point_height,
                color,
                point_index
            )
        
        # Bottom points
        for i in range(12):
            point_index = 12 - i
            x_offset = i * self.point_width

            if i >= 6:
                x_offset += self.bar_width
            
            color = (self.colors['point_dark'] if i % 2 == 0 
                    else self.colors['point_light'])
            
            self._draw_triangle_up(
                self.board_x + x_offset,
                self.board_y + self.board_height,
                self.point_width,
                self.point_height,
                color,
                point_index
            )
    
    def _draw_triangle_down(self, x, y, width, height, color, point_num):
        """
        Draw downward pointing triangle.
        """
        points = [
            (x, y),
            (x + width, y),
            (x + width // 2, y + height)
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.colors['black'], points, 1)
        
        font = pygame.font.Font(None, 24)
        text = font.render(str(point_num), True, self.colors['white'])
        text_rect = text.get_rect(center=(x + width // 2, y + 15))
        self.screen.blit(text, text_rect)
    
    def _draw_triangle_up(self, x, y, width, height, color, point_num):
        """
        Draw upward pointing triangle.
        """
        points = [
            (x, y),
            (x + width, y),
            (x + width // 2, y - height)
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.colors['black'], points, 1)
        
        font = pygame.font.Font(None, 24)
        text = font.render(str(point_num), True, self.colors['white'])
        text_rect = text.get_rect(center=(x + width // 2, y - 15))
        self.screen.blit(text, text_rect)
    
    def _draw_bar(self):
        """
        Draw the bar.
        """
        bar_x = self.board_x + (6 * self.point_width)
        bar_y = self.board_y
        
        pygame.draw.rect(self.screen, self.colors['board_margin'],
                        (bar_x, bar_y, self.bar_width, self.board_height))
        pygame.draw.rect(self.screen, self.colors['black'],
                        (bar_x, bar_y, self.bar_width, self.board_height), 2)
