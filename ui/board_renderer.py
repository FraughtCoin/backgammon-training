import pygame
from typing import Tuple, Optional


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
    
    def draw_board(self, selected_line: Optional[int]):
        """
        Draw the complete board.
        Args:
            selected_line: the line number to highlight or None
        """
        self._draw_background()
        self._draw_points()
        self._draw_bar()
        self._draw_border()
        self._draw_highlight(selected_line)
    
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
    
    def _draw_triangle_down(self, x: int, y: int, width: int, height: int,
                            color: Tuple[int, int, int], point_num: int):
        """
        Draw downward pointing triangle.
        Args:
            x: x-coordinate of top-left corner
            y: y-coordinate of top-left corner
            width: width of triangle base
            height: height of triangle
            color: RGB color tuple
            point_num: point number to display
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
    
    def _draw_triangle_up(self, x: int, y: int, width: int, height: int,
                            color: Tuple[int, int, int], point_num: int):
        """
        Draw upward pointing triangle.
        Args:
            x: x-coordinate of top-left corner
            y: y-coordinate of top-left corner
            width: width of triangle base
            height: height of triangle
            color: RGB color tuple
            point_num: point number to display
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
        
    def _get_line_position(self, line) -> Tuple[int, int, bool]:
        """
        Get the center position of a line.
        Args:
            line: the line number (0-23)
        Returns:
            tuple of (x, y, is_top) where is_top indicates if line is on top
            half
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
        
    def _draw_highlight(self, selected_line: Optional[int]):
        """
        Draw highlight on selected point.
        Args:
            selected_line: the line number to highlight (0-23), or None
        """
        if selected_line is None:
            return
        
        line_x, line_y, is_top = self._get_line_position(selected_line)

        highlight_surface = pygame.Surface((self.point_width,
                                            self.point_height),
                                            pygame.SRCALPHA)
        highlight_surface.fill(self.colors['highlight'])

        if is_top:
            visual_index = selected_line - 12
            x_offset = visual_index * self.point_width
            if visual_index >= 6:
                x_offset += self.bar_width

            x = self.board_x + x_offset
            y = self.board_y
        else:
            visual_index = 11 - selected_line
            x_offset = visual_index * self.point_width
            if visual_index >= 6:
                x_offset += self.bar_width

            x = self.board_x + x_offset
            y = self.board_y + self.board_height - self.point_height

        self.screen.blit(highlight_surface, (x, y))
