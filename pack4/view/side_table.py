import pygame


class SideTable:

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen, score):
        curr_x = self.x
        curr_y = self.y
        line_height = 40
        smallfont = pygame.font.SysFont('Times new roman', line_height // 2)
        color = (0, 255, 255)
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

        for key in score:
            text = smallfont.render(f'{key}: {score[key]}', True, (0, 0, 0))
            pygame.draw.rect(screen, color,
                             pygame.Rect(curr_x, curr_y, self.width, line_height))
            screen.blit(text, (curr_x, curr_y))
            curr_y += line_height + 10
