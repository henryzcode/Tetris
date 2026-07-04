import pygame
import os
import entities
import random
import json
import time

x, y = 0, 0
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

pygame.init()
pygame.mixer.init()
pygame.joystick.init()

joystick = None
is_joy = False
joy_button = 0
try:
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        is_joy = True
        joy_button = joystick.get_numbuttons()
except Exception:
    is_joy = False

pygame.key.set_repeat(150, 50)

screen_dimension = pygame.display.get_desktop_sizes()[0]
icon = pygame.image.load("assets/logo.ico")
win = pygame.display.set_mode(screen_dimension, pygame.DOUBLEBUF)
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

log_time = time.asctime()
with open("log.jsonl", "a") as f:
    f.write(json.dumps({"Info": f"Started log at {log_time}"}) + "\n")

FALL_EVENT = pygame.USEREVENT + 1
MUSIC_END = pygame.USEREVENT + 2
SAVE_EVENT = pygame.USEREVENT + 3

pygame.mixer.music.set_endevent(MUSIC_END)

current_track_index = 0
random.shuffle(MUSICS)

joy_config = {}
try:
    with open("joy_map.json", "r") as f:
        raw_map = json.load(f)
        for action, cfg in raw_map.items():
            normalized_combos = []
            if isinstance(cfg, dict):
                normalized_combos = [[cfg]]
            elif isinstance(cfg, list):
                for item in cfg:
                    if isinstance(item, dict):
                        normalized_combos.append([item])
                    elif isinstance(item, list):
                        normalized_combos.append(item)
            joy_config[action] = normalized_combos
except Exception:
    joy_config = {a: [] for a in ["LEFT", "RIGHT", "ROTATE", "HARD_DROP", "SOFT_DROP"]}

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

grid_surf = pygame.Surface((play_area_width, play_area_height), pygame.SRCALPHA)
for current_y in range(0, int(play_area_height) + 1, grid_size):
    pygame.draw.line(grid_surf, "#1f1f1f", (0, current_y), (play_area_width, current_y), 2)
for current_x in range(0, int(play_area_width) + 1, grid_size):
    pygame.draw.line(grid_surf, "#1f1f1f", (current_x, 0), (current_x, play_area_height), 2)

lbl_title = font.render("Tetris 3.0", True, "#ffffff")
lbl_next = font.render("Next:", True, "#ffffff")

def generate_piece(x_pos):
    shape = random.choice(list(entities.TETROMINOES.keys()))
    return entities.Tetromino(x_pos, 0, shape)

def volume(change):
    global volume_level
    volume_level = max(0.0, min(1.0, volume_level + change))
    pygame.mixer.music.set_volume(volume_level)
    for sound in landed:
        sound.set_volume(volume_level)
    clear.set_volume(volume_level)

loaded_tiles = entities.load_and_scale_tiles(grid_size, grid_size)
locked_blocks = {} 

