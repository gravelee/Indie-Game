import pygame

class SpriteSheet:
    def __init__(self, path, frame_w, frame_h):
        self.sheet   = pygame.image.load(path).convert_alpha()
        self.frame_w = frame_w
        self.frame_h = frame_h

    def get_all_frames(self):
        cols = self.sheet.get_width() // self.frame_w
        return [
            self.sheet.subsurface(
                pygame.Rect(col * self.frame_w, 0, self.frame_w, self.frame_h)
            )
            for col in range(cols)
        ]
