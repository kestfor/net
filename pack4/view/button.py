import pygame


class GameButton:
    def __init__(self, text, x, y, width, height, color, func, *args):
        smallfont = pygame.font.SysFont('Times new roman', height // 2)
        self.text = smallfont.render(text, True, (0, 0, 0))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.func = func
        self.args = args

    def run_func(self):
        self.func(*self.args)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color,
                         pygame.Rect(self.x, self.y, self.width, self.height))
        screen.blit(self.text, (self.x, self.y))

    def collide(self, x, y):
        if self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height:
            return True
        return False