current_piece = generate_piece((play_area_columns // 2) - 2)
next_piece = generate_piece(0)
ghost_y = 0
needs_ghost_update = True

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
            
    if lines_cleared_this_turn > 0:
        clear.play()
    return locked, lines_cleared_this_turn

def cal_bottom(piece, locked):
    original_y = piece.y 
    while valid_position(piece, locked):
        piece.y += 1
    bottom_y = piece.y - 1 
    piece.y = original_y 
    return bottom_y

def log(lines, playtime):
    log_t = time.asctime()
    lines_efficiency = lines / playtime if lines != 0 else 0
    level_names = ["Noob", "Beginner", "Good", "Pro", "Legendary", "God"]
    if lines < 1: level = level_names[0]
    elif lines < 3: level = level_names[1]
    elif lines < 6: level = level_names[2]
    elif lines < 12: level = level_names[3]
    elif lines < 26: level = level_names[4]
    else: level = level_names[5]
    info = {"Lines Cleared": lines, "Lines Efficiency": round(lines_efficiency * 100, 2), "Play Time": playtime, "Level": level, "Log Time": log_t}
    with open("log.jsonl", "a") as f:
        f.write(json.dumps(info) + "\n")

fall_time = 120
save_time = 10000

pygame.time.set_timer(FALL_EVENT, fall_time)
pygame.time.set_timer(SAVE_EVENT, save_time)

total_lines_cleared = 0

space_pressed = False
rotation_pressed = False

DAS = 130
ARR = 20
active_dirs = {"LEFT": False, "RIGHT": False, "DOWN": False}
das_triggered = {"LEFT": False, "RIGHT": False, "DOWN": False}
last_move_time = {"LEFT": 0, "RIGHT": 0, "DOWN": 0}

play_music()

while running:
    current_time_sec = pygame.time.get_ticks() / 1000
    win.fill("#000074")
    pygame.draw.rect(win, "#000000", play_area_r)
    win.blit(grid_surf, (play_area_x, play_area_y))

    joy_actions = {action: False for action in ["LEFT", "RIGHT", "ROTATE", "HARD_DROP", "SOFT_DROP"]}
    hat_x, hat_y = 0, 0

    if is_joy and joystick:
        if joystick.get_numaxes() >= 2:
            hat_x = round(joystick.get_axis(0), 0)
            hat_y = round(joystick.get_axis(1), 0)
        if joystick.get_numhats() > 0 and hat_x == 0 and hat_y == 0:
            hat_x, hat_y = joystick.get_hat(0)

        for action, combos in joy_config.items():
            for combo in combos:
                combo_is_active = True
                for cfg in combo:
                    input_active = False
                    if cfg["type"] == "button" and cfg["index"] < joy_button:
                        input_active = joystick.get_button(cfg["index"])
                    elif cfg["type"] == "axis" and joystick.get_numaxes() > cfg["index"]:
                        val = joystick.get_axis(cfg["index"])
                        if (cfg["dir"] > 0 and val > 0.6) or (cfg["dir"] < 0 and val < -0.6):
                            input_active = True
                    elif cfg["type"] == "hat" and joystick.get_numhats() > cfg["index"]:
                        val = joystick.get_hat(cfg["index"])
                        if val == tuple(cfg["dir"]):
                            input_active = True
                    
                    if not input_active:
                        combo_is_active = False
                        break
                
                if combo_is_active and len(combo) > 0:
                    joy_actions[action] = True
                    break
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == SAVE_EVENT:
            log(total_lines_cleared, current_time_sec)
        
        if event.type == pygame.JOYDEVICEADDED:
            is_joy = True
            joystick = pygame.joystick.Joystick(0)
            joy_button = joystick.get_numbuttons()
        
        if event.type == pygame.JOYDEVICEREMOVED:
            is_joy = False
            joystick = None

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

                current_piece = next_piece
                current_piece.x = (play_area_columns // 2) - 2
                next_piece = generate_piece(0)
                needs_ghost_update = True
                random.choice(landed).play()

                if not valid_position(current_piece, locked_blocks):
                    if is_joy and joystick:
                        joystick.rumble(0.5, 0.5, 1500)
                    locked_blocks = {} 
                    total_lines_cleared = 0 
                    needs_ghost_update = True
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_q:
                volume(-0.03)
            if event.key == pygame.K_e:
                volume(0.03)

    keys = pygame.key.get_pressed()

    if not keys[pygame.K_SPACE] and not joy_actions.get("HARD_DROP", False):
        space_pressed = False
    if not (keys[pygame.K_UP] or keys[pygame.K_w]) and not joy_actions.get("ROTATE", False):
        rotation_pressed = False

    if (keys[pygame.K_UP] or keys[pygame.K_w] or joy_actions.get("ROTATE", False)) and not rotation_pressed:
        rotation_pressed = True
        current_piece.rotate(1)
        if not valid_position(current_piece, locked_blocks):
            current_piece.rotate(-1)
        else:
            needs_ghost_update = True

    input_state = {
        "LEFT": keys[pygame.K_LEFT] or keys[pygame.K_a] or hat_x == -1 or joy_actions.get("LEFT", False),
        "RIGHT": keys[pygame.K_RIGHT] or keys[pygame.K_d] or hat_x == 1 or joy_actions.get("RIGHT", False),
        "DOWN": keys[pygame.K_DOWN] or keys[pygame.K_s] or hat_y == 1 or joy_actions.get("SOFT_DROP", False)
    }

    current_time_ms = pygame.time.get_ticks()

    for direction in ["LEFT", "RIGHT", "DOWN"]:
        move_this_frame = False

        if input_state[direction]:
            if not active_dirs[direction]:
                active_dirs[direction] = True
                das_triggered[direction] = False
                last_move_time[direction] = current_time_ms
                move_this_frame = True
            else:
                time_held = current_time_ms - last_move_time[direction]
                if not das_triggered[direction] and time_held >= DAS:
                    das_triggered[direction] = True
                    last_move_time[direction] = current_time_ms
                    move_this_frame = True
                elif das_triggered[direction] and time_held >= ARR:
                    last_move_time[direction] = current_time_ms
                    move_this_frame = True
        else:
            active_dirs[direction] = False
            das_triggered[direction] = False

        if move_this_frame:
            if direction == "LEFT":
                current_piece.x -= 1
                if not valid_position(current_piece, locked_blocks): 
                    current_piece.x += 1
                else:
                    needs_ghost_update = True
            elif direction == "RIGHT":
                current_piece.x += 1
                if not valid_position(current_piece, locked_blocks): 
                    current_piece.x -= 1
                else:
                    needs_ghost_update = True
            elif direction == "DOWN":
                current_piece.y += 1
                if not valid_position(current_piece, locked_blocks): 
                    current_piece.y -= 1

    if (keys[pygame.K_SPACE] or joy_actions.get("HARD_DROP", False)) and not space_pressed:
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
        
        current_piece = next_piece
        current_piece.x = (play_area_columns // 2) - 2
        next_piece = generate_piece(0)
        needs_ghost_update = True
        
        if not valid_position(current_piece, locked_blocks):
            locked_blocks = {}
            total_lines_cleared = 0
            needs_ghost_update = True
        random.choice(landed).play()

    if needs_ghost_update:
        ghost_y = cal_bottom(current_piece, locked_blocks)
        needs_ghost_update = False

    for (lock_x, lock_y), color in locked_blocks.items():
        tile_image = loaded_tiles[color]
        screen_x = play_area_x + (lock_x * grid_size)
        screen_y = play_area_y + (lock_y * grid_size)
        win.blit(tile_image, (screen_x, screen_y))

    side_panel_x = play_area_x + play_area_width + 50
    side_panel_y = play_area_y + 100
    
    win.blit(lbl_next, (side_panel_x, side_panel_y - 60))
    pygame.draw.rect(win, "#101010", [side_panel_x - 10, side_panel_y - 10, 140, 140])
    next_piece.draw(win, loaded_tiles, grid_size, side_panel_x + 5, side_panel_y + 10)

    current_piece.draw(win, loaded_tiles, grid_size, play_area_x, play_area_y)
    current_piece.draw_ghost(win, loaded_tiles, grid_size, play_area_x, play_area_y, ghost_y)

    win.blit(lbl_title, (10, 10))
    entities.render_txt(font, win, f"Landed: {len(locked_blocks) // 4}", "#ffffff", 10, 70) 
    entities.render_txt(font, win, f"Lines cleared: {total_lines_cleared}", "#ffffff", 10, 130)

    pygame.display.flip()
    clock.tick(60)

log_t = time.asctime()
with open("log.jsonl", "a") as f:
    f.write(json.dumps({"Info": f"Ended log at {log_t}"}) + "\n")
pygame.quit()