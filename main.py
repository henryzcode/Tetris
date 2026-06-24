import pygame
import os
import entities
import random

x, y = 0, 0
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

pygame.init()
pygame.mixer.init()

pygame.key.set_repeat(150, 50)

screen_dimension = pygame.display.get_desktop_sizes()[0]
icon = pygame.image.load("assets/logo.ico")
win = pygame.display.set_mode(screen_dimension, pygame.FULLSCREEN | pygame.DOUBLEBUF)
pygame.display.set_caption("Tetris", "Tetris")
pygame.display.set_icon(icon)
font = pygame.font.Font("assets/anybody.ttf", 50)

cursor_img = pygame.image.load("assets/cursor.png").convert_alpha()

cursor = pygame.cursors.Cursor((0, 0), cursor_img)
pygame.mouse.set_cursor(cursor)

volume_level = 0.5

MUSICS = [
    "assets/music/hyperspace.mp3",
    "assets/music/kora.mp3",
    "assets/music/liquid glass.mp3",
    "assets/music/phrase break.mp3",
    "assets/music/shipwrecked.mp3",
    "assets/music/thalassophobia.mp3",
]
MUSIC_END = pygame.USEREVENT + 2
pygame.mixer.music.set_endevent(MUSIC_END)

current_track_index = 0
random.shuffle(MUSICS)

def play_music():
    global current_track_index, volume_level
    pygame.mixer.music.load(MUSICS[current_track_index])
    pygame.mixer.music.play(fade_ms=15000)
    pygame.mixer.music.set_volume(volume_level) 
    current_track_index = (current_track_index + 1) % len(MUSICS)



landed = [pygame.mixer.Sound("assets/landed.wav"),
          pygame.mixer.Sound("assets/landed1.wav")]
clear = pygame.mixer.Sound("assets/level_up.wav")

grid_size = 30
running = True

min_padding = 20
available_height = screen_dimension[1] - (2 * min_padding)
rows_that_fit = available_height // grid_size
play_area_height = rows_that_fit * grid_size
ui_offset = (screen_dimension[1] - play_area_height) / 2

play_area_width = 600
play_area_x = (screen_dimension[0] / 2) - (play_area_width / 2)
play_area_y = ui_offset

play_area_r = pygame.Rect(play_area_x, play_area_y, play_area_width, play_area_height)

play_area_columns = play_area_width // grid_size
play_area_rows = rows_that_fit

shapes = list(entities.TETROMINOES.keys())
next_shape = random.choice(shapes)

