import pygame
import random

TILE_PATHS = {
    "blue": "assets/tiles/blue.png",
    "dark_b": "assets/tiles/dark_b.png",
    "green": "assets/tiles/green.png",    
    "orange": "assets/tiles/orange.png",
    "purple": "assets/tiles/purple.png",
    "red": "assets/tiles/red.png",
    "yellow": "assets/tiles/yellow.png",
}

TETROMINOES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]]
}

def load_and_scale_tiles(width, height):
    scaled_tiles = {}
    for color_name, path in TILE_PATHS.items():
        raw_surface = pygame.image.load(path).convert_alpha()
        scaled_surface = pygame.transform.smoothscale(raw_surface, (width, height))
        scaled_tiles[color_name] = scaled_surface
    return scaled_tiles

class Tetromino:
    def __init__(self, x, y, shape_name, rotation=0):
        self.x = x
        self.y = y
        self.shape_name = shape_name
        self.rotation = rotation
        self.color = random.choice(list(TILE_PATHS.keys()))

    def rotate(self, steps=1):
        self.rotation += steps
        

    def get_matrix(self):
        shape = TETROMINOES[self.shape_name]
        steps = self.rotation % 4
        result = shape
        for _ in range(steps):
            result = [list(row) for row in zip(*result[::-1])]
        return result

    def draw(self, surface, tiles_dict, tile_size, offset_x, offset_y):
        matrix = self.get_matrix()
        tile_image = tiles_dict[self.color]

        for row_idx, row in enumerate(matrix):
            for col_idx, cell in enumerate(row):
                if cell == 1:
                    screen_x = offset_x + ((self.x + col_idx) * tile_size)
                    screen_y = offset_y + ((self.y + row_idx) * tile_size)
                    surface.blit(tile_image, (screen_x, screen_y))

    def draw_ghost(self, surface, tiles_dict, tile_size, offset_x, offset_y, ghost_y):
        matrix = self.get_matrix()

        ghost_image = tiles_dict[self.color].copy() 
        ghost_image.set_alpha(70)

        for row_idx, row in enumerate(matrix):
            for col_idx, cell in enumerate(row):
                if cell == 1:
                    screen_x = offset_x + ((self.x + col_idx) * tile_size)
                    screen_y = offset_y + ((ghost_y + row_idx) * tile_size) 
                    surface.blit(ghost_image, (screen_x, screen_y))
            

def render_txt(font: pygame.font.Font, surf: pygame.surface.Surface, txt, color, x, y):
    texture = font.render(txt, True, color)
    surf.blit(texture, (x, y))
