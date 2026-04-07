import pygame
from typing import Tuple, Optional

class Button:
    """
    """

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 color: Tuple[int, int, int],
                 text_color: Tuple[int, int, int],
                 hover_color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        Constructor
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover_color = hover_color if hover_color else color
        self.is_hovered = False
        self.enabled = True

    def draw(self, screen: pygame.Surface):
        """
        Draw the button
        """
        if not self.enabled:
            color = (150, 150, 150)
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

        font = pygame.font.Font(None, 30)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse event
        """
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos) and self.enabled
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered and self.enabled:
                return True
        return False
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or dissable the button.
        """
        self.enabled = enabled