def spawn_piece():
    global next_shape, next_color
    x_pos = (play_area_columns // 2) - 2 
    shape_to_spawn = next_shape
    shapes = list(entities.TETROMINOES.keys())
    next_shape = random.choice(shapes)
    next_color = random.choice(list(entities.TILE_PATHS.keys()))
    
    return entities.Tetromino(x_pos, 0, shape_to_spawn)

def volume(change):
    global volume_level
    volume_level = max(0.0, min(1.0, volume_level + change))
    pygame.mixer.music.set_volume(volume_level)
    for sound in landed:
        sound.set_volume(volume_level)
    clear.set_volume(volume_level)

loaded_tiles = entities.load_and_scale_tiles(grid_size, grid_size)

locked_blocks = {} 
current_piece = spawn_piece()

clock = pygame.time.Clock()

def valid_position(piece, locked):
    matrix = piece.get_matrix()
    
    for row_idx, row in enumerate(matrix):
        for col_idx, cell in enumerate(row):
            if cell == 1:
                grid_x = piece.x + col_idx
                grid_y = piece.y + row_idx

                if grid_x < 0 or grid_x >= play_area_columns or grid_y >= play_area_rows:
                    return False
                
                if (grid_x, grid_y) in locked:
                    return False
    return True

def clear_lines(locked):
    lines_cleared_this_turn = 0
    row = play_area_rows - 1
    while row >= 0:
        row_is_full = True
        for col in range(play_area_columns):
            if (col, row) not in locked:
                row_is_full = False
                break
        
        if row_is_full:
            lines_cleared_this_turn += 1
            for col in range(play_area_columns):
                del locked[(col, row)]
            
            shifted_locked = {}
            for (x, y), color in locked.items():
                if y < row:
                    shifted_locked[(x, y + 1)] = color
                else:
                    shifted_locked[(x, y)] = color
            
            locked = shifted_locked
        else:
            row -= 1 
    clear.play()

    return locked, lines_cleared_this_turn


def cal_bottom(piece, locked):
    original_y = piece.y 

    while valid_position(piece, locked):
        piece.y += 1
        
    bottom_y = piece.y - 1 
    
    piece.y = original_y 
    
    return bottom_y


fall_time = 120

FALL_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(FALL_EVENT, fall_time) 

total_lines_cleared = 0
bottom = 0

space_pressed = False
rotation_pressed = False

play_music()

while running:
    win.fill("#000074")
    pygame.draw.rect(win, "#000000", play_area_r)


    for current_y in range(int(play_area_y), int(play_area_y + play_area_height) + 1, grid_size):
        start_pos = (play_area_x, current_y)
        end_pos = (play_area_x + play_area_width, current_y)
        pygame.draw.line(win, "#1f1f1f", start_pos, end_pos, 2)
        
    for current_x in range(int(play_area_x), int(play_area_x + play_area_width) + 1, grid_size):
        start_pos = (current_x, play_area_y)
        end_pos = (current_x, play_area_y + play_area_height)
        pygame.draw.line(win, "#1f1f1f", start_pos, end_pos, 2)
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                space_pressed = False
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                rotation_pressed = False
        
        if event.type == MUSIC_END:
            play_music()
            
        if event.type == FALL_EVENT:
            current_piece.y += 1
            if not valid_position(current_piece, locked_blocks):
                current_piece.y -= 1

                matrix = current_piece.get_matrix()
                for r_idx, row in enumerate(matrix):
                    for c_idx, cell in enumerate(row):
                        if cell == 1:
                            locked_blocks[(current_piece.x + c_idx, current_piece.y + r_idx)] = current_piece.color
                
                locked_blocks, cleared = clear_lines(locked_blocks)
                total_lines_cleared += cleared

                current_piece = spawn_piece()
                random.choice(landed).play()

                if not valid_position(current_piece, locked_blocks):
                    locked_blocks = {} 
                    total_lines_cleared = 0 
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if (event.key == pygame.K_UP or event.key == pygame.K_w) and not rotation_pressed:
                rotation_pressed = True
                current_piece.rotate(1)
                if not valid_position(current_piece, locked_blocks):
                    current_piece.rotate(-1)
        
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                current_piece.x -= 1
                if not valid_position(current_piece, locked_blocks):
                    current_piece.x += 1
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                current_piece.x += 1
                if not valid_position(current_piece, locked_blocks):
                    current_piece.x -= 1

            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                current_piece.y += 1
                if not valid_position(current_piece, locked_blocks):
                    current_piece.y -= 1
                    
            if event.key == pygame.K_SPACE and not space_pressed:
                space_pressed = True
                while valid_position(current_piece, locked_blocks):
                    current_piece.y += 1
                current_piece.y -= 1
                
                matrix = current_piece.get_matrix()
                for r_idx, row in enumerate(matrix):
                    for c_idx, cell in enumerate(row):
                        if cell == 1:
                            locked_blocks[(current_piece.x + c_idx, current_piece.y + r_idx)] = current_piece.color
                
                locked_blocks, cleared = clear_lines(locked_blocks)
                total_lines_cleared += cleared
                current_piece = spawn_piece()
                
                if not valid_position(current_piece, locked_blocks):
                    locked_blocks = {}
                    total_lines_cleared = 0
                random.choice(landed).play()
            
            if event.key == pygame.K_q:
                volume(-0.03)
            if event.key == pygame.K_e:
                volume(0.03)
    
    keys = pygame.key.get_pressed()

    for (lock_x, lock_y), color in locked_blocks.items():
        tile_image = loaded_tiles[color]
        screen_x = play_area_x + (lock_x * grid_size)
        screen_y = play_area_y + (lock_y * grid_size)
        win.blit(tile_image, (screen_x, screen_y))

    bottom = cal_bottom(current_piece, locked_blocks)
    side_panel_x = play_area_x + play_area_width + 50
    side_panel_y = play_area_y + 100
    entities.render_txt(font, win, "Next:", "#ffffff", side_panel_x, side_panel_y - 60)

    pygame.draw.rect(win, "#101010", [side_panel_x - 10, side_panel_y - 10, 140, 140])

    next_block = entities.Tetromino(0, 0, next_shape, 0)
    next_block.draw(win, loaded_tiles, grid_size, side_panel_x + 5, side_panel_y + 10, next_color)

    current_piece.draw(win, loaded_tiles, grid_size, play_area_x, play_area_y)
    current_piece.draw_ghost(win, loaded_tiles, grid_size, play_area_x, play_area_y, bottom)

    entities.render_txt(font, win, "Tetris 2.0", "#ffffff", 10, 10)
    entities.render_txt(font, win, f"Landed: {len(locked_blocks) // 4}", "#ffffff", 10, 70) 
    entities.render_txt(font, win, f"Lines: {total_lines_cleared}", "#ffffff", 10, 130)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
