import pygame, json, numpy, psutil, sys, subprocess
from os.path import dirname, abspath, exists, getsize, isdir, splitext, basename, join
from os import listdir, makedirs
from datetime import datetime as system_time
from tkinter import messagebox
from time import time as random_seed_generator

class CustomError:
    def __init__(self, error_name, error_message):
        sound_player.play_sound(error_sound)
        messagebox.showerror("Error", f"{error_name}: {error_message}")
        pygame.quit()
        sys.exit()

pygame.init()
pygame.font.init()
pygame.mixer.init()

is_executable = getattr(sys, "frozen", False)

infinity = float("inf")
pi = 3.141592653589793
main_directory = dirname(sys.executable if is_executable else abspath(__file__))

def get_text_from_language(text):
    language_text = load_json(join("languages", get_key(splitext(language), 0)), text)
    if language_text is None:
        raise CustomError("LanguageError", f"Missing {text} in {language}!")
    else:
        return str(language_text)

def random_number(a, b):
    return a + ((int((random_seed_generator() - int(random_seed_generator())) * 1e9) ^ (int((random_seed_generator() - int(random_seed_generator())) * 1e9) >> 21)) & 0xFFFFFFFF) % (b - a + 1)

def random_symmetric(num):
    return random_number(-num, num)

def random_list_item(seq):
    if not seq:
        raise IndexError(get_text_from_language("Cannot choose from an empty sequence"))
    return get_key(seq, random_number(0, len(seq) - 1))

def is_tuple_of_tuples(value):
    return isinstance(value, tuple) and all(isinstance(item, tuple) for item in value)

def get_start(text, num_chars):
    return text[:num_chars]

def fix_list(obj):
    return obj[:]
    
def key_exists(bundle, key):
    return key in bundle

def get_key(obj, *keys, default=None, type=None):
    try:
        for key in keys:
            obj = obj[key]
        if type is not None and not isinstance(obj, type):
            return default
        return obj
    except Exception:
        return default
    
def set_key(obj, *keys):
    def setter(value):
        target = obj
        for i, key in enumerate(get_start(keys, -1)):
            next_key = get_key(keys, i + 1)

            if isinstance(key, int):
                while len(target) <= key:
                    target.append([] if isinstance(next_key, int) else {})
            else:
                if nor(key_exists(target, key), isinstance(get_key(target, key), (dict, list))):
                    target[key] = [] if isinstance(next_key, int) else {}
            target = get_key(target, key)

        last_key = get_key(keys, -1)
        if isinstance(last_key, int):
            while len(target) <= last_key:
                target.append(None)
        target[last_key] = value

    return setter

def set_attr(obj, *keys):
    def setter(value):
        target = obj
        for key in get_start(keys, -1):
            target = getattr(target, key)
        setattr(target, get_key(keys, -1), value)
    return setter
    
def get_nitpick(nitpick):
    return get_key(globals(), nitpick)

def is_negative(value):
    return 1 if value >= 0 else -1

def radians(deg):
    return deg * (pi / 180)

def sin(num):
    num = num % (2 * pi)
    if num > pi:
        num -= 2 * pi

    term = num
    result = 0
    n = 0

    while abs(term) > 1e-15:
        result += term
        n += 1
        term *= -num * num / ((2 * n) * (2 * n + 1))

    return result

def cos(num):
    return sin(num + pi / 2)

def floor(num):
    return int(num) if num >= 0 or num == int(num) else int(num) - 1

def ceil(num):
    return int(num) if num == int(num) or num < 0 else int(num) + 1

def set_image_alpha(image, alpha=1):
    try:
        alpha = float(alpha)
        if not (0 <= alpha <= 1):
            raise ValueError(get_text_from_language(f"Expected value between 0 and 1, got {alpha}."))
    except:
        alpha = 1

    image = image.convert_alpha()
    image.set_alpha(alpha * 255)

    return image

def mean(*numbers):
    try:
        return sum(numbers) / len(numbers)
    except:
        return 0

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(color1, color2, t):
    return [floor(get_key(color1, i) + (get_key(color2, i) - get_key(color1, i)) * t) for i in range(3)]

def load_local_file(file):
    return join(main_directory, file)

def load_system_file(file):
    return join(load_local_file("system"), file)

def load_intro_file(file):
    return load_system_file(join("intro", file))

def load_menu_tooltip(file):
    return pygame.image.load(load_system_file(join("menu tooltips", file))).convert_alpha()

if not exists(load_local_file("courses")):
    makedirs(load_local_file("courses"))

if not exists(load_local_file("textures")):
    makedirs(load_local_file("textures"))

def load_json(path, *keys, default=None):
    try:
        with open(load_local_file(f"{path}.json"), "r", encoding="utf-8") as file:
            json_file = json.load(file)

        for key in keys:
            json_file = get_key(json_file, key)
        return json_file
    except (KeyError, TypeError, FileNotFoundError, json.JSONDecodeError):
        return default

asset_directory = load_json("settings", "asset_directory", default="assets")

if not isdir(load_local_file(asset_directory)):
    asset_directory = "assets"

old_asset_directory = asset_directory

course_directory = load_json("settings", "course_directory", default="classic")

if not isdir(load_local_file(course_directory)):
    course_directory = "classic"

def get_folders(directory):
    return [folder for folder in listdir(load_local_file(directory))]

def load_asset(asset):
    return load_local_file(join(asset_directory if exists(load_local_file(join(asset_directory, asset))) else "assets", asset))

def replace_infinity(obj):
    if isinstance(obj, dict):
        return {k: replace_infinity(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_infinity(i) for i in obj]
    elif obj == "infinity":
        return infinity
    else:
        return obj

def get_game_property(*items, default=None):
    try:
        data = load_json(join(asset_directory, "game_properties"))
        backup_data = load_json(join("assets", "game_properties"))

        for item in items:
            if isinstance(data, list):
                if isinstance(item, int) and item < len(data):
                    data = get_key(data, item)
                elif isinstance(backup_data, list) and isinstance(item, int) and item < len(backup_data):
                    data = get_key(backup_data, item)
                else:
                    return default
            elif isinstance(data, dict):
                if not key_exists(data, item):
                    if isinstance(backup_data, dict) and key_exists(backup_data, item):
                        set_key(data, item)(get_key(backup_data, item))
                    else:
                        return default
                data = get_key(data, item)
            else:
                return default

            if isinstance(backup_data, list) and isinstance(item, int) and item < len(backup_data):
                backup_data = get_key(backup_data, item)
            elif isinstance(backup_data, dict):
                backup_data = get_key(backup_data, item, default=None)

        def deep_merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                for k in b:
                    set_key(a, k)(deep_merge(get_key(a, k), get_key(b, k)) if key_exists(a, k) else get_key(b, k))
                return a
            elif isinstance(a, list) and isinstance(b, list):
                result = list(a)
                for i in count_list_items(b):
                    if i >= len(result):
                        result.append(get_key(b, i))
                    else:
                        set_key(result, i)(deep_merge(get_key(result, i), get_key(b, i)))
                return result
            return a if a is not None else b

        if isinstance(data, (dict, list)) and isinstance(backup_data, (dict, list)):
            data = deep_merge(data, backup_data)

        return replace_infinity(data) if data is not None else default
    except:
        return default


def load_background(background):
    return pygame.image.load(load_asset(join("backgrounds", f"{background}.png"))).convert_alpha()

def load_sound(sound):
    return pygame.mixer.Sound(load_asset(join("sounds", f"{sound}.wav")))
    
def load_sprite(sprite):
    return pygame.image.load(load_asset(join("sprites", f"{sprite}.png"))).convert_alpha()
    
def range_number(num, minval, maxval):
    return min(max(num, minval), maxval)

def count_list_items(array):
    return range(len(array))

def format_number(num, digits):
    return f"{num:0{digits}d}" if num < (10 ** digits) else num

def nand(*conditions):
    return not all(conditions)

def nor(*conditions):
    return not any(conditions)

def xor(a, b):
    return (a or b) and not (a and b)

def scale_image(image, scale_factor=1):
    if isinstance(scale_factor, (int, float)):
        new_width = int(image.get_width() * abs(scale_factor))
        new_height = int(image.get_height() * abs(scale_factor))
    elif isinstance(scale_factor, (list, tuple)) and len(scale_factor) == 2:
        new_width = int(image.get_width() * abs(get_key(scale_factor, 0)))
        new_height = int(image.get_height() * abs(get_key(scale_factor, 1)))
    else:
        raise ValueError(f"{get_text_from_language("Invalid type for 'scale_factor': expected int, float, list, or tuple, got")} {type(scale_factor).__name__}.")

    new_surface = pygame.Surface((new_width * 2, new_height * 2), pygame.SRCALPHA)
    new_surface.blit(pygame.transform.scale(image, (new_width, new_height)), (mean((new_width * 2) - new_width, -image.get_width()), mean((new_height * 2) - new_height, -image.get_height())))
    return new_surface

def split_image(image, cols=1, rows=1):
    image_width, image_height = image.get_size()
    cell_width = image_width // cols
    cell_height = image_height // rows
    cells = []

    for row in range(rows):
        for col in range(cols):
            surface = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            surface.blit(image, (0, 0), (col * cell_width, row * cell_height, cell_width, cell_height))
            cells.append(surface)

    return cells

def create_course(file, dont_reset_timer=False):
    data = replace_infinity(load_json(file))

    pygame.display.update()

    default_music = get_key(data, "default_music", default="overworld")
    main_music = get_key(data, "music", default=default_music)

    def get_music(fanfare):
        return join("music", main_music, fanfare) if exists(load_asset(join("music", main_music, fanfare))) else fanfare

    music_list = {
        "default_music": default_music,
        "main_music": main_music,
        "clear_music": get_music("clear"),
        "dead_music": get_music("dead"),
        "hurry_music": get_music("hurry"),
        "star_music": get_music("star"),
    }

    for key, value in music_list.items():
        set_key(globals(), key)(value)

    set_key(globals(), "background")(get_key(data, "background", default="ground", type=str))
    set_key(globals(), "y_range")(get_key(data, "height", default=25, type=int) * 16)
    set_key(globals(), "asset_directory")(get_key(data, "texture", default=asset_directory))

    if not get_key(globals(), "old_asset_directory") == get_key(globals(), "asset_directory"):
        set_key(globals(), "old_asset_directory")(get_key(globals(), "asset_directory"))
        reload_data()
        set_key(globals(), "camera").x = 0
        set_key(globals(), "camera").y = 0
        intro_players = []
        for i in count_list_items(characters_name):
            try:
                player = Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, controls_enabled=False, size=1, player_number=i, walk_cutscene=True)
            except:
                player = None
            if player is not None:
                intro_players.append(player)
        set_key(globals(), "all_players")(len(intro_players))

    set_key(globals(), "time")(get_key(globals(), "course_time") if dont_reset_timer else (0 if get_game_property("use_elapsed_time") else (100 if get_nitpick("hurry_mode") else get_key(data, "timelimit", default=400, type=(int, float)))))
    set_key(globals(), "course_time")(get_key(globals(), "time"))

    set_key(globals(), "show_course_name")(not dont_reset_timer)
    set_key(globals(), "show_progress_bar")(get_key(data, "show_progress_bar", default=True, type=bool))

    set_key(globals(), "course_name")(get_key(data, "course_name", default=get_key(splitext(basename(file)), 0)) if get_key(globals(), "show_course_name") else None)

    tiles = []
    if get_key(data, "tiles", type=dict):
        for class_name, params_list in get_key(data, "tiles", type=dict).items():
            if class_name == "Pipe":
                for params in params_list:
                    x, y = get_start(params, 2)
                    length = get_key(params, 2, default=2, type=int)
                    can_enter = get_key(params, 3, default=False, type=(bool, str))
                    new_zone = get_key(params, 4, default=None, type=int)
                    pipe_dir = get_key(params, 4, default="up", type=str)
                    color = get_key(params, 6, default=0, type=int)

                    id_adjustments = {
                        "up": lambda pid: pid,
                        "down": lambda pid: pid + (4 if key_exists({1, 2}, pid) else 0),
                        "left": lambda pid: pid + (pid == 3) * 8 + (pid == 4) * 4 + (pid == 1) * 11 + (pid == 2) * 7,
                        "right": lambda pid: pid + (pid == 3) * 8 + (pid == 4) * 4 + (pid == 1) * 9 + (pid == 2) * 5
                    }

                    coord_adjustments = {
                        "up": lambda i, j: (x + i, y + j),
                        "down": lambda i, j: (x + i, y - j),
                        "left": lambda i, j: (x - j, y - i),
                        "right": lambda i, j: (x + j, y - i)
                    }

                    for i in range(2):
                        for j in range(length):
                            pipe_id = i + (j * 2) + 1
                            while pipe_id >= 5:
                                pipe_id -= 2

                            px, py = get_key(coord_adjustments, pipe_dir)(i, j)
                            tile_img = get_key(split_image(load_sprite("pipe"), 16), get_key(id_adjustments, pipe_dir)(pipe_id) - 1)
                            tiles.append(Tile(px, py, tile_img, color))

                            if can_enter and i == 0 and j == 0:
                                pipe_markers.append(PipeMarker(px + (0.5 if key_exists(("up", "down"), pipe_dir) else 0), py + (1 if key_exists(("left", "right"), pipe_dir) else 0), pipe_dir, new_zone))
            elif key_exists(globals(), class_name) and callable(get_key(globals(), class_name)):
                for params in params_list:
                    obj_params = [get_key(globals(), param) if get_key(globals(), param, type=str) and callable(get_key(globals(), param)) else param for param in (params if isinstance(params, (list, tuple)) else [params])]
                    obj = get_key(globals(), class_name)(*obj_params, **({"tileset": get_key(data, "tileset", default="ground", type=str)} if class_name == "Ground" else {}))
                    if hasattr(obj, "spriteset"):
                        obj.spriteset = (1 if hasattr(obj, "is_ground") and obj.is_ground else get_key(data, "spriteset", default=1)) - 1
                        if hasattr(obj, "tileset"):
                            obj.tileset = get_key(data, "tileset", default="ground", type=str)

                    tiles.append(obj)

    if get_key(data, "castle", type=list):
        set_key(globals(), "castle")(get_key(data, "castle"))

        if key_exists(globals(), "Castle") and callable(get_key(globals(), "Castle")):
            castle_obj = get_key(globals(), "Castle")(*get_key(data, "castle"))
            castle_obj.spriteset = get_key(data, "spriteset", default=1) - 1
            set_key(globals(), "castle")(castle_obj)

    set_key(globals(), "x_range")((max(40, get_key(data, "width", type=int, default=40)) - (SCREEN_WIDTH / 16)) * 16)
    set_key(globals(), "underwater")(get_key(data, "underwater", type=bool, default=False) or get_nitpick("always_underwater"))
    set_key(globals(), "inverthorizontal")(get_key(data, "inverthorizontal", type=bool, default=False))
    set_key(globals(), "invertvertical")(get_key(data, "invertvertical", type=bool, default=False))
    set_key(globals(), "vertical")(get_key(data, "vertical", type=bool, default=False) and nor(get_key(globals(), "inverthorizontal"), get_key(globals(), "invertvertical")))

    if get_key(data, "flagpole", type=list):
        set_key(globals(), "flagpole")(get_key(globals(), "Flagpole")(*get_key(data, "flagpole")))

    set_key(globals(), "tiles")(tiles)

    if get_key(data, "spawnpositions", type=list):
        set_key(globals(), "spawnposx")(get_key(data, "spawnpositions", 0) * 16)
        set_key(globals(), "spawnposy")((get_key(data, "spawnpositions", 1) - 5) * 16 - 1)

    for category, items in data.items():
        if key_exists(("tiles", "castle", "background", "tileset", "underwater", "vertical", "invertvertical", "inverthorizontal", "flagpole"), category):
            continue

        object_list = []
        if isinstance(items, dict):
            for class_name, params_list in items.items():
                if key_exists(globals(), class_name) and callable(get_key(globals(), class_name)):
                    for params in params_list:
                        obj_params = [get_key(globals(), param) if get_key(globals(), param, type=str) and callable(get_key(globals(), param)) else param for param in (params if isinstance(params, (list, tuple)) else [params])]
                        obj = get_key(globals(), class_name)(*obj_params)
                        if hasattr(obj, "spriteset"):
                            obj.spriteset = get_key(data, "spriteset", default=1) - 1

                        object_list.append(obj)

        set_key(globals(), category)(object_list)

def initialize_game(reset_fast_music=True):
    set_key(globals(), "menu")(False)
    set_key(globals(), "pause")(False)
    set_key(globals(), "game_ready")(False)
    set_key(globals(), "reset_ready")(False)
    set_key(globals(), "pipe_ready")(False)
    set_key(globals(), "everyone_dead")(False)
    set_key(globals(), "game_over")(False)
    set_key(globals(), "fast_music")(time <= 100 and not reset_fast_music)
    set_key(globals(), "fade_out")(True)
    set_key(globals(), "game")(True)
    set_key(globals(), "intro_players")(None)
    set_key(globals(), "logo")(None)
    set_key(globals(), "title_ground")(None)
    set_key(globals(), "castle_obj")(None)
    set_key(globals(), "dt")(0)
    set_key(globals(), "game_dt")(0)
    set_key(globals(), "pipe_wait_timer")(0)
    set_key(globals(), "players")([])
    set_key(globals(), "players_hud")([])
    set_key(globals(), "power_meters")([])
    set_key(globals(), "tiles")([])
    set_key(globals(), "pipe_markers")([])
    set_key(globals(), "items")([])
    set_key(globals(), "enemies")([])
    set_key(globals(), "debris")([])
    set_key(globals(), "particles")([])
    set_key(globals(), "overlay_particles")([])
    set_key(globals(), "overlays")([])
    set_key(globals(), "fireballs_table")({str(i): [] for i in range(player_count)})
    set_key(globals(), "hud")(CoinHUD())
    set_key(globals(), "progress_bar")(ProgressBar())
    set_key(globals(), "camera").x = 0
    set_key(globals(), "camera").y = 0

def reload_data():
    set_key(globals(), "MAX_RUN_TIMER")(get_game_property("character_properties", "max_run_timer") * 10)
    set_key(globals(), "characters_data")(get_game_property("character_properties", "character_data"))
    set_key(globals(), "characters_name")([get_game_property("character_properties", "character_data", i, "name") for i in count_list_items(get_key(globals(), "characters_data"))])
    set_key(globals(), "characters_color")([get_game_property("character_properties", "character_data", i, "color") for i in count_list_items(get_key(globals(), "characters_data"))])
    set_key(globals(), "camera")(Camera(get_game_property("camera_smoothness")))
    set_key(globals(), "text")(Text())
    pygame.display.set_icon(pygame.image.load(load_asset("icon.ico")))
    if menu:
        set_attr(get_key(globals(), "logo"), "spritesheet")(load_sprite("logo"))
        set_attr(get_key(globals(), "title_ground"), "sprite")(split_image(load_sprite("tiles_ground"), 8, 6))
    for name in sound_names:
        set_key(globals(), f"{name}_sound")(load_sound(name))

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 400
MIN_RUN_TIMER = 0
MAX_RUN_TIMER = get_game_property("character_properties", "max_run_timer") * 10
JUMP_HOLD_TIME = 10
FPS = range_number(load_json("settings", "fps", default=60), 1, 120)
OLD_FPS = FPS
FADE_DURATION = 30
SPROUT_SPEED = 0.9125
STAR_EFFECT_DURATION = 4

error_sound = pygame.mixer.Sound(load_system_file("error.wav"))
konami_sound = pygame.mixer.Sound(load_system_file("konami.wav"))

sound_names = ["beep", "break", "bump", "coin", "dead", "fireball", "jump", "jumpbig", "oneup", "pause", "pipe", "powerup", "pspeed", "shot", "shrink", "skid", "sprout", "stomp", "swim"]

for name in sound_names:
    set_key(globals(), f"{name}_sound")(pygame.mixer.Sound(load_local_file(join("assets", "sounds", f"{name}.wav"))))

class StarEffect:
    def __init__(self, x, y, color, random_boundary=16, sticktocamera=False):
        self.x = x + random_symmetric(get_key(random_boundary, 0, default=8, type=(int, float, tuple, list)))
        self.y = y + random_symmetric(get_key(random_boundary, 1, default=8, type=(int, float, tuple, list)))
        self.timer = 0
        self.sprite = load_sprite("stareffect")
        self.sprites = [pygame.Rect(16 * i, 0, 16, 16) for i in range(4)]
        self.color = color
        self.sticktocamera = sticktocamera

    def update(self):
        self.timer += 1
        if self.timer >= 16:
            self.timer = 0
            if key_exists(particles, self):
                particles.remove(self)
            else:
                overlay_particles.remove(self)

    def draw(self):
        frame_index = get_key(self.sprites, int(self.timer / 4))
        sprite = self.sprite.subsurface(frame_index)
        sprite.fill(self.color, special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(sprite, (self.x - (0 if self.sticktocamera else camera.x), self.y - (0 if self.sticktocamera else camera.y)))

class ProgressBar:
    def __init__(self):
        self.x = centerx
        self.y = 8
        self.playerdist = 0
        self.oldplayerdist = 0
        self.progress = 0
        self.height = 8
        self.bar_width = 100
        self.circle_radius = self.height / 2
        self.rainbow_timer = 0

        self.colors = get_game_property("progress_bar_colors")
        if not isinstance(self.colors, list) or not all(isinstance(c, (list, tuple)) and len(c) == 3 for c in self.colors):
            raise CustomError("GamePropertyError", f"{get_text_from_language("Invalid type for 'progress_bar_colors' in game_properties.json: expected list of RGB triplets, got")} {type(self.colors).__name__}.")

        if len(self.colors) < 2:
            raise CustomError("GamePropertyError", f"{get_text_from_language("'progress_bar_colors' must contain at least 2 colors.")}")

        self.color_start = get_key(self.colors, 0)
        self.color_mid = get_key(self.colors, len(self.colors) // 2)
        self.color_end = get_key(self.colors, -1)

        self.color = get_game_property("star_colors", 0) if get_nitpick("rainbow_progress_bar") else self.color_start
        self.full_surface = pygame.Surface((self.bar_width + int(self.circle_radius * 2) + 2, self.height + int(self.circle_radius * 2) + 2), pygame.SRCALPHA)
        self.offset_surface = pygame.Surface(self.full_surface.get_size(), pygame.SRCALPHA)
        self.draw_left = self.circle_radius + 1
        self.draw_top = self.circle_radius + 1

    def update(self):
        self.playerdist = (min if vertical or inverthorizontal else max)(mean(*[(player.rect.y if vertical or invertvertical else player.rect.x) + ((player.rect.height if vertical or invertvertical else player.rect.width) // 2) for player in players]), self.oldplayerdist)
        self.progress = range_number((self.playerdist - spawnposx) / (flagpole.x - spawnposx), 0, 1)
        self.oldplayerdist = self.playerdist if ((vertical and self.playerdist < self.oldplayerdist) or (not vertical and self.playerdist > self.oldplayerdist)) else self.oldplayerdist
        self.rainbow_timer += 1
        self.color = lerp_color(get_key(get_game_property("star_colors"), (self.rainbow_timer // 10) % len(get_game_property("star_colors"))), get_key(get_game_property("star_colors"), ((self.rainbow_timer // 10) % len(get_game_property("star_colors")) + 1) % len(get_game_property("star_colors"))), (self.rainbow_timer % 10) / 10) if get_nitpick("rainbow_progress_bar") else get_key(self.colors, -1) if (i := int(self.progress * (n := len(self.colors) - 1))) >= n else lerp_color(get_key(self.colors, i), get_key(self.colors, i + 1), self.progress * n - i)

    def draw(self):
        def draw_shapes(surface, color):
            pygame.draw.circle(surface, color, (self.draw_left, self.draw_top + self.circle_radius), self.circle_radius)
            pygame.draw.circle(surface, color, (self.draw_left + self.bar_width, self.draw_top + self.circle_radius), self.circle_radius)
            pygame.draw.rect(surface, color, pygame.Rect(self.draw_left, self.draw_top, self.bar_width, self.height))

        if get_game_property("font_outline"):
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw_shapes(self.offset_surface, (0, 0, 0))
                self.full_surface.blit(self.offset_surface, (dx, dy))

        draw_shapes(self.full_surface, self.color)

        screen.blit(self.full_surface.subsurface(pygame.Rect(0, 0, (self.bar_width + self.circle_radius * 2) * (self.progress * (1.02 if get_game_property("font_outline") else 1)), self.full_surface.get_height())), (self.x - self.bar_width // 2 - self.circle_radius - 1, self.y + 12 - self.circle_radius - 1))

        text.create_text(
            text=f"{round(self.progress * 100)}%",
            position=(self.x, self.y),
            alignment="center",
            color=self.color,
            stickxtocamera=True,
            stickytocamera=True,
            scale=0.5
        )

class Flagpole:
    def __init__(self, x, y, height=8):
        self.x, self.y = x * 16, y * 16
        self.image = [load_sprite("flagpole"), load_sprite("flag")]
        self.height = height + 1
        self.sprites = [pygame.Rect(0, 16 * i, 16, 16) for i in range(2)]
        self.flag_sprite_data = get_game_property("flagpole")
        self.flag_sprite_size = get_key(self.image, 1).get_size()
        self.flag_sprite = [pygame.Rect((get_key(self.flag_sprite_size, 0) / get_key(self.flag_sprite_data, "frames")) * i, 0, get_key(self.flag_sprite_size, 0) / get_key(self.flag_sprite_data, "frames"), get_key(self.flag_sprite_size, 1)) for i in range(get_key(self.flag_sprite_data, "frames"))]
        self.dt = 0
        self.frame_index = 0
        self.flag_offset = 0

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt / 60) / get_key(self.flag_sprite_data, "speed")) % get_key(self.flag_sprite_data, "frames")

    def draw(self):
        screen.blit(get_key(self.image, 0).subsurface(get_key(self.sprites, 0)), (self.x - camera.x, self.y - camera.y - (self.height * 16)))
        for i in range(self.height):
            screen.blit(get_key(self.image, 0).subsurface(get_key(self.sprites, 1)), (self.x - camera.x, self.y - camera.y - (i * 16)))
        screen.blit(get_key(self.image, 1).subsurface(get_key(self.flag_sprite, self.frame_index)), (self.x - camera.x - ((get_key(self.flag_sprite_size, 0) / get_key(self.flag_sprite_data, "frames")) / 2), self.y - camera.y - ((self.height - 1) * 16)))

class PipeMarker:
    def __init__(self, x, y, pipe_dir, zone, exit=False):
        self.x = x * 16
        self.y = y * 16 + 8
        self.exit = exit
        if pipe_dir == "up":
            self.y -= 1
        elif pipe_dir == "down":
            self.y += 1
        elif pipe_dir == "left":
            self.x += 1
            self.y -= 16
        elif pipe_dir == "right":
            self.x -= 1
            self.y -= 16
        self.pipe_dir = pipe_dir
        self.zone = zone
        self.rect = pygame.Rect(self.x, self.y, 16, 16)

class SFXPlayer:
    def __init__(self):
        self.sounds = {}
        self.paused = False

    def play_sound(self, *args):
        sounds_to_play = []

        for arg in args:
            if isinstance(arg, list):
                if len(arg) == 2:
                    sounds_to_play.append(tuple(arg))
                elif len(arg) == 1:
                    sounds_to_play.append((get_key(arg, 0), 0))
                else:
                    raise ValueError(f"{get_text_from_language("Invalid list argument:")} {arg}")
            else:
                sounds_to_play.append((arg, 0))

        for sound, pitch in sounds_to_play:
            if not key_exists(self.sounds, sound):
                set_key(self.sounds, sound)(sound)

            pitched_sound = self.change_pitch(get_key(self.sounds, sound), pitch)
            pitched_sound.set_volume(snd_vol)
            pitched_sound.stop()
            pitched_sound.play()

    def change_pitch(self, sound, semitones):
        return sound if semitones == 0 else pygame.sndarray.make_sound(get_key(pygame.sndarray.array(sound), numpy.round(numpy.linspace(0, len(pygame.sndarray.array(sound)) - 1, int(len(pygame.sndarray.array(sound)) / (2 ** (semitones / 12))))).astype(int)))

    def stop_sound(self, *sounds):
        for sound in sounds:
            if key_exists(self.sounds, sound):
                get_key(self.sounds, sound).stop()

    def stop_all_sounds(self):
        for sound in self.sounds.values():
            sound.stop()

    def loop_sound(self, sound):
        set_key(self.sounds, sound)(sound)
        if key_exists(self.sounds, sound) and not self.is_playing(get_key(self.sounds, sound)):
            get_key(self.sounds, sound).set_volume(snd_vol)
            get_key(self.sounds, sound).play(-1)

    def set_volume(self, volume):
        for sound in self.sounds:
            get_key(self.sounds, sound).set_volume(volume)

    def is_playing(self, *sounds):
        return any(sound.get_num_channels() > 0 for sound in sounds)

    def pause(self):
        self.paused = not self.paused
        (pygame.mixer.pause if self.paused else pygame.mixer.unpause)()

class BGMPlayer:
    def __init__(self):
        self.loop_point = 0
        self.music = None
        self.music_playing = False
        self.paused = False

    def play_music(self, music, reloop_music=False):
        if reloop_music:
            self.music = False
        if nor(self.paused, self.music == load_asset(join("music", f"{music}.ogg"))):
            self.stop_music()
            self.music = load_asset(join("music", f"{music}.ogg"))
            self.loop_point = get_game_property("loop_points", music, default=False)
            if nor(isinstance(self.loop_point, (int, bool)), self.loop_point is None):
                raise CustomError("LoopPointError", f"{get_text_from_language("Invalid type for 'loop_points' in game_properties.json: expected int, got")} {type(self.loop_point).__name__}.")
            pygame.mixer.music.load(self.music)
            pygame.mixer.music.play(-1 if self.loop_point == True else 0)
            self.set_volume(mus_vol)
            if isinstance(self.loop_point, int) and not self.loop_point == 0:
                self.loop_point /= 1000
                self.music_playing = True
            else:
                if self.loop_point == True:
                    self.music_playing = False

    def stop_music(self):
        self.music_playing = False
        pygame.mixer.music.stop()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def fade_out(self):
        self.music_playing = False
        pygame.mixer.music.fadeout(int(FADE_DURATION * (1000 / clock.get_fps())))

    def pause_music(self):
        if get_nitpick("play_music_in_pause"):
            return
        self.paused = not self.paused
        (pygame.mixer.music.pause if self.paused else pygame.mixer.music.unpause)()

    def update(self):
        if self.music_playing:
            if nor(self.paused, pygame.mixer.music.get_busy()):
                pygame.mixer.music.play(0, self.loop_point)
                self.music_playing = True

    def is_playing(self, music):
        return pygame.mixer.music.get_busy() and self.music == load_asset(join("music", f"{music}.ogg"))

class Text:
    def __init__(self):
        self.font_size = get_game_property("font_size")
        self.font = pygame.font.Font(load_asset("font.ttf"), self.font_size)

    def create_text(self, text, position, color=(255, 255, 255), alignment="left", stickxtocamera=False, stickytocamera=False, scale=1, font=None, font_size=None, outline=True, make_caps=True):
        text = str(text)
        if make_caps:
            text = text.upper()
        font_size = self.font_size if font_size is None else font_size
        font = self.font if font is None else pygame.font.Font(font, font_size)
        x, y = position

        lines = text.split("\n")
        rendered_lines = []
        char_colors = None

        if isinstance(color, (tuple, list)) and len(color) > 0 and isinstance(get_key(color, 0), (tuple, list)):
            char_colors = color

        global_char_index = 0

        for line in lines:
            if char_colors:
                surfaces = []
                line_width = 0
                line_height = 0

                for char in line:
                    char_surface = font.render(char, True, tuple(get_key(char_colors, global_char_index)) if global_char_index < len(char_colors) else (255, 255, 255))
                    if scale != 1.0:
                        char_surface = pygame.transform.scale(char_surface, (int(char_surface.get_width() * scale), int(char_surface.get_height() * scale)))
                    surfaces.append(char_surface)
                    line_width += char_surface.get_width()
                    line_height = max(line_height, char_surface.get_height())
                    global_char_index += 1

                text_surface = pygame.Surface((line_width, line_height), pygame.SRCALPHA)
                offset = 0
                for s in surfaces:
                    text_surface.blit(s, (offset, 0))
                    offset += s.get_width()

            else:
                text_surface = font.render(line, True, color)
                if scale != 1.0:
                    text_surface = pygame.transform.scale(text_surface, (int(text_surface.get_width() * scale), int(text_surface.get_height() * scale)))

                line_width, line_height = text_surface.get_size()

            if get_game_property("font_outline") and outline:
                outline_size = scale * 2
                outline_surface = pygame.Surface((int(text_surface.get_width() + outline_size * 2), int(text_surface.get_height() + outline_size * 2)), pygame.SRCALPHA)

                temp_surface = font.render(line, True, (0, 0, 0))
                if scale != 1.0:
                    temp_surface = pygame.transform.scale(temp_surface, (int(text_surface.get_width()), int(text_surface.get_height())))

                for dx in [-outline_size, 0, outline_size]:
                    for dy in [-outline_size, 0, outline_size]:
                        if dx == 0 and dy == 0:
                            continue
                        outline_surface.blit(temp_surface, (dx + outline_size, dy + outline_size))

                outline_surface.blit(text_surface, (outline_size, outline_size))
                text_surface = outline_surface

            rendered_lines.append((text_surface, text_surface.get_width(), text_surface.get_height()))

        for i, (text_surface, text_width, _) in enumerate(rendered_lines):
            line_x = x
            line_y = y + i * (scale * (font_size ** 2) / 10)

            if alignment == "center":
                line_x -= text_width // 2
            elif alignment == "right":
                line_x -= text_width

            screen.blit(text_surface, (line_x - (0 if stickxtocamera else camera.x), line_y - (0 if stickytocamera else camera.y)))

    def wrap_text(self, text, width):
        words = text.split()
        lines = []
        current_line = ''

        for word in words:
            if len(current_line + ' ' + word) <= width:
                current_line = current_line + ' ' + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return '\n'.join(lines)

class Background:
    def __init__(self):
        self.bg_image = None
        self.bg_layers = []
        self.bg_positions = []
        self.layer_width = 0
        self.bg_width = 0
        self.bg_height = 0
        self.parallax_offset = get_game_property("parallax_offset", default=1)

    def load_background(self, bgname):
        self.bg_layers_count = get_game_property("background_layers", bgname)
        self.bg_image = load_background(bgname)
        self.bg_width, self.bg_height = self.bg_image.get_size()
        self.layer_width = self.bg_width // self.bg_layers_count
        self.bg_layers = [self.bg_image.subsurface(pygame.Rect(x * self.layer_width, 0, self.layer_width, self.bg_height)) for x in range(self.bg_layers_count)]
        self.bg_positions = [0] * self.bg_layers_count

    def update(self):
        for i in count_list_items(self.bg_layers):
            self.bg_positions[i] -= camera.x * (1 - (i / len(self.bg_layers) * 0.8))
            self.bg_positions[i] /= self.parallax_offset
            self.bg_positions[i] %= self.layer_width

    def draw(self):
        for i in count_list_items(self.bg_layers):
            layer_x = get_key(self.bg_positions, i)
            while layer_x < SCREEN_WIDTH:
                screen.blit(get_key(self.bg_layers, i), (layer_x, SCREEN_HEIGHT - self.bg_height))
                layer_x += self.layer_width
            layer_x = get_key(self.bg_positions, i) - self.layer_width
            while layer_x < 0:
                screen.blit(get_key(self.bg_layers, i), (layer_x, SCREEN_HEIGHT - self.bg_height))
                layer_x += self.layer_width

class Camera:
    def __init__(self, smoothing=1):
        self.x = 0
        self.y = 0
        self.smoothing = 1 if smoothing == 0 else smoothing

    def update(self, players, max_x=None, max_y=None):
        self.x += (((mean(*[player.rect.x + player.rect.width // 2 for player in players])) - centerx) - self.x) / self.smoothing
        self.y += (((mean(*[player.rect.y + player.rect.height // 2 for player in players])) - centery) - self.y) / self.smoothing
        self.x = range_number(self.x, 0, max_x if max_x is not None else infinity)
        self.y = range_number(self.y, 0, max_y if max_y is not None else infinity)

class Logo:
    def __init__(self):
        self.spritesheet = load_sprite("logo")
        self.spritesheet_size = self.spritesheet.get_size()
        self.x = centerx
        self.y = -get_key(self.spritesheet_size, 1)
        self.speedy = 0
        self.timer = 0
        self.bounce_y = 48
        self.bounce_time = 3
        self.shift_timer = 0

    def update(self):
        self.timer = min(self.timer + 1, self.bounce_time * 60)
        canbounce = self.y < self.bounce_y
        if self.timer < self.bounce_time * 60:
            self.y += self.speedy
            self.speedy += 0.25
        if self.y > self.bounce_y and canbounce and self.timer > 0 and not self.speedy == 0:
            sound_player.play_sound(bump_sound)
            self.speedy /= -1.5
            self.y -= 0.25
        if self.timer >= self.bounce_time * 60:
            self.shift_timer += 1
            if self.y > self.bounce_y:
                sound_player.play_sound(bump_sound)
                self.speedy = 0
                self.y = self.bounce_y

    def draw(self):
        screen.blit(self.spritesheet, ((self.x - (self.x / 2) * (1 - cos(min(self.shift_timer, FADE_DURATION) / FADE_DURATION * pi)) / 2) - (get_key(self.spritesheet_size, 0) // 2), self.y))

class TitleGround:
    def __init__(self):
        self.y = SCREEN_HEIGHT - 24
        self.sprite = split_image(load_sprite("tiles_ground"), 8, 6)

    def draw(self):
        for i in range((SCREEN_WIDTH // 16) + 1):
            x = i * 16
            screen.blit(get_key(self.sprite, 1), (x - (camera.x % 16), self.y - camera.y))
            screen.blit(get_key(self.sprite, 9), (x - (camera.x % 16), self.y + 16 - camera.y))

class PowerMeter:
    def __init__(self, player):
        self.spritesheet = load_sprite("powermeter")
        self.spritesheet_width, self.spritesheet_height = self.spritesheet.get_size()
        self.power_meter_quads = get_game_property("power_meter_frames", default=8)
        self.frames = [pygame.Rect(0, i * (self.spritesheet_height // self.power_meter_quads), self.spritesheet_width, (self.spritesheet_height // self.power_meter_quads)) for i in range(self.power_meter_quads)]
        self.player = player
        self.frame_index = 0
        self.frame_swap_timer = 0
        self.swap_state = False

    def update(self):
        if self.player.pspeed:
            self.frame_swap_timer += 1
            if self.frame_swap_timer >= 6:
                self.swap_state = not self.swap_state
                self.frame_swap_timer = 0
            self.frame_index = 7 if self.swap_state else 6
        else:
            self.frame_index = min(int(self.player.run_timer) // int(round(MAX_RUN_TIMER / 7.5)), 7)
            self.frame_swap_timer = 0

    def draw(self):
        screen.blit(self.spritesheet.subsurface(get_key(self.frames, self.frame_index)), (48 + (text.font_size / 2) * len(str("inf" if get_nitpick("infinite_lives") else self.player.lives)), 24 + (self.player.player_number + 1) * 16))

class Score:
    def __init__(self, x, y, points=100):
        self.x, self.y = x, y
        self.image = load_sprite("score")
        self.image_width, self.image_height = self.image.get_size()
        self.frames = [pygame.Rect(0, i * (self.image_height // 9), self.image_width, (self.image_height // 9)) for i in range(9)]
        self.frame_index = get_key({100: 0, 200: 1, 400: 2, 800: 3, 1000: 4, 2000: 5, 4000: 6, 8000: 7, 10000: 8}, points, default=-1)
        self.dt = 0
        if not points == 10000:
            set_key(globals(), "score")(get_key(globals(), "score") + points)

    def update(self):
        self.dt += 1
        if self.dt >= 60:
            overlays.remove(self)

    def draw(self):
        screen.blit(self.image.subsurface(get_key(self.frames, self.frame_index)), (self.x, self.y - self.dt))

class CoinAnimation:
    def __init__(self, x, y, **kwargs):
        self.x, self.y = x * 16 + 4, y * 16 - 28
        self.image = load_sprite("coinanim")
        self.image_width, self.image_height = self.image.get_size()
        self.sprites = [pygame.Rect((self.image_width // 32) * column, 0, (self.image_width // 32), self.image_height) for column in range(32)]
        self.dt = 0
        hud.add_coins(1)

    def update(self):
        self.dt += 1
        if self.dt >= 31:
            particles.remove(self)
            overlays.append(Score(self.x - camera.x, self.y - camera.y + 32, 200))

    def draw(self):
        screen.blit(self.image.subsurface(get_key(self.sprites, self.dt)), (self.x - camera.x - (((self.image_width // 32) - 8) / 2), self.y - camera.y))

class CoinHUD:
    def __init__(self, coins=0):
        self.x, self.y = 16, 17
        self.image = load_sprite("coinhud")
        self.coins = coins

    def add_coins(self, coin):
        self.coins += coin
        sound_player.play_sound(coin_sound)
        if self.coins >= 100:
            sound_player.play_sound(oneup_sound)
            self.coins -= 100
            for player in players:
                player.lives += 1

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

class PlayerHUD:
    def __init__(self, player):
        self.player = player
        self.image = load_sprite("playerhud")
        self.sprite_size = self.image.get_size()
        self.sprites = [[pygame.Rect(x * (get_key(self.sprite_size, 0) // 2), y * (get_key(self.sprite_size, 1) // all_players), (get_key(self.sprite_size, 0) // 2), (get_key(self.sprite_size, 1) // all_players)) for x in range(2)] for y in range(all_players)]
        self.rainbow_timer = 0

    def update(self):
        self.player_number = self.player.player_number + 1
        self.size = max(self.player.size - 1, 0)
        self.star = self.player.star
        self.star_timer = self.player.star_timer
        self.star_effect_timer = self.player.star_effect_timer
        self.rainbow_timer = self.player.rainbow_timer

    def draw(self):
        try:
            frame_rect = get_key(self.sprites, self.player_number - 1, self.size)
            sprite = self.image.subsurface(frame_rect)
            
            if get_nitpick("moonwalking_mario"):
                sprite = pygame.transform.flip(sprite, True, False)

            sprite_width = get_key(self.sprite_size, 0)
            sprite_height = get_key(self.sprite_size, 1)
            pos_x = (sprite_width // 2) - 4
            pos_y = (sprite_height // all_players) + 4 + self.player_number * 16

            if self.star:
                star_sprite = sprite.copy()
                star_colors = get_game_property("star_colors")
                color_count = len(star_colors)

                cycle_time = 2 if self.star_timer >= 1 else 4
                index = (self.rainbow_timer // cycle_time) % color_count
                next_index = (index + 1) % color_count
                blend_ratio = (self.rainbow_timer % cycle_time) / cycle_time

                color = lerp_color(get_key(star_colors, index), get_key(star_colors, next_index), blend_ratio)
                star_sprite.fill(color, special_flags=pygame.BLEND_RGBA_MULT)

                screen.blit(star_sprite, (pos_x, pos_y))
                
                if self.star_effect_timer >= STAR_EFFECT_DURATION:
                    overlay_particles.append(StarEffect(pos_x, pos_y, color, 8, True))
            else:
                screen.blit(sprite, (pos_x, pos_y))

        except AttributeError:
            pass

class Tile:
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False, item=None, item_spawn_anim=True, item_sound=None, is_ground=False):
        self.x = x * 16
        self.y = y * 16 + 8
        self.og_x, self.og_y = x, y
        self.is_ground = is_ground
        self.spriteset = 0 if self.is_ground else spriteset
        self.original_image = image
        try:
            self.image = load_sprite(image)
        except:
            self.image = self.original_image
        try:
            self.img_width, self.img_height = self.image.get_size()
        except:
            self.img_width, self.img_height = 16, 16
        self.tile_size = 16
        self.rect = pygame.Rect(x * 16, y * 16 + 8, self.tile_size, self.tile_size)
        self.cols = 1
        self.rows = self.img_height // self.tile_size
        self.sprites = [pygame.Rect(0, row * self.tile_size, 16, self.tile_size) for row in range(self.rows)]

        self.left_collide = left_collide
        self.right_collide = right_collide
        self.top_collide = top_collide
        self.bottom_collide = bottom_collide
        self.bonk_bounce = bonk_bounce
        self.breakable = breakable
        self.item = item
        self.item_spawn_anim = item_spawn_anim

        if isinstance(self.item, str) and nor(self.item == CoinAnimation, str(self.item) == "MultiCoin"):
            self.item = get_key(globals(), self.item)

        self.broken = False
        
        self.bouncing = False
        self.bounce_timer = 0
        self.bounce_speed = 0
        self.y_offset = 0
        self.can_break_now = False
        self.hit = False
        self.item_spawned = False
        self.item_sound = None if self.item == CoinAnimation or str(self.item) == "MultiCoin" else (item_sound or sprout_sound)
        self.player = None
        self.coin_block_timer = 0
        self.coins = 0
        self.image_scale = 1
        self.sprite = None

    def update(self):
        if self.coins > 0 and not self.item_spawned:
            self.item_sound = None
            self.coin_block_timer += 1/60
        
        if self.bouncing:
            if self.item is not None:
                if self.item_spawned:
                    self.bonk_bounce = False
                    self.hit = True
                    self.breakable = False
                    self.image = load_sprite("blockhit")
                    self.cols = 1
                    self.frame_index = 0
                    self.item = None
                else:
                    if self.original_image == None:
                        self.left_collide = True
                        self.right_collide = True
                        self.top_collide = True
                        self.bottom_collide = True
                    if self.item == Mushroom:
                        if get_nitpick("non-progressive_powerups") or (self.player and not self.player.size == 0):
                            self.item = FireFlower
                    else:
                        if not str(self.item) == "MultiCoin":
                            self.item_spawned = True
                            if not self.item == CoinAnimation:
                                if ((getattr(self.item(infinity, infinity) if isinstance(self.item, type) else self.item, "progressive", False) and self.player and self.player.size == 0) and not get_nitpick("non-progressive_powerups")):
                                    self.item = Mushroom
                    if self.item == CoinAnimation:
                        particles.append(CoinAnimation(self.og_x, self.og_y - 1, spriteset=self.spriteset, sprout=False))
                    elif str(self.item) == "MultiCoin":
                        if self.y_offset == 0 and self.bounce_speed == -1:
                            tile.coins += 1
                            tile.item_spawned = tile.coin_block_timer >= 5 or tile.coins >= 10
                            particles.append(CoinAnimation(tile.og_x, tile.og_y - 1, spriteset=tile.spriteset, sprout=False))
                    else:
                        items.append(self.item(self.og_x, self.og_y - (0.625 if self.item_spawn_anim else 1), spriteset=self.spriteset, sprout=self.item_spawn_anim))
                        self.item_spawned = True
                    if self.item_sound is not None:
                        sound_player.play_sound(self.item_sound)

            self.y_offset += self.bounce_speed
            self.bounce_speed += 0.25

            if self.y_offset >= 0:
                self.y_offset = 0
                self.bouncing = False

        if self.can_break_now and not self.broken:
            self.broken = True
            self.y_offset = 0
            self.left_collide = False
            self.right_collide = False
            self.top_collide = False
            self.bottom_collide = False
            self.bonk_bounce = False
            self.breakable = False
            self.rect = pygame.Rect(0, 0, 0, 0)
            debris.append(BrickDebris(self.x, self.y, -1, -5, self.spriteset))
            debris.append(BrickDebris(self.x, self.y, 1, -5, self.spriteset))
            debris.append(BrickDebris(self.x, self.y, -1, 0, self.spriteset))
            debris.append(BrickDebris(self.x, self.y, 1, 0, self.spriteset))
            sound_player.play_sound(break_sound)
            set_key(globals(), "score")(get_key(globals(), "score") + 50)

        self.image_scale = 1 - (self.y_offset / 8)
        try:
            self.sprite = (self.image if self.is_ground else self.image.subsurface(get_key(self.sprites, self.spriteset))) if self.image_scale == 1 else scale_image(self.image if self.is_ground else self.image.subsurface(get_key(self.sprites, self.spriteset)), self.image_scale)
        except:
            self.sprite = None

    def bump(self, player=None):
        self.bouncing = True
        self.bounce_speed = -1
        self.y_offset = 0
        self.player = player

    def break_block(self):
        if self.item is None:
            self.can_break_now = self.breakable
            self.bouncing = True

    def draw(self):
        if nor(self.sprite is None, self.broken):
            screen.blit(self.sprite, (self.x - camera.x - (self.sprite.get_width() / (1 if self.image_scale == 1 else 2)) + 16, self.y - camera.y + (self.y_offset * ((2 / 3) if get_nitpick("inverted_block_bounce") else 4))))

class Ground(Tile):
    def __init__(self, x, y, tile_index=1, tileset="ground", rows=8, cols=6):
        super().__init__(x, y, get_key(split_image(load_sprite(f"tiles_{tileset}"), rows, cols), tile_index - 1), 0, is_ground=True)

class HardBlock(Tile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "hardblock", spriteset)

class AnimatedTile(Tile):
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False, item=None, item_spawn_anim=True, item_sound=None, anim_speed=1):
        super().__init__(x, y, image, spriteset, left_collide, right_collide, top_collide, bottom_collide, bonk_bounce, breakable, item, item_spawn_anim, item_sound)

        self.cols = self.img_width // self.tile_size
        self.total_frames = self.cols
        self.frame_index = 0
        self.anim_speed = anim_speed

        self.sprites = [[pygame.Rect(col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size) for col in range(self.cols)] for row in range(self.rows)]

    def update(self):
        super().update()
        self.frame_index = int((dt / (60 / self.cols) / self.anim_speed) % self.total_frames)
        try:
            self.sprite = (self.image.subsurface(get_key(self.sprites, self.spriteset if not self.hit else 0, self.frame_index if nor(self.broken, self.hit) else 0))) if self.image_scale == 1 else scale_image(self.image.subsurface(get_key(self.sprites, self.spriteset if not self.hit else 0, self.frame_index if nor(self.broken, self.hit) else 0)), self.image_scale)
        except:
            self.sprite = None

class Brick(AnimatedTile):
    def __init__(self, x, y, item=None, item_spawn_anim=True, spriteset=1, item_sound=None):
        super().__init__(x, y, "brick", spriteset, bonk_bounce=True, breakable=True, item=item, item_spawn_anim=item_spawn_anim, item_sound=item_sound, anim_speed=get_game_property("animation_speed", "brick"))

    def update(self):
        super().update()

class QuestionBlock(AnimatedTile):
    def __init__(self, x, y, item=CoinAnimation, item_spawn_anim=True, spriteset=1, item_sound=None):
        super().__init__(x, y, "questionblock", spriteset, bonk_bounce=True, item=item, item_spawn_anim=False if item == CoinAnimation else item_spawn_anim, item_sound=item_sound, anim_speed=get_game_property("animation_speed", "? block"))

    def update(self):
        super().update()

class HiddenBlock(AnimatedTile):
    def __init__(self, x, y, item=CoinAnimation, item_spawn_anim=True, spriteset=1, item_sound=None):
        super().__init__(x, y, None, spriteset, bonk_bounce=True, item=item, item_spawn_anim=False if item == CoinAnimation else item_spawn_anim, item_sound=item_sound, left_collide=False, right_collide=False, top_collide=False)

    def update(self):
        super().update()

class Coin(AnimatedTile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "coin", spriteset=spriteset, anim_speed=get_game_property("animation_speed", "coin"))

    def update(self):
        super().update()

        for tile in tiles:
            if tile.rect.colliderect(self.rect.move(0, 16)) and tile.bouncing and tile.top_collide and not tile.hit:
                tiles.remove(self)
                particles.append(CoinAnimation(self.x / 16, (self.y - 8) / 16))

class BrickDebris:
    def __init__(self, x, y, speedx, speedy, spriteset=1):
        self.x, self.y = x + 4, y + 4
        self.spriteset = spriteset
        self.speedx, self.speedy = speedx, speedy
        self.image = load_sprite("brickdebris")
        self.rotated_image = None
        self.img_width, self.img_height = self.image.get_size()
        self.sprites = [[pygame.Rect(row * 8, column * 8, 8, 8) for row in range(2)] for column in range(4)]
        self.angle = 0
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.quad = self.image.subsurface(get_key(self.sprites, self.spriteset, 0))

    def update(self):
        self.x += self.speedx
        self.y += self.speedy
        self.speedy += self.gravity
        self.sprite = int(self.speedx > 0)
        self.angle -= self.speedx * 4
        self.quad = self.image.subsurface(get_key(self.sprites, self.spriteset, self.sprite))
        self.rotated_image = pygame.transform.rotate(self.image.subsurface(get_key(self.sprites, self.spriteset, self.sprite)), self.angle)
        if self.y >= (y_range or SCREEN_HEIGHT) + 16:
            debris.remove(self)
    
    def draw(self):
        if self.rotated_image:
            screen.blit(self.rotated_image, (self.x - camera.x, self.y - camera.y))

class Mushroom:
    def __init__(self, x, y, sprout=False, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8 + (8 if sprout else 0)
        self.sprite = load_sprite("mushroom")
        self.speedx = 0 if sprout else 1
        self.speedy = -0.5 if sprout else 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.size = 1
        self.dt = 0
        self.frame_index = 0
        self.sprouting = sprout
        self.sprout_timer = 0
        self.spriteset = spriteset
        self.sprite_size = self.sprite.get_size()
        self.frames = get_key(self.sprite_size, 0) // 16
        self.quad_size = get_key(self.sprite_size, 0) // self.frames
        self.spriteset_size = get_key(self.sprite_size, 1) // 4
        self.sprites = [[pygame.Rect(self.quad_size * i, self.spriteset_size * j, self.quad_size, self.spriteset_size) for i in range(self.frames)] for j in range(4)]

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt * get_game_property("animation_speed", "mushroom")) % self.frames)
        if self.sprouting:
            self.sprout_timer += 1
            self.y += self.speedy / 2

            if self.sprout_timer >= SPROUT_SPEED * 60:
                self.sprouting = False
                self.speedx = 1
                self.speedy = 0
        else:
            self.x += self.speedx
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedx > 0 and tile.left_collide:
                        self.x = tile.rect.left - self.rect.width
                    elif self.speedx < 0 and tile.right_collide:
                        self.x = tile.rect.right
                    self.speedx *= -1
                    break

            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0 and tile.top_collide:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = -pi if (tile.bouncing and not tile.hit) or tile.can_break_now else 0
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            self.rect.topleft = (self.x, self.y)

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height)))
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        screen.blit(self.sprite.subsurface(get_key(self.sprites, self.spriteset, self.frame_index)), (self.x - camera.x, self.y - camera.y))

class OneUp(Mushroom):
    def __init__(self, x, y, sprout=False, spriteset=1):
        super().__init__(x, y, sprout, spriteset)
        self.lives = 1
        self.sprite = load_sprite("oneup")
        self.sprite_size = self.sprite.get_size()
        self.frames = get_key(self.sprite_size, 0) // 16
        self.quad_size = get_key(self.sprite_size, 0) // self.frames
        self.spriteset_size = get_key(self.sprite_size, 1) // 4
        self.sprites = [[pygame.Rect(self.quad_size * i, self.spriteset_size * j, self.quad_size, self.spriteset_size) for i in range(self.frames)] for j in range(4)]

    def update(self):
        super().update()

    def is_visible(self):
        return super().is_visible()
    
    def below_camera(self):
        return super().below_camera()

    def draw(self):
        super().draw()

class FireFlower:
    def __init__(self, x, y, sprout=False, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8 + (8 if sprout else 0)
        self.progressive = True
        self.spriteset = spriteset
        self.sprite = load_sprite("fireflower")
        self.sprite_size = self.sprite.get_size()
        self.frames = get_key(self.sprite_size, 0) // 16
        self.quad_size = get_key(self.sprite_size, 0) // self.frames
        self.spriteset_size = get_key(self.sprite_size, 1) // 4
        self.sprites = [[pygame.Rect(self.quad_size * i, self.spriteset_size * j, self.quad_size, self.spriteset_size) for i in range(self.frames)] for j in range(4)]
        self.speedx = 0
        self.speedy = -0.5 if sprout else 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.size = 2
        self.frame_index = 0
        self.sprouting = sprout
        self.sprout_timer = 0
        self.dt = 0

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt * get_game_property("animation_speed", "fire flower")) % self.frames)
        if self.sprouting:
            self.sprout_timer += 1
            self.y += self.speedy / 2

            if self.sprout_timer >= SPROUT_SPEED * 60:
                self.sprouting = False
                self.speedy = 0
        else:
            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0 and tile.top_collide:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = -pi if (tile.bouncing and not tile.hit) or tile.can_break_now else 0
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height)))
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        screen.blit(self.sprite.subsurface(get_key(self.sprites, self.spriteset, self.frame_index)), (self.x - camera.x, self.y - camera.y))

class Star:
    def __init__(self, x, y, sprout=False, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8 + (8 if sprout else 0)
        self.bounce = 2.5
        self.sprite = load_sprite("star")
        self.speedx = 0 if sprout else 1
        self.speedy = -0.5 if sprout else -self.bounce
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.125 / (2 if low_gravity else 1)
        self.size = 1
        self.sprouting = sprout
        self.sprout_timer = 0
        self.sprite_size = self.sprite.get_size()
        self.frames = get_key(self.sprite_size, 0) // 16
        self.quad_size = get_key(self.sprite_size, 0) // self.frames
        self.spriteset_size = get_key(self.sprite_size, 1) // 4
        self.sprites = [[pygame.Rect(self.quad_size * i, self.spriteset_size * j, self.quad_size, self.spriteset_size) for i in range(4)] for j in range(self.frames)]
        self.spriteset = spriteset
        self.frame_index = 0
        self.dt = 0
        self.angle = 0
        self.rainbow_timer = 0
        self.star_effect_timer = 0

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt * get_game_property("animation_speed", "star") % self.frames))
        if self.sprouting:
            self.sprout_timer += 1
            self.y += self.speedy / 2

            if self.sprout_timer >= SPROUT_SPEED * 60:
                self.sprouting = False
                self.speedx = 1
                self.speedy = -self.bounce
        else:
            self.star_effect_timer += 1 if get_game_property("star_roll") else 0
            self.angle -= (self.speedx * 4) if get_game_property("star_roll") else 0
            self.rainbow_timer += 1
            self.x += self.speedx
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedx > 0 and tile.left_collide:
                        self.x = tile.rect.left - self.rect.width
                    elif self.speedx < 0 and tile.right_collide:
                        self.x = tile.rect.right
                    self.speedx *= -1
                    break

            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0 and tile.top_collide:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = -self.bounce
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            self.rect.topleft = (self.x, self.y)

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height)))
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        sprite = pygame.transform.rotate(self.sprite.subsurface(get_key(self.sprites, self.spriteset, self.frame_index)), self.angle)

        if get_game_property("star_rainbow_effect") and not self.sprouting:
            star_sprite = sprite.copy()
            star_colors = get_game_property("star_colors")
            color_count = len(star_colors)

            cycle_time = 2
            index = (self.rainbow_timer // cycle_time) % color_count
            next_index = (index + 1) % color_count
            blend_ratio = (self.rainbow_timer % cycle_time) / cycle_time

            color = lerp_color(get_key(star_colors, index), get_key(star_colors, next_index), blend_ratio)
            star_sprite.fill(color, special_flags=pygame.BLEND_RGBA_MULT)

            screen.blit(star_sprite, (self.x - camera.x, self.y - camera.y))

            if self.star_effect_timer >= STAR_EFFECT_DURATION:
                self.star_effect_timer -= STAR_EFFECT_DURATION
                particles.append(StarEffect(self.x, self.y, color, 8))
        else:
            screen.blit(sprite, (self.x - camera.x, self.y - camera.y))

class Fireball:
    def __init__(self, player):
        self.x = player.rect.left - 1
        self.y = player.rect.top
        self.bounce = pi
        self.speedx = 5 if player.facing_right else -5
        self.speedy = self.bounce * (-1 if player.up else 1)
        self.rect = pygame.Rect(self.x, self.y, 8, 8)
        self.sprite = load_sprite("fireball")
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprites = [pygame.Rect(i * (self.sprite_width // 4), 0, (self.sprite_width // 4), self.sprite_height) for i in range(4)]
        self.angle = 0
        self.frame_index = 0
        self.frame_timer = 0
        self.destroyed = False
        self.gravity = 0.5 / (2 if low_gravity else 1)
        self.player = player
        self.dt = 0

    def update(self):
        self.dt += 1
        if self.destroyed:
            self.frame_timer += 1
            self.frame_index = floor(min(self.frame_timer / 4, 3))
            if self.frame_timer >= 15:
                get_key(fireballs_table, str(self.player.player_number)).remove(self)
        else:
            self.angle -= 12 * (-1 if self.speedx < 0 else 1)

            self.x += self.speedx
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedx > 0 and tile.left_collide:
                        self.x = tile.rect.left - self.rect.width
                        self.destroy()
                    elif self.speedx < 0 and tile.right_collide:
                        self.x = tile.rect.right
                        self.destroy()
                    return

            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0 and tile.top_collide:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = -self.bounce
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                        self.destroy()
                        return
                    break

            self.rect.topleft = (self.x, self.y)

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    self.destroy()
                    enemy.shot(self)
                    overlays.append(Score(self.x - camera.x, self.y - camera.y))
                    sound_player.play_sound(shot_sound)

            self.rect.topleft = (self.x, self.y)

    def destroy(self):
        self.destroyed = True
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.frame_timer = 5
        self.angle = 0
        self.x -= (0 if self.player.facing_right else 8)
        self.speedx = 0
        self.speedy = 0
        sound_player.play_sound(bump_sound)

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height)))

    def draw(self):
        if self.dt > 1:
            screen.blit(pygame.transform.rotate(self.sprite.subsurface(get_key(self.sprites, self.frame_index)), self.angle), (self.x - camera.x, self.y - camera.y - 3))

class Goomba:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.spriteset = spriteset
        self.properties = get_game_property("enemies", "goomba")
        self.sprite = load_sprite("goomba")
        self.total_frames = sum(get_key(self.properties, "frames").values())
        self.spr_width, self.spr_height = self.sprite.get_size()
        self.quad_width = self.spr_width // self.total_frames
        self.sprites = [[pygame.Rect(i * self.quad_width, j * self.spr_height // 4, self.quad_width, self.spr_height // 4) for i in range(self.total_frames)] for j in range(4)]
        self.speedx = -pi / 4
        self.speedy = 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.frame_index = 0
        self.stomped = False
        self.shotted = False
        self.angle = 0
        self.dt = 0

    def update(self):
        if self.shotted:
            self.angle = 180 if get_game_property("enemies", "classic_death_anim") else (self.angle - (self.speedx * 4))
            self.x += self.speedx
            self.y += self.speedy
            self.speedy += self.gravity
            try:
                self.frame_index = get_key(self.properties, "frames", "normal") + int((self.dt * get_key(self.properties, "frame_speeds", "shot")) % get_key(self.properties, "frames", "shot"))
            except:
                pass
            if self.rect.top >= SCREEN_HEIGHT:
                enemies.remove(self)
        else:
            if self.stomped:
                self.frame_index = get_key(self.properties, "frames", "normal") + (get_key(self.properties, "frames", "shot") if key_exists(get_key(self.properties, "frames"), "shot") else 0) + (int((self.dt * get_key(self.properties, "frame_speeds", "stomp")) % get_key(self.properties, "frames", "stomp")) if get_key(self.properties, "loop_stomp_animation") else min(int((self.dt * get_key(self.properties, "frame_speeds", "stomp"))), get_key(self.properties, "frames", "stomp") - 1))
                self.dt += 1
                if self.dt >= 30:
                    enemies.remove(self)
            else:
                self.dt += 0.5
                self.x += self.speedx
                self.rect.topleft = (self.x, self.y)

                for tile in tiles:
                    if tile.broken:
                        continue
                    if self.rect.colliderect(tile.rect):
                        if self.speedx > 0 and tile.left_collide:
                            self.x = tile.rect.left - self.rect.width
                        elif self.speedx < 0 and tile.right_collide:
                            self.x = tile.rect.right
                        self.speedx *= -1
                        break

                self.y += self.speedy
                self.speedy += self.gravity
                self.rect.topleft = (self.x, self.y)

                self.rect.topleft = (self.x, self.y)

                for tile in tiles:
                    if tile.broken:
                        continue
                    if self.rect.colliderect(tile.rect):
                        if self.speedy > 0 and tile.top_collide:
                            self.y = tile.rect.top - self.rect.height
                            self.speedy = 0
                            if (tile.bouncing and not tile.hit) or tile.can_break_now:
                                self.shot()
                                overlays.append(Score(self.x - camera.x, self.y - camera.y))
                                sound_player.play_sound(shot_sound)
                        elif self.speedy < 0 and tile.bottom_collide:
                            self.y = tile.rect.bottom
                            self.speedy = 0
                        break

                for enemy in enemies:
                    if self.rect.colliderect(enemy.rect) and self is not enemy:
                        if self.speedx > 0:
                            self.x = enemy.rect.left - self.rect.width
                        elif self.speedx < 0:
                            self.x = enemy.rect.right
                        self.speedx *= -1
                        break

                self.rect.topleft = (self.x, self.y)
                self.frame_index = int((self.dt * get_key(self.properties, "frame_speeds", "normal")) % get_key(self.properties, "frames", "normal"))

    def stomp(self):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.stomped = True
        self.shotted = False
        self.dt = 0

    def shot(self, culprit=None):
        self.dt = 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.shotted = True
        self.stomped = False
        self.speedx = 2 * -is_negative(self.speedx)
        self.speedy = -pi

        if culprit:
            try:
                if culprit.x < self.x:
                    self.speedx = 2
                elif culprit.x > self.x:
                    self.speedx = -2
            except AttributeError:
                if culprit.rect.x < self.x:
                    self.speedx = 2
                elif culprit.rect.x > self.x:
                    self.speedx = -2

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height)))
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        image = pygame.transform.rotate(self.sprite.subsurface(get_key(self.sprites, self.spriteset, self.frame_index)), self.angle)
        image = pygame.transform.flip(image, xor((self.speedx > 0 and not self.shotted), get_nitpick("moonwalking_enemies")), False)
        screen.blit(image, (self.x - camera.x, self.y - camera.y + 1 - ((self.spr_height // 4) - 16)))

class Koopa:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.properties = get_game_property("enemies", "koopa")
        self.offset_y = get_key(self.properties, "offsety")
        self.spriteset = spriteset
        self.sprite = load_sprite("koopa")
        self.total_frames = sum(get_key(self.properties, "frames").values())
        self.spr_width, self.spr_height = self.sprite.get_size()
        self.quad_width = self.spr_width // self.total_frames
        self.sprites = [[pygame.Rect(i * self.quad_width, j * self.spr_height // 4, self.quad_width, self.spr_height // 4) for i in range(self.total_frames)] for j in range(4)]
        self.speedx = -pi / 4
        self.speedy = 0
        self.shell_speed = 3.75
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.frame_index = 0
        self.stomped = False
        self.shotted = False
        self.angle = 0
        self.dt = 0
        self.combo = 0

    def update(self):
        if self.shotted:
            self.dt += 1
            self.angle = 180 if get_game_property("enemies", "classic_death_anim") else (self.angle - (self.speedx * 4))
            self.x += self.speedx
            self.y += self.speedy
            self.speedy += self.gravity
            self.frame_index = int((self.dt * get_key(self.properties, "frame_speeds", "shell")) % get_key(self.properties, "frames", "shell")) if get_key(self.properties, "shell_death_anim") else 0
            if self.rect.top >= SCREEN_HEIGHT:
                enemies.remove(self)
        else:
            self.dt += 0.5
            self.x += self.speedx
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedx > 0 and tile.left_collide:
                        self.x = tile.rect.left - self.rect.width
                    elif self.speedx < 0 and tile.right_collide:
                        self.x = tile.rect.right
                    self.speedx *= -1
                    if self.stomped:
                        sound_player.play_sound(bump_sound)
                        if tile.item is not None:
                            tile.y_offset = 0
                            tile.bump()
                        if tile.breakable and tile.item is None:
                            tile.break_block()
                    break

            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0 and tile.top_collide:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = 0
                        if (tile.bouncing and not tile.hit) or tile.can_break_now:
                            self.whack_upside_down()
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect) and self is not enemy:
                    if self.stomped and not self.speedx == 0:
                        enemy.shot(self)
                        overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, get_key([100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000], self.combo)))
                        if self.combo == 8:
                            for player in players:
                                player.lives += 1
                        self.combo = min(self.combo + 1, 8)
                        sound_player.play_sound([shot_sound, ((self.combo - 1) * 2) if get_game_property("pitch_shot_sound") else 0])
                    elif not self.stomped:
                        if self.speedx > 0:
                            self.x = enemy.rect.left - self.rect.width
                        elif self.speedx < 0:
                            self.x = enemy.rect.right
                        self.speedx *= -1
                    break

            self.rect.topleft = (self.x, self.y)

            self.frame_index = int((self.dt * (abs(self.speedx) if self.stomped else 1) * get_key(self.properties, "frame_speeds", "shell" if self.stomped else "normal")) % get_key(self.properties, "frames", "shell" if self.stomped else "normal"))

    def whack_upside_down(self):
        self.speedx = 0
        self.speedy = -2.5
        self.stomped = True
        self.angle = 180
        sound_player.play_sound(shot_sound)
        overlays.append(Score(self.x - camera.x, self.y - camera.y))

    def stomp(self):
        self.stomped = True
        self.shotted = False
        self.frame_index = 0
        self.speedx = 0
        self.dt = 0
        self.combo = 0

    def shot(self, culprit=None):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.shotted = True
        self.stomped = False
        self.speedx = 2 * -is_negative(self.speedx)
        self.speedy = -pi
        self.dt = 0

        if culprit:
            try:
                if culprit.x < self.x:
                    self.speedx = 2
                elif culprit.x > self.x:
                    self.speedx = -2
            except AttributeError:
                if culprit.rect.x < self.x:
                    self.speedx = 2
                elif culprit.rect.x > self.x:
                    self.speedx = -2

    def is_visible(self):
        return (((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and ((self.y > camera.y - self.rect.height) or (self.y + self.rect.height > camera.y - self.rect.height)))
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        image = pygame.transform.rotate(self.sprite.subsurface(get_key(self.sprites, self.spriteset, self.frame_index + (get_key(self.properties, "frames", "normal") if self.stomped or self.shotted else 0))), self.angle)
        image = pygame.transform.flip(image, xor((self.speedx > 0 and not self.shotted), get_nitpick("moonwalking_enemies")), False)
        
        image_rect = image.get_rect()
        image_rect.centerx = self.x - camera.x + (self.quad_width // 4)
        image_rect.centery = self.y - camera.y + (self.spr_height // 16) + 1 - self.offset_y

        screen.blit(image, image_rect.topleft)

class Castle:
    def __init__(self, x, y, spriteset=1):
        self.spriteset = spriteset
        self.image = load_sprite("castle")
        self.image_width, self.image_height = self.image.get_size()
        self.x, self.y = x * 16, y * 16 - ((self.image_height // 4) - 24)
        self.sprites = [pygame.Rect(0, (self.image_height // 4) * i, self.image_width, (self.image_height // 4)) for i in range(4)]

    def draw(self):
        screen.blit(self.image.subsurface(get_key(self.sprites, self.spriteset)), (self.x - camera.x, self.y - camera.y))

class Player:
    def __init__(self, x=0, y=0, lives=3, size=0, controls_enabled=True, walk_cutscene=False, player_number=1, exiting_pipe=False):
        self.properties = get_game_property("character_properties")
        self.walk_speed = get_key(self.properties, "walk_speed")
        self.run_speed = get_key(self.properties, "run_speed")
        self.death_anim = get_key(self.properties, "pre_death_anim_jump")
        self.sync_crouch = get_key(self.properties, "sync_crouch_fall_anim")
        self.midair_turn = get_key(self.properties, "midair_turn")
        self.quad_width = get_key(self.properties, "quad_width")
        self.quad_height = get_key(self.properties, "quad_height")
        self.star_duration = get_key(self.properties, "star_duration")
        self.character_data = get_key(self.properties, "character_data", player_number)
        self.frame_group = get_key(self.character_data, "frames")
        self.frame_loops = get_key(self.character_data, "frame_loops")
        self.frame_speeds = get_key(self.character_data, "frame_speeds")
        self.acceleration = get_key(self.character_data, "acceleration")
        self.swim_height = get_key(self.character_data, "swim_height")
        self.max_jump = get_key(self.character_data, "max_jump") + 0.5
        self.color = get_key(self.character_data, "color")
        self.frame_data = {}
        self.prev_key = 0
        for key in ["idle", "crouch", "crouchfall", "walk", "skid", "jump", "fall", "run", "runjump", "runfall", "dead", "pipe", "climb", "swim", "swimpush", "fire"]:
            set_key(self.frame_data, key)(get_key(self.frame_group, key, default=0) + self.prev_key)
            self.prev_key = get_key(self.frame_data, key)
        self.spritesheet = load_sprite(f"p{player_number + 1}")
        self.controls_enabled = controls_enabled
        self.can_control = controls_enabled
        self.player_number = player_number
        self.enemy_speedx = 0
        self.speedx = 0
        self.speedy = 0
        self.jump_speedx = 0
        self.frame_timer = 0
        self.changing_controls = False
        self.control_changing_timer = 0
        self.on_ground = False
        self.facing_right = True
        self.pipe_anim_timer = 0
        self.crouch_timer = 0
        self.crouch_fall_timer = 0
        self.skid_timer = 0
        self.swimming_timer = 0
        self.swimpushing_timer = 0
        self.idle_timer = 0
        self.jumping_timer = 0
        self.falling_timer = 0
        self.jump_timer = 0
        self.anim_state = 0
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.down_key = False
        self.run = False
        self.jump = False
        self.prev_run = False
        self.prev_jump = False
        self.run_lock = False
        self.jump_lock = False
        self.img_width, self.img_height = self.spritesheet.get_size()
        self.rect = pygame.Rect(x, y, self.img_width, self.img_height)
        self.sprites = [[pygame.Rect(x * self.quad_width, y * self.quad_height, self.quad_width, self.quad_height) for x in range(self.img_width // self.quad_width)] for y in range(self.img_height // self.quad_height)]
        self.size = size
        self.walk_cutscene = walk_cutscene
        self.controls = get_key([get_key(globals(), f"controls{i+1}" if i else "controls") for i in count_list_items(characters_data)], player_number)
        self.skidding = False
        self.gravity = 0.25 / (2 if low_gravity else 1)
        self.min_jump = 0.5
        self.run_timer = 0
        self.update_hitbox()
        self.fall_timer = 0
        self.fall_duration = 0.125
        self.falling = True
        self.pspeed = False
        self.player_number = player_number
        self.size_change = []
        self.size_change_timer = 0
        self.old_controls = False
        self.fire_timer = 10
        self.fire_duration = 10
        self.fire_lock = False
        self.fired = False
        self.speed = 0
        self.swim_push_anim = False
        self.lives = lives
        self.dead = False
        self.dead_timer = 0
        self.dead_music = False
        self.shrunk = False
        self.shrunk_timer = 0
        self.all_dead = False
        self.can_draw = True
        self.stomp_jump = False
        self.stomp_combo = 0
        self.stomped_enemies = []
        self.star = False
        self.star_timer = 0
        self.star_effect_timer = 0
        self.star_combo = 8 if konami_complete else 0
        self.star_music = False
        self.rainbow_timer = 0
        self.piping = False
        self.piping_exit = exiting_pipe
        self.pipe_dir = False
        self.pipe_timer = 0
        self.pipe_duration = 1
        self.pipe_speed = 0.75
        self.pipe_marker = None
        self.clear = False
        self.kicked_shell = False
        self.kicked_timer = 0
        self.kicked_duration = 0.25
        self.prev_bottom = 0
        self.full_accel = False
        self.full_run_accel = False
        self.min_speedx = 0.25
        self.active_timer = 0
        try:
            for tile in tiles:
                if tile.top_collide:
                    if player.rect.bottom == tile.rect.top:
                        if player.rect.right > tile.rect.left and player.rect.left < tile.rect.right:
                            self.fall_timer = self.fall_duration
                            self.on_ground = False
        except:
            pass

    def add_life(self):
        if get_nitpick("infinite_lives"):
            for player in players:
                player.lives += 1
        else:
            self.lives += 1
        if not sound_player.is_playing(oneup_sound):
            sound_player.play_sound(oneup_sound)

    def update_hitbox(self):
        self.prev_bottom = self.rect.bottom
        new_width, new_height = (16, 8 if self.size == 0 else 16) if self.down else (16, 16 if self.size == 0 else 24)
        self.rect.width, self.rect.height = new_width, new_height
        self.rect.bottom = self.prev_bottom

    def update(self):
        self.active_timer += 1
        if self.dead:
            if self.dead_timer == 0:
                if self.star:
                    bgm_player.play_music(main_music)
                self.skidding = False
                self.gravity = 0.1875 / (2 if low_gravity else 1)
                self.speedx = 0
                self.frame_timer = 0
                self.piping = False
                self.run_timer = 0
                self.pspeed = False
                self.star = False
                self.star_timer = 0
                self.star_combo = 0
                self.star_music = False
                if not get_nitpick("infinite_lives"):
                    self.lives -= 1
                self.all_dead = everyone_dead
                if everyone_dead:
                    bgm_player.stop_music()
                    sound_player.stop_all_sounds()
                sound_player.play_sound(dead_sound)
            self.dead_timer += 1
            if self.dead_timer >= 30:
                if not self.dead_music:
                    self.speedy = -5
                    if self.all_dead:
                        bgm_player.play_music(dead_music)
                self.speedy += self.gravity
                self.rect.y += self.speedy
                self.dead_music = True
                if self.dead_timer >= 150 and self.lives > 0 and not everyone_dead:
                    furthest_player = max([player for player in players if not player.dead], key=lambda player: player.rect.x)
                    self.__init__(self.rect.x, self.rect.y, self.lives, player_number=self.player_number)
                    self.rect.x = furthest_player.rect.x
                    self.rect.bottom = furthest_player.rect.bottom
                    self.fall_timer = 0 if furthest_player.fall_timer < furthest_player.fall_duration else self.fall_duration
                    self.jump_timer = 0 if furthest_player.fall_timer < furthest_player.fall_duration else 1
                    self.shrunk = True
                    self.respawning = True
        else:
            self.gravity = (0.125 if underwater else 0.25) / (2 if low_gravity else 1)
            self.left = (get_key(keys, get_key(self.controls, "left"))) if self.controls_enabled and self.can_control and not self.piping else False
            self.right = (get_key(keys, get_key(self.controls, "right"))) if self.controls_enabled and self.can_control and not self.piping else False
            self.up = (get_key(keys, get_key(self.controls, "up"))) if self.controls_enabled and self.can_control and not self.piping else False
            self.down_key = (get_key(keys, get_key(self.controls, "down"))) if self.controls_enabled and self.can_control and not self.piping else False
            self.down = self.down_key if self.fall_timer < self.fall_duration else self.down
            self.run = (get_key(keys, get_key(self.controls, "run"))) if self.controls_enabled and self.can_control and not self.piping else False
            self.jump = (get_key(keys, get_key(self.controls, "jump"))) if self.controls_enabled and self.can_control and not self.piping else False

            if self.kicked_shell:
                self.kicked_timer += 1
                if self.kicked_timer >= self.kicked_duration * 60:
                    self.kicked_shell = False
                    self.kicked_timer = 0

            if self.shrunk:
                if self.shrunk_timer < 60:
                    self.can_draw = (self.shrunk_timer // 10) % 2 == 0
                elif self.shrunk_timer < 120:
                    self.can_draw = (self.shrunk_timer // 5) % 2 == 0
            else:
                self.can_draw = True

            if self.shrunk and not self.size_change:
                self.shrunk_timer += 1

            if self.shrunk_timer >= 120:
                self.shrunk = False
                self.shrunk_timer = 0
                self.can_draw = True

            for pipe_marker in pipe_markers:
                if self.rect.colliderect(pipe_marker.rect) and nor(self.piping, self.dead, self.size_change, pipe_marker.exit):
                    if self.down_key and self.rect.bottom + 2 >= pipe_marker.rect.top >= self.rect.bottom - 2 and pipe_marker.rect.left - 6 <= self.rect.x <= pipe_marker.rect.right - 12 and pipe_marker.pipe_dir == "up":
                        self.speedx = 0
                        self.speedy = self.pipe_speed
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and not player.pipe_marker == pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.up and self.fall_timer >= self.fall_duration and self.rect.top + 2 >= pipe_marker.rect.bottom >= self.rect.top - 2 and pipe_marker.rect.left - 6 <= self.rect.x <= pipe_marker.rect.right - 12 and pipe_marker.pipe_dir == "down":
                        self.speedx = 0
                        self.speedy = -self.pipe_speed
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and not player.pipe_marker == pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.right and self.rect.right - 2 <= pipe_marker.rect.left <= self.rect.right + 2 and self.fall_timer < self.fall_duration and pipe_marker.pipe_dir == "right":
                        self.speedx = self.pipe_speed
                        self.speedy = 0
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and not player.pipe_marker == pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.left and self.rect.left - 2 <= pipe_marker.rect.right <= self.rect.left + 2 and self.fall_timer < self.fall_duration and pipe_marker.pipe_dir == "left":
                        self.speedx = -self.pipe_speed
                        self.speedy = 0
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and not player.pipe_marker == pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

            if self.piping:
                self.pipe_timer += 1
                if self.pipe_timer <= self.pipe_duration * 60:
                    self.rect.y += self.speedy
                    if self.pipe_timer <= self.pipe_duration * 30:
                        self.rect.x += self.speedx
                self.can_draw = self.pipe_timer <= self.pipe_duration * 60
                if abs(self.speedx) < self.min_speedx:
                    self.anim_state = get_key(self.frame_data, "dead") + ((int(self.pipe_anim_timer * get_key(self.frame_speeds, "pipe")) % get_key(self.frame_group, "pipe")) if get_key(self.frame_loops, "pipe") else min(int(self.pipe_timer * get_key(self.frame_speeds, "pipe")), get_key(self.frame_group, "pipe") + 1))
                else:
                    self.frame_timer += abs(self.speedx) / 1.25
                    self.anim_state = get_key(self.frame_data, "crouchfall") + ((int(self.frame_timer * get_key(self.frame_speeds, "walk")) % get_key(self.frame_group, "walk")) if get_key(self.frame_loops, "walk") else min(int(self.frame_timer * get_key(self.frame_speeds, "walk")), get_key(self.frame_group, "walk") - 1))
                return

            if self.piping_exit:
                self.pipe_timer += 1
                if self.pipe_timer <= self.pipe_duration * 60:
                    self.rect.y += self.speedy
                    if self.pipe_timer <= self.pipe_duration * 30:
                        self.rect.x += self.speedx
                else:
                    self.pipe_timer = 0
                    self.piping_exit = False
                if abs(self.speedx) < self.min_speedx:
                    self.anim_state = get_key(self.frame_data, "dead") + ((int(self.pipe_anim_timer * get_key(self.frame_speeds, "pipe")) % get_key(self.frame_group, "pipe")) if get_key(self.frame_loops, "pipe") else min(int(self.pipe_timer * get_key(self.frame_speeds, "pipe")), get_key(self.frame_group, "pipe") + 1))
                else:
                    self.frame_timer += abs(self.speedx) / 1.25
                    self.anim_state = get_key(self.frame_data, "crouchfall") + ((int(self.frame_timer * get_key(self.frame_speeds, "walk")) % get_key(self.frame_group, "walk")) if get_key(self.frame_loops, "walk") else min(int(self.frame_timer * get_key(self.frame_speeds, "walk")), get_key(self.frame_group, "walk") - 1))
                return

            if self.walk_speed * 0.875 <= floor(abs(self.speedx) * 10) / 10 <= self.walk_speed and not self.full_accel:
                self.run = True
                self.speed = self.walk_speed
                self.speedx = self.walk_speed * is_negative(self.speedx)
                self.full_accel = True

            if self.run_speed * 0.875 <= floor(abs(self.speedx) * 10) / 10 <= self.run_speed and self.run and not self.full_run_accel:
                self.speed = self.run_speed
                self.speedx = self.run_speed * is_negative(self.speedx)
                self.full_run_accel = True

            if not self.run:
                self.full_run_accel = False

            self.speed = round(lerp(self.speed, self.run_speed * (1.25 if self.pspeed else 1) if self.run and not underwater else self.walk_speed, 0.125) * 10) / 10

            self.run_lock = self.run and not self.prev_run
            self.jump_lock = self.jump and not self.prev_jump

            if self.size == 2 and not self.down:
                if self.run:
                    if self.fire_timer < self.fire_duration:
                        if self.fire_timer == 0 and len(get_key(fireballs_table, str(self.player_number))) < max_fireballs:
                            sound_player.play_sound(fireball_sound)
                            get_key(fireballs_table, str(self.player_number)).append(Fireball(self))
                            self.fired = True
                        self.fire_timer += 1
                        if self.fire_timer == self.fire_duration:
                            self.fire_lock = True
                elif not self.run:
                    if 0 < self.fire_timer < self.fire_duration:
                        self.fire_timer += 1
                    else:
                        self.fire_timer = 0
                        self.fire_lock = False
                        self.fired = False
                elif self.fire_timer == self.fire_duration:
                    self.fire_timer = 0
                    self.fire_lock = False
                    self.fired = False
            else:
                self.fire_timer = self.fire_duration

            self.update_hitbox()

            if self.fall_timer < self.fall_duration:
                if self.down:
                    self.speedx *= (1 - self.acceleration)
                else:
                    if self.left and not self.right:
                        self.speedx = max(self.speedx - self.acceleration, -self.speed / (1.25 if underwater else 1))
                        self.facing_right = False
                    elif self.right and not self.left:
                        self.speedx = min(self.speedx + self.acceleration, self.speed / (1.25 if underwater else 1))
                        self.facing_right = True
                    else:
                        if not self.walk_cutscene:
                            self.speedx *= (1 - self.acceleration)
                            if abs(self.speedx) < self.min_speedx:
                                self.speedx = 0
            else:
                if self.left and not self.right:
                    self.speedx = max(self.speedx - self.acceleration, -self.speed / (1.25 if underwater else 1))
                    if self.midair_turn or underwater:
                        self.facing_right = False
                elif self.right and not self.left:
                    self.speedx = min(self.speedx + self.acceleration, self.speed / (1.25 if underwater else 1))
                    if self.midair_turn or underwater:
                        self.facing_right = True

            self.speedx = range_number(self.speedx, -self.speed, self.speed)
            
            self.new_rect = self.rect.copy()
            self.new_rect.x += self.speedx

            for tile in tiles:
                if tile.broken:
                    continue
                if self.new_rect.colliderect(tile.rect) and not abs(self.rect.bottom - tile.rect.top) == 1:
                    if self.speedx > self.min_speedx and tile.left_collide and abs(self.rect.right - tile.rect.left) < 4:
                        self.rect.right = tile.rect.left
                        self.speedx = 0
                    elif self.speedx < self.min_speedx and tile.right_collide and abs(self.rect.left - tile.rect.right) < 4:
                        self.rect.left = tile.rect.right
                        self.speedx = 0
                    elif abs(self.rect.right - tile.rect.left) < 32 if tile.left_collide else abs(self.rect.left - tile.rect.right) < 32 if tile.right_collide else False:
                        self.speedx = 0
                    break

            self.rect.x += self.speedx
            self.rect.y += self.speedy
            self.on_ground = False

            self.speedy = min(self.speedy, 2.5 if underwater or low_gravity else 5)

            if underwater:
                if self.jump and self.jump_timer == 0:
                    self.down = False
                    self.speedy = -self.swim_height * (1.5 if self.up and not self.down_key else 0.75 if self.down_key and not self.up else 1)
                    self.jump_timer = 1
                    self.fall_timer = self.fall_duration
                    self.swim_push_anim = True
                    sound_player.play_sound(swim_sound)
                elif not self.jump:
                    self.jump_timer = 0
            else:
                if (self.fall_timer < self.fall_duration or underwater) and self.jump_lock and self.jump_timer == 0:
                    self.speedy = -self.min_jump
                    self.jump_timer = 1
                elif self.jump and 0 < self.jump_timer < JUMP_HOLD_TIME:
                    if self.jump_timer == 1:
                        self.fall_timer = self.fall_duration
                        self.jump_speedx = 1 if self.stomp_jump else abs(self.speedx)
                        if underwater:
                            self.down = False
                        if not self.stomp_jump:
                            sound_player.play_sound(jump_sound if self.size == 0 or get_game_property("character_properties", "same_jump_sound") else jumpbig_sound)
                    self.max_speedx_jump = (self.max_jump + (2 if self.pspeed else 1) / 2) if self.jump_speedx >= 1 else self.max_jump
                    self.speedy = max(self.speedy - self.max_speedx_jump, -self.max_speedx_jump)
                    if not underwater:
                        self.jump_timer += 1
                elif not self.jump:
                    self.jump_timer = 1 if self.fall_timer < self.fall_duration else 0

            self.pspeed = self.run_timer >= MAX_RUN_TIMER

            if self.fall_timer < self.fall_duration:
                self.stomp_jump = False
                self.stomp_combo = False

            if self.can_control and not get_game_property("character_properties", "hide_power_meter"):
                if self.fall_timer < self.fall_duration and self.controls_enabled:
                    self.run_timer = range_number(self.run_timer + ((2 if self.star or konami_complete else 1) if ceil(abs(self.speedx) * 1000) / 1000 >= self.run_speed else -(2 if self.star or konami_complete else 0.5)), MIN_RUN_TIMER, MAX_RUN_TIMER)
                elif not self.run_timer == MAX_RUN_TIMER:
                    self.run_timer = range_number(self.run_timer - (2 if self.star or konami_complete else 0.5), MIN_RUN_TIMER, MAX_RUN_TIMER)

            if self.rect.left <= camera.x:
                self.rect.left = camera.x
                if self.rect.x <= camera.x and ((self.speedx < 0 and not self.facing_right) or (self.speedx < 0 and self.facing_right)):
                    self.speedx = 0

            if self.rect.right >= camera.x + SCREEN_WIDTH:
                self.rect.right = camera.x + SCREEN_WIDTH
                if self.rect.x >= camera.x + SCREEN_WIDTH - self.rect.width and ((self.speedx > 0 and self.facing_right) or (self.speedx > 0 and not self.facing_right)):
                    self.speedx = 0

            if self.size_change:
                if self.can_control:
                    self.old_controls = [self.left, self.right, self.up, self.down, self.run, self.jump, self.speedx, self.speedy, self.jump_timer, self.run_timer, self.fall_timer, self.falling, self.fire_timer, self.can_draw]
                self.can_control = False
                self.left = False
                self.right = False
                self.up = False
                self.down = False
                self.run = False
                self.jump = False
                self.speedx = 0
                self.speedy = 0
                self.jump_timer = 0
                self.run_timer = 0
                self.fall_timer = 0
                self.can_draw = True
                self.falling = False
                self.fire_timer = 0
                if self.size_change_timer % 5 == 0:
                    self.size = self.size_change.pop(0)
                self.size_change_timer += 1
            else:
                if self.controls_enabled and not self.can_control:
                    self.left, self.right, self.up, self.down, self.run, self.jump, self.speedx, self.speedy, self.jump_timer, self.run_timer, self.fall_timer, self.falling, self.fire_timer, self.can_draw = self.old_controls
                self.can_control = True

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if isinstance(tile, Coin):
                        tiles.remove(tile)
                        hud.add_coins(1)
                    else:
                        if self.speedy > 0 and self.rect.bottom >= tile.rect.top and tile.top_collide:
                            self.rect.bottom = tile.rect.top
                            self.speedy = 0
                            self.on_ground = True
                            self.falling = False
                            self.fall_timer = 0
                        elif self.speedy < 0 and tile.rect.bottom - 8 <= self.rect.top <= tile.rect.bottom and tile.bottom_collide:
                            if abs(self.rect.left - tile.rect.right) <= 4 and not any(t.rect.colliderect(pygame.Rect(self.rect.left, self.rect.bottom - 1, 1, 1)) for t in tiles if not t.broken):
                                if tile.right_collide:
                                    self.rect.x = tile.rect.right
                            elif abs(self.rect.right - tile.rect.left) <= 4 and not any(t.rect.colliderect(pygame.Rect(self.rect.right - 1, self.rect.bottom - 1, 1, 1)) for t in tiles if not t.broken):
                                if tile.left_collide:
                                    self.rect.x = tile.rect.left - self.rect.width
                            else:
                                self.rect.top = tile.rect.bottom
                                self.jump_timer = 0
                                self.speedy = 0
                                sound_player.play_sound(bump_sound)

                                if tile.bonk_bounce:
                                    tile.y_offset = 0
                                    tile.bump(self)
                                if not self.size == 0:
                                    tile.break_block()
                                if self.jump:
                                    sound_player.stop_sound(jump_sound)
                                    sound_player.stop_sound(jumpbig_sound)

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect) and not self.size_change:
                    if self.star or konami_complete:
                        enemy.shot(self)
                        overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, get_key([100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000], self.star_combo)))
                        if self.star_combo == 8:
                            self.add_life()
                        self.star_combo = min(self.star_combo + 1, 8)
                        sound_player.play_sound([shot_sound, ((self.star_combo - 1) * 2) if get_game_property("pitch_shot_sound") else 0])
                    elif self.speedy > 0 and self.rect.bottom - enemy.rect.top < 8 and not enemy.stomped:
                        self.stomped_enemies.append(enemy)
                    elif isinstance(enemy, Koopa):
                        self.enemy_speedx = (enemy.shell_speed + (self.speedx / 4)) * -is_negative(self.rect.centerx - enemy.rect.centerx)
                        if enemy.speedx == 0 and ((self.on_ground and self.rect.right > enemy.rect.left and self.rect.left < enemy.rect.right) or (self.fall_timer >= self.fall_duration and self.rect.top - enemy.rect.bottom < 8)):
                            self.kicked_shell = True
                            enemy.speedx = self.enemy_speedx
                            overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y))
                            sound_player.play_sound(shot_sound)
                        elif self.on_ground and self.kicked_timer == 0 and nor(self.shrunk, enemy.speedx == 0, self.rect.bottom - enemy.rect.top < 8):
                            if self.size == 0:
                                self.dead = True
                            else:
                                self.shrunk = True
                                target_size = 0 if get_nitpick("classic_powerdown") else self.size - 1
                                self.size_change_timer = 0
                                self.size_change = [target_size, self.size, target_size, self.size, target_size, self.size, target_size]
                                sound_player.play_sound(shrink_sound)
                        elif self.speedy > 0 and self.rect.bottom - enemy.rect.top < 8 and nand(enemy.stomped, enemy.speedx == 0):
                            self.stomped_enemies.append(enemy)
                    elif nor((isinstance(enemy, Koopa) and self.kicked_timer == 0), self.shrunk, self.rect.bottom - enemy.rect.top < 8):
                        if self.size == 0:
                            self.dead = True
                        else:
                            self.shrunk = True
                            target_size = 0 if get_nitpick("classic_powerdown") else self.size - 1
                            self.size_change_timer = 0
                            self.size_change = [target_size, self.size, target_size, self.size, target_size, self.size, target_size]
                            sound_player.play_sound(shrink_sound)

            if self.stomped_enemies:
                for enemy in self.stomped_enemies:
                    enemy.stomp()
                    overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, get_key([100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000], self.stomp_combo)))
                    self.stomped_enemies.remove(enemy)
                if self.stomp_combo == 8:
                    self.add_life()
                sound_player.play_sound([stomp_sound, self.stomp_combo if get_game_property("pitch_stomp_sound") else 0])
                self.stomp_combo = min(self.stomp_combo + 1, 8)
                self.stomp_jump = True
                self.speedy = -self.max_jump / (2 if underwater else 1)
                self.jump_timer = 1
                self.on_ground = False
                self.fall_timer = self.fall_duration

            for item in items:
                if self.rect.colliderect(item.rect) and nor(item.sprouting, isinstance(item, CoinAnimation)):
                    if isinstance(item, OneUp):
                        overlays.append(Score(item.x - camera.x, item.y - camera.y, 10000))
                        self.add_life()
                        items.remove(item)
                        sound_player.play_sound(oneup_sound)
                    elif isinstance(item, Star):
                        overlays.append(Score(item.x - camera.x, item.y - camera.y, 1000))
                        self.star = True
                        self.star_timer = self.star_duration
                        items.remove(item)
                        sound_player.play_sound(powerup_sound)
                    else:
                        overlays.append(Score(item.x - camera.x, item.y - camera.y, 1000))
                        if nand((isinstance(item, Mushroom) and not self.size == 0), (isinstance(item, (Mushroom, FireFlower)) and self.size == 2)):
                            if not self.size == item.size:
                                old_size = self.size
                                self.size_change_timer = 0
                                self.size_change = [item.size, old_size, item.size, old_size, item.size, old_size, item.size]

                        items.remove(item)
                        sound_player.play_sound(powerup_sound)

            self.star_timer = (self.star_timer - 1/60) if self.star else 0
            if self.star:
                if self.star_timer <= 0:
                    self.star_timer = 0
                    self.star = False
                self.rainbow_timer += 1

            if self.rect.bottom >= (y_range or SCREEN_HEIGHT + camera.x):
                if self.rect.top >= (y_range or SCREEN_HEIGHT + camera.x):
                    self.dead = True
                    self.can_draw = False
                elif konami_complete and not self.down_key:
                    self.stomp_combo = min(self.stomp_combo + 1, 8)
                    self.stomp_jump = True
                    self.speedy = -self.max_jump / (2 if underwater else 1)
                    self.jump_timer = 1
                    self.on_ground = False
                    self.fall_timer = self.fall_duration
                    sound_player.play_sound(stomp_sound)

            self.skidding = (self.fall_timer < self.fall_duration and ((self.speedx < 0 and self.facing_right and self.right and not self.left) or (self.speedx > 0 and not self.facing_right and self.left and not self.right)) and nor(self.down, 0 <= self.anim_state <= get_key(self.frame_data, "idle"), abs(self.speedx) < self.min_speedx))

            if self.on_ground:
                self.speedy = 0
                self.fall_timer = 0
                self.falling = True
            else:
                if not self.size_change:
                    self.speedy += self.gravity * (2 if self.fall_timer >= self.fall_duration and nor(self.jump, underwater) else 1)
                self.fall_timer += 0.025
                if not self.falling:
                    self.falling = True
                    self.fall_timer = 0

            self.prev_run = self.run
            self.prev_jump = self.jump

        self.star_effect_timer = (self.star_effect_timer + 1) if self.star else 0

        self.falling_condition = self.speedy > 0 and self.fall_timer >= self.fall_duration
        self.crouch_falling = self.down and self.falling_condition and not get_key(self.frame_group, "crouchfall") == 0

        self.crouch_timer = (self.crouch_timer + 1) if self.down and (self.sync_crouch and not self.falling_condition) and get_key(self.frame_group, "crouchfall") == 0 else 0
        self.crouch_fall_timer = (self.crouch_fall_timer + 1) if self.down and self.falling_condition and not get_key(self.frame_group, "crouchfall") == 0 else 0
        self.pipe_anim_timer = (self.pipe_anim_timer + 1) if self.piping else 0
        self.skid_timer = (self.skid_timer + 1) if self.skidding else 0
        self.jumping_timer = (self.jumping_timer + 1) if self.speedy < 0 and self.fall_timer >= self.fall_duration else 0
        self.falling_timer = (self.falling_timer + 1) if self.falling_condition else 0
        self.idle_timer = (self.idle_timer + 1) if abs(self.speedx) < self.min_speedx else 0
        self.swimming_timer = (self.swimming_timer + 1) if self.fall_timer >= self.fall_duration and underwater else 0
        self.swimpushing_timer = (self.swimpushing_timer + 1) if self.fall_timer >= self.fall_duration and underwater and self.swim_push_anim and not get_key(self.frame_group, "swimpush") == 0 else 0

        if self.dead:
            self.frame_timer += 1 if self.dead_timer >= 30 and not self.death_anim else 0
            self.anim_state = get_key(self.frame_data, "runfall") + ((int(self.frame_timer * get_key(self.frame_speeds, "dead")) % get_key(self.frame_group, "dead")) if get_key(self.frame_loops, "dead") else min(int(self.frame_timer * get_key(self.frame_speeds, "dead")), get_key(self.frame_group, "dead") - 1))
        elif self.size == 2 and 0 < self.fire_timer < self.fire_duration and self.fired and nor(self.fire_lock, self.fall_timer >= self.fall_duration and underwater):
            self.anim_state = get_key(self.frame_data, "swimpush") + int((self.fire_timer * get_key(self.frame_group, "fire")) / self.fire_duration)
            self.frame_timer = 0
        elif self.down:
            self.anim_state = get_key(self.frame_data, "crouch" if self.crouch_falling else "idle") + ((int(((self.crouch_fall_timer if self.crouch_falling else self.crouch_timer) if self.sync_crouch else self.crouch_timer) * get_key(self.frame_speeds, "crouchfall" if self.crouch_falling else "crouch")) % get_key(self.frame_group, "crouchfall" if self.crouch_falling else "crouch")) if get_key(self.frame_loops, "crouchfall" if self.crouch_falling else "crouch") else min(int(((self.crouch_fall_timer if self.crouch_falling else self.crouch_timer) if self.sync_crouch else self.crouch_timer) * get_key(self.frame_speeds, "crouchfall" if self.crouch_falling else "crouch")), get_key(self.frame_group, "crouchfall" if self.crouch_falling else "crouch") - 1))
            self.frame_timer = 0
        elif self.skidding:
            self.anim_state = get_key(self.frame_data, "walk") + ((int(self.skid_timer * get_key(self.frame_speeds, "skid")) % get_key(self.frame_group, "skid")) if get_key(self.frame_loops, "skid") else min(int(self.skid_timer * get_key(self.frame_speeds, "skid")), get_key(self.frame_group, "skid") - 1))
            self.frame_timer = 0
        elif self.fall_timer >= self.fall_duration and underwater:
            self.anim_state = get_key(self.frame_data, "swim" if self.swim_push_anim else "climb") + ((int((self.swimpushing_timer if self.swim_push_anim else self.swimming_timer) * get_key(self.frame_speeds, "swimpush" if self.swim_push_anim else "swim")) % get_key(self.frame_group, "swimpush" if self.swim_push_anim else "swim")) if get_key(self.frame_loops, "swimpush" if self.swim_push_anim else "swim") else min(int((self.swimpushing_timer if self.swim_push_anim else self.swimming_timer) * get_key(self.frame_speeds, "swimpush" if self.swim_push_anim else "swim")), get_key(self.frame_group, "swimpush" if self.swim_push_anim else "swim") - 1))
            self.frame_timer = 0
            if self.anim_state >= get_key(self.frame_data, "swimpush") - 1:
                self.swim_push_anim = False
        elif self.speedy < 0 and not underwater:
            self.anim_state = get_key(self.frame_data, "run" if self.pspeed else "skid") + ((int(self.jumping_timer * get_key(self.frame_speeds, "runjump" if self.pspeed else "jump")) % get_key(self.frame_group, "runjump" if self.pspeed else "jump")) if get_key(self.frame_loops, "runjump" if self.pspeed else "jump") else min(int(self.jumping_timer * get_key(self.frame_speeds, "runjump" if self.pspeed else "jump")), get_key(self.frame_group, "runjump" if self.pspeed else "jump") - 1))
            self.frame_timer = 0
        elif get_key(self.frame_group, "runfall" if self.pspeed else "fall") == 0 and self.fall_timer >= self.fall_duration and self.active_timer > 1:
            if get_key(self.frame_data, "walk") <= self.anim_state <= get_key(self.frame_data, "skid") - 1 or (get_key(self.frame_data, "swimpush") <= self.anim_state <= get_key(self.frame_data, "fire") - 1 and self.fire_lock) or 0 <= self.anim_state <= get_key(self.frame_data, "crouch") - 1:
                self.anim_state = get_key(self.frame_data, "crouch")
        elif self.speedy > 0 and self.fall_timer >= self.fall_duration and nor(self.on_ground, self.down, underwater, get_key(self.frame_group, "runfall" if self.pspeed else "fall") == 0):
            self.anim_state = get_key(self.frame_data, "runjump" if self.pspeed else "jump") + ((int(self.falling_timer * get_key(self.frame_speeds, "runfall" if self.pspeed else "fall")) % get_key(self.frame_group, "runfall" if self.pspeed else "fall")) if get_key(self.frame_loops, "runfall" if self.pspeed else "fall") else min(int(self.falling_timer * get_key(self.frame_speeds, "runfall" if self.pspeed else "fall")), get_key(self.frame_group, "runfall" if self.pspeed else "fall") - 1))
            self.frame_timer = 0
        elif abs(self.speedx) < self.min_speedx and self.on_ground:
            self.anim_state = (int(self.idle_timer * get_key(self.frame_speeds, "idle")) % get_key(self.frame_group, "idle")) if get_key(self.frame_loops, "idle") else min(int(self.idle_timer * get_key(self.frame_speeds, "idle")), get_key(self.frame_group, "idle") - 1)
            self.frame_timer = 0
        elif abs(self.speedx) > self.min_speedx * 2 and self.fall_timer < self.fall_duration and not self.pspeed:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = get_key(self.frame_data, "crouchfall") + ((int(self.frame_timer * get_key(self.frame_speeds, "walk")) % get_key(self.frame_group, "walk")) if get_key(self.frame_loops, "walk") else min(int(self.frame_timer * get_key(self.frame_speeds, "walk")), get_key(self.frame_group, "walk") - 1))
        elif self.pspeed and self.fall_timer < self.fall_duration:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = get_key(self.frame_data, "fall") + ((int(self.frame_timer * get_key(self.frame_speeds, "run")) % get_key(self.frame_group, "run")) if get_key(self.frame_loops, "run") else min(int(self.frame_timer * get_key(self.frame_speeds, "run")), get_key(self.frame_group, "run") - 1))

        self.rect.x = range_number(self.rect.x, 0, camera.x + SCREEN_WIDTH)

    def draw(self, scale=1, offset_x=0, offset_y=0):
        if menu:
            self.changing_controls = self == control_changing_player and key_exists(title_screen[4:], menu_options)
            self.control_changing_timer = range_number(self.control_changing_timer + (1 if self.changing_controls else -1), 0, 60)

        if not self.can_draw:
            return

        frame_rect = get_key(self.sprites, self.size, self.anim_state)
        sprite = self.spritesheet.subsurface(frame_rect)

        should_flip = xor(not self.facing_right, get_nitpick("moonwalking_mario"))
        if should_flip:
            sprite = pygame.transform.flip(sprite, True, False)

        draw_x = self.rect.x - camera.x + offset_x + ((self.rect.width - self.quad_width) / 2)
        draw_y = self.rect.y - camera.y + offset_y + self.rect.height - self.quad_height + 1

        draw_x *= scale
        draw_y *= scale

        sprite = pygame.transform.scale(sprite, (self.quad_width * scale, self.quad_height * scale))

        if self.star:
            star_sprite = sprite.copy()
            star_colors = get_game_property("star_colors")
            color_count = len(star_colors)

            cycle_time = 2 if self.star_timer >= 1 else 4
            index = (self.rainbow_timer // cycle_time) % color_count
            next_index = (index + 1) % color_count
            blend_ratio = (self.rainbow_timer % cycle_time) / cycle_time

            color = lerp_color(get_key(star_colors, index), get_key(star_colors, next_index), blend_ratio)
            star_sprite.fill(color, special_flags=pygame.BLEND_RGBA_MULT)

            screen.blit(star_sprite, (draw_x, draw_y))

            if self.star_effect_timer >= STAR_EFFECT_DURATION:
                self.star_effect_timer -= STAR_EFFECT_DURATION
                particles.append(StarEffect(self.rect.x, self.rect.y, color, (self.rect.width / 2, self.rect.height / 2)))
        else:
            screen.blit(sprite, (draw_x, draw_y))

mus_vol = snd_vol = 1

controls = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "run": pygame.K_z,
    "jump": pygame.K_x
}
controls2 = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "run": pygame.K_c,
    "jump": pygame.K_v
}
controls3 = {
    "up": pygame.K_i,
    "down": pygame.K_j,
    "left": pygame.K_k,
    "right": pygame.K_l,
    "run": pygame.K_m,
    "jump": pygame.K_n
}
controls4 = {
    "up": pygame.K_HOME,
    "down": pygame.K_END,
    "left": pygame.K_DELETE,
    "right": pygame.K_PAGEDOWN,
    "run": pygame.K_INSERT,
    "jump": pygame.K_PAGEUP
}
fullscreen = False
language = "english.json"

characters_data = get_game_property("character_properties", "character_data")
characters_name = [get_game_property("character_properties", "character_data", i, "name") for i in count_list_items(characters_data)]
characters_color = [get_game_property("character_properties", "character_data", i, "color") for i in count_list_items(characters_data)]

for i in range(floor(len(characters_data) / 4)):
    set_key(globals(), "controls" if i == 0 else f"controls{i + 1}")(
        {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "run": pygame.K_z,
            "jump": pygame.K_x
        }
    )
    set_key(globals(), f"controls{i + 2}")(
        {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "run": pygame.K_c,
            "jump": pygame.K_v
        }
    )
    set_key(globals(), f"controls{i + 3}")(
        {
            "up": pygame.K_i,
            "down": pygame.K_j,
            "left": pygame.K_k,
            "right": pygame.K_l,
            "run": pygame.K_m,
            "jump": pygame.K_n
        }
    )
    set_key(globals(), f"controls{i + 4}")(
        {
            "up": pygame.K_HOME,
            "down": pygame.K_END,
            "left": pygame.K_DELETE,
            "right": pygame.K_PAGEDOWN,
            "run": pygame.K_INSERT,
            "jump": pygame.K_PAGEUP
        }
    )

nitpicks_list = [
    "moonwalking_mario",
    "moonwalking_enemies",
    "classic_powerdown",
    "hurry_mode",
    "inverted_block_bounce",
    "infinite_fireballs",
    "infinite_lives",
    "infinite_time",
    "show_fps",
    "show_battery",
    "show_time",
    "play_music_in_pause",
    "non-progressive_powerups",
    "always_underwater",
    "hide_course_name",
    "dont_reset_size",
    "always_konami",
    "rainbow_progress_bar"
]

if exists(load_local_file("nitpicks.json")):
    data = load_json("nitpicks")
        
    for key in nitpicks_list:
        if not key_exists(data, key):
            set_key(data, key)(False)
    
with open(load_local_file("nitpicks.json"), "w") as nitpicks:
    if exists(load_local_file("nitpicks.json")):
        json.dump(data, nitpicks, indent=4)
    else:
        json.dump({key: False for key in nitpicks_list}, nitpicks, indent=4)

nitpicks = load_json("nitpicks")

moonwalking_mario, moonwalking_enemies, classic_powerdown, hurry_mode, inverted_block_bounce, infinite_fireballs, infinite_lives, infinite_time, show_fps, show_battery, show_time, play_music_in_pause, non_progressive_powerups, always_underwater, hide_course_name, dont_reset_size, always_konami, rainbow_progress_bar = nitpicks.values()

if exists(load_local_file("settings.json")) and not getsize(load_local_file("settings.json")) == 0:
    mus_vol = load_json("settings", "mus_vol", default=1)
    snd_vol = load_json("settings", "snd_vol", default=1)
    fullscreen = load_json("settings", "fullscreen", default=False)
    language = load_json("settings", "language", default="english.json")

    for key in load_json("settings"):
        if key.startswith("controls"):
            set_key(globals(), key)(load_json("settings", key))

running = True
konami_code = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_b, pygame.K_a]
konami_complete = get_nitpick("always_konami")
konami_index = len(konami_code) if konami_complete else 0
centerx = SCREEN_WIDTH / 2
centery = SCREEN_HEIGHT / 2
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0))
clock = pygame.time.Clock()
pygame.display.set_icon(pygame.image.load(load_asset("icon.ico")))
pygame.display.set_caption(f"{get_text_from_language("Super Mario Bros. Python")} {f"(FPS: {round(clock.get_fps())})" if get_nitpick("show_fps") else ""}")
player_dist = 20
intro_players = []
low_gravity = False
for i in count_list_items(characters_name):
    try:
        player = Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, controls_enabled=False, size=1, player_number=i, walk_cutscene=True)
    except:
        player = None
    if player is not None:
        intro_players.append(player)
all_players = len(intro_players)
players = []
camera = Camera(get_game_property("camera_smoothness"))
bgm_player = BGMPlayer()
sound_player = SFXPlayer()
title_ground = TitleGround()
background_manager = Background()
text = Text()
logo = Logo()
fireballs_table = {}
tiles = []
pipe_markers = []
items = []
enemies = []
debris = []
power_meters = []
particles = []
overlay_particles = []
overlays = []
player_lives = []
player_sizes = []
players_hud = []
world = 0
course = 0
lives = 50 if konami_complete else get_game_property("lives")
score = 0
time = 0
game_time = 0
pipe_wait_timer = 0
show_course_name = False
show_progress_bar = False
course_name = None
progress_bar = None
castle = None
flagpole = None
x_range = 40
y_range = 0
spawnposx = None
spawnposy = None
main_music = "title"
star_music = None
dead_music = None
clear_music = None
background = None
tileset = None
hud = None
previous_control_player = None
control_changing_player = None
control_changing_timer = 0
fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
a = 255
vertical = False
invertvertical = False
inverthorizontal = False
fade_in = False
fade_out = True

player_count = 0
players_ready = 1
players_controls = 1
selected_course_pack = 1
selected_texture = 1
selected_language = get_folders("languages").index(language) + 1
selected_menu_index = 0
pause_menu_index = 0
old_players_ready = 1
old_players_controls = 1
old_selected_course_pack = 0 if len(get_folders("courses")) == 0 else 1
old_selected_texture = 0 if len(get_folders("textures")) == 0 else 1
old_selected_language = get_folders("languages").index(language) + 1
old_selected_menu_index = 0
old_pause_menu_index = 0
old_mus_vol = mus_vol
old_snd_vol = snd_vol
pipe_timer = 5
dt = 0
game_dt = 0
intro_dt = 0
text_shift_dt = 0
menu_area = 1
intro = True
menu = False
title = False
bind_table = ["up", "down", "left", "right", "run", "jump"]
binding_key = False
current_bind = False
game_ready = False
exit_ready = False
restart_ready = False
reset_ready = False
pipe_ready = False
underwater = False
game = False
everyone_dead = False
pause = False
coins = 0
max_fireballs = infinity if get_nitpick("infinite_fireballs") else 2
game_over = False
fast_music = False

intro_sound = pygame.mixer.Sound(load_intro_file("boot.wav"))
intro_message = random_list_item(load_json(join("system", "intro", "messages")))
konami_message = random_list_item(load_json(join("system", "intro", "konami messages")))

sound_player.play_sound(konami_sound if konami_complete else intro_sound)

while running:
    bgm_player.set_volume(mus_vol)
    sound_player.set_volume(snd_vol)
    SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
    centerx, centery = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
    pygame.display.set_caption(f"{get_text_from_language("Super Mario Bros. Python")} {f"(FPS: {round(clock.get_fps())})" if get_nitpick("show_fps") else ""}")
    current_fps = FPS if clock.get_fps() == 0 else clock.get_fps()
    screen.fill((0, 0, 0))
    keys = pygame.key.get_pressed()
    
    controls_table = [get_key(globals(), f"controls{i+1}" if i else "controls") for i in range(all_players)]

    mus_vol = round(range_number(mus_vol, 0, 1) * 20) / 20
    snd_vol = round(range_number(snd_vol, 0, 1) * 20) / 20
    players_ready = range_number(players_ready, 1, all_players)
    players_controls = range_number(players_controls, 1, all_players)
    selected_course_pack = range_number(selected_course_pack, 0 if len(get_folders("courses")) == 0 else 1, len(get_folders("courses")))
    selected_texture = range_number(selected_texture, 0 if len(get_folders("textures")) == 0 else 1, len(get_folders("textures")))
    selected_language = range_number(selected_language, 0 if len(get_folders("languages")) == 0 else 1, len(get_folders("languages")))
    FPS = range_number(FPS, 1, 120)
    if ((menu or pause) and not old_players_ready == players_ready) or nand(old_mus_vol == mus_vol, old_snd_vol == snd_vol, old_players_controls == players_controls, old_selected_texture == selected_texture, old_selected_course_pack == selected_course_pack, old_selected_language == selected_language, OLD_FPS == FPS):
        sound_player.play_sound(beep_sound)
    old_mus_vol = mus_vol
    old_snd_vol = snd_vol
    old_players_ready = players_ready
    old_players_controls = players_controls
    old_selected_course_pack = selected_course_pack
    old_selected_texture = selected_texture
    old_selected_language = selected_language
    OLD_FPS = FPS

    with open(load_local_file("settings.json"), "w") as settings:
        json.dump(
            {
                "mus_vol": mus_vol,
                "snd_vol": snd_vol,
                **{f"controls{'' if i == 0 else i+1}": get_key(controls_table, i) for i in range(all_players)},
                "fullscreen": fullscreen,
                "fps": FPS,
                "asset_directory": asset_directory,
                "course_directory": course_directory,
                "language": language
            }, settings, indent=4
        )

    if not old_asset_directory == asset_directory:
        old_asset_directory = asset_directory
        reload_data()
        sound_player.play_sound(coin_sound)
        camera.x = 0
        camera.y = 0
        intro_players = []
        for i in count_list_items(characters_name):
            try:
                player = Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, controls_enabled=False, size=1, player_number=i, walk_cutscene=True)
            except:
                player = None
            if player is not None:
                intro_players.append(player)
        all_players = len(intro_players)
        bgm_player.play_music(main_music)

    if fade_in:
        fade_out = False
        a += 255 / FADE_DURATION
        if a >= 255:
            a = 255
            fade_in = False
            if exit_ready or restart_ready:
                running = False
                menu = False
                title = False
                fade_in = False
                fade_out = False
                binding_key = False
                current_bind = False
            elif game_ready:
                course += 1
                while not exists(load_local_file(join("courses", course_directory, f"{world}-{course}.json"))):
                    course = 1
                    world += 1
                initialize_game()
                create_course(join("courses", course_directory, f"{world}-{course}"))
                camera.x = 0
                camera.y = 0
                bgm_player.paused = False
                bgm_player.play_music(main_music, True)
                for i in range(min(player_count, all_players)):
                    if get_key(player_lives, i) == 0:
                        set_key(player_lives, i)(lives)
                    players.append(Player(x=spawnposx + (i * 8), y=spawnposy, player_number=i, lives=get_key(player_lives, i), size=get_key(player_sizes, i)))
                    players_hud.append(PlayerHUD(get_key(players, i)))
                    if not get_game_property("character_properties", "hide_power_meter"):
                        power_meters.append(PowerMeter(get_key(players, i)))
            elif reset_ready:
                initialize_game()
                create_course(join("courses", course_directory, f"{world}-{course}"))
                camera.x = 0
                camera.y = 0
                bgm_player.paused = False
                bgm_player.play_music(main_music, True)
                player_count = players_ready
                player_lives = [get_key(player_lives, i, default=lives) for i in range(player_count)]
                player_sizes = [get_key(player_sizes, i, default=0) for i in range(player_count)]
                for i in range(min(player_count, all_players)):
                    if get_key(player_lives, i) == 0:
                        set_key(player_lives, i)(lives)
                    players.append(Player(x=spawnposx + (i * 8), y=spawnposy, player_number=i, lives=get_key(player_lives, i), size=get_key(player_sizes, i)))
                    players_hud.append(PlayerHUD(get_key(players, i)))
                    if not get_game_property("character_properties", "hide_power_meter"):
                        power_meters.append(PowerMeter(get_key(players, i)))
            elif pipe_ready:
                subzone = (next((marker for marker in [player.pipe_marker for player in players] if marker is not None), None)).zone
                initialize_game(False)
                try:
                    create_course(join("courses", course_directory, f"{world}-{course}" + ("" if subzone == 0 else f"_{subzone}")), True)
                except:
                    raise CustomError("MissingSubzoneError", f"{get_text_from_language("Subzone {subzone} does not exist in").replace("{subzone}", str(subzone))} {world}-{course}.")
                camera.x = 0
                camera.y = 0
                if time <= 100 and not get_game_property("use_elapsed_time"):
                    main_music += "_fast"
                    star_music += "_fast"
                bgm_player.paused = False
                bgm_player.play_music(main_music, True)
                for i in range(min(player_count, all_players)):
                    if get_key(player_lives, i) == 0:
                        set_key(player_lives, i)(lives)
                    players.append(Player(x=spawnposx + (i * 8), y=spawnposy, player_number=i, lives=get_key(player_lives, i), size=get_key(player_sizes, i)))
                    players_hud.append(PlayerHUD(get_key(players, i)))
                    if not get_game_property("character_properties", "hide_power_meter"):
                        power_meters.append(PowerMeter(get_key(players, i)))
            elif everyone_dead:
                camera.x = 0
                camera.y = 0
                if all(player.lives == 0 for player in players):
                    fade_out = True
                    game_over = True
                    game = False
                    bgm_player.play_music("gameover")
                    course = 0
                    dt = 0
                    game_dt = 0
                    pipe_wait_timer = 0
                else:
                    initialize_game()
                    create_course(join("courses", course_directory, f"{world}-{course}"))
                    bgm_player.paused = False
                    bgm_player.play_music(main_music, True)
                    for i in range(min(player_count, all_players)):
                        if get_key(player_lives, i) == 0:
                            set_key(player_lives, i)(lives)
                        players.append(Player(x=spawnposx + (i * 8), y=spawnposy, player_number=i, lives=get_key(player_lives, i), size=get_key(player_sizes, i) if get_nitpick("dont_reset_size") else 0))
                        players_hud.append(PlayerHUD(get_key(players, i)))
                        if not get_game_property("character_properties", "hide_power_meter"):
                            power_meters.append(PowerMeter(get_key(players, i)))
            elif intro:
                menu = True
                title = True
                intro = False
                sound_player.stop_sound(coin_sound, oneup_sound, shrink_sound)
                for name in sound_names:
                    set_key(globals(), f"{name}_sound")(load_sound(name))

    elif fade_out:
        fade_in = False
        a -= 255 / FADE_DURATION
        if a <= 0:
            a = 0
            fade_out = False

    if intro:
        screen.blit(pygame.image.load(load_intro_file("logo.png")).convert_alpha(), (0, 0))
        intro_dt += 1

        dot_speed = 20

        base_text = floor(intro_dt / (len(intro_message) / dot_speed))

        if (intro_dt // 4) % 2 == 0 if konami_complete else True:
            text.create_text(
                text=konami_message if konami_complete else (f"{get_start(intro_message, len(intro_message))}{'.' * (((floor((intro_dt - len(intro_message)) / dot_speed) % 4)) if base_text >= len(intro_message) else 0)}" if base_text >= len(intro_message) else get_start(intro_message, min(base_text, len(intro_message)))),
                position=(centerx, centery * 1.75),
                color=(16.5, 86.5, 8),
                alignment="center",
                font=load_intro_file("font.ttf"),
                font_size=16,
                outline=False,
                scale=1 + (max(sin(min(intro_dt / 60, 3)) if konami_complete else 0, 0)) / 3,
                make_caps=False
            )

        if intro_dt >= (get_game_property("intro_time") * 60) and nor(fade_in, sound_player.is_playing(intro_sound), sound_player.is_playing(konami_sound)):
            fade_in = True

    elif menu:
        game_text = text.wrap_text(get_text_from_language("{players} player game").replace("{players}", str(players_ready)), 32)
        player_game_text = len(game_text.splitlines()) / 16
        control_text = get_text_from_language("controls")
        player_control_text = len(text.wrap_text(f"{control_text} ({get_key(characters_name, players_controls - 1)})", 32).splitlines()) / 16

        languages_list = get_folders("languages")
        language = get_key(languages_list, selected_language - 1)

        title_screen = [
            [
                [game_text, 0.75],
                [get_text_from_language("options"), 0.75 + player_game_text],
                [get_text_from_language("reboot game"), 0.8125 + player_game_text],
                [get_text_from_language("quit"), 0.875 + player_game_text]
            ],
            [
                [text.wrap_text(f"{control_text} ({get_key(characters_name, players_controls - 1)})", 32), 0.75, (( (255, 255, 255), ) * len(control_text)) + (tuple(get_key(characters_color, players_controls - 1)), ) * (len(get_key(characters_name, players_controls - 1)) + 3)],
                [f"{get_text_from_language("music volume:")} {int(mus_vol * 100)}%", 0.75 + player_control_text],
                [f"{get_text_from_language("sound volume:")} {int(snd_vol * 100)}%", 0.8125 + player_control_text],
                [get_text_from_language("set course pack"), 0.875 + player_control_text],
                [get_text_from_language("load texture"), 0.9375 + player_control_text],
                [f"{get_text_from_language("set fps:")} {FPS}", 1 + player_control_text],
                [text.wrap_text(f"{get_text_from_language("set language:")} {get_key(splitext(language), 0)}", 32), 1.0625 + player_control_text],
                [get_text_from_language("back"), 1.0625 + player_control_text + (len(text.wrap_text(f"{get_text_from_language("set language:")} {get_key(splitext(language), 0)}", 32).splitlines()) / 16)]
            ]
        ]

        textures_list = get_folders("textures")
        textures = [[get_text_from_language("base texture"), 0.75]]
        if not len(textures_list) == 0:
            textures.append([f"{text.wrap_text(get_key(textures_list, selected_texture - 1), 16)}", 0.8125])
        textures.append([get_text_from_language("back"), 0.8125 + (len(text.wrap_text(get_key(textures_list, selected_texture - 1), 16).splitlines()) / 8 if textures_list else 0)])
        title_screen.append(textures)

        courses_list = get_folders("courses")
        courses = []
        if not len(courses_list) == 0:
            courses.append([f"{get_key(courses_list, selected_course_pack - 1)}", 0.75])
        courses.append([get_text_from_language("back"), 0.75 if len(courses_list) == 0 else 0.8125])
        title_screen.append(courses)

        for i in range(all_players):
            try:
                title_screen.append(
                    [
                        *[[f"{bind}: {pygame.key.name(get_key(controls_table, i, bind))}", 0.8125 + (j / 16)] for j, bind in enumerate(bind_table)],
                        [get_text_from_language("back"), 0.8125 + (len(bind_table) / 16)]
                    ]
                )
            except:
                pass

        dt += 1
        background_manager.load_background("ground")
        background_manager.update()
        background_manager.draw()

        menu_options = get_key(title_screen, menu_area - 1)
        selected_menu_index = range_number(selected_menu_index, 0, len(menu_options) - 1)
        if not old_selected_menu_index == selected_menu_index:
            sound_player.play_sound(beep_sound)
        old_selected_menu_index = selected_menu_index
        
        camera.update(intro_players, max_y=0)
        
        title_ground.draw()

        if menu_options == get_key(title_screen, 0):
            for i in count_list_items(menu_options):
                options = get_key(menu_options, i)

                text.create_text(
                    text=get_key(options, 0),
                    position=(centerx - (centerx / 2) * (1 - cos(min(text_shift_dt, FADE_DURATION) / FADE_DURATION * pi)) / 2, centery * get_key(options, 1)),
                    alignment="center",
                    stickxtocamera=True,
                    color=(255, 255, 255) if selected_menu_index == i else (128, 128, 128),
                    scale=0.5
                )

                if selected_menu_index == 0:
                    text.create_text(
                        text=get_text_from_language("press left or right\nto switch between players"),
                        position=(centerx - (centerx / 2) * (1 - cos(min(text_shift_dt, FADE_DURATION) / FADE_DURATION * pi)) / 2, centery / 16 + 4),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )
        
        elif menu_options == get_key(title_screen, 1):
            for i in count_list_items(menu_options):
                options = get_key(menu_options, i)

                text.create_text(
                    text=get_key(options, 0),
                    position=(centerx / 2, centery * get_key(options, 1)),
                    alignment="center",
                    stickxtocamera=True,
                    color=(get_key(options, 2) if selected_menu_index == i else tuple(tuple(x / 2 for x in inner) for inner in get_key(options, 2)) if is_tuple_of_tuples(get_key(options, 2)) else tuple(x / 2 for x in get_key(options, 2))) if len(options) == 3 else ((255, 255, 255) if selected_menu_index == i else (128, 128, 128)),
                    scale=0.5
                )

                if selected_menu_index == 0:
                    text.create_text(
                        text=get_text_from_language("press left or right\nto switch between players"),
                        position=(centerx / 2, centery / 16 + 4),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )
        
        elif menu_options == get_key(title_screen, 2):
            for i in count_list_items(textures):
                texture_data = get_key(textures, i)
                
                text.create_text(
                    text=get_key(texture_data, 0),
                    position=(centerx / 2, centery * get_key(texture_data, 1)),
                    alignment="center",
                    stickxtocamera=True,
                    color=(255, 255, 255) if selected_menu_index == i else (128, 128, 128),
                    scale=0.5
                )

                if selected_menu_index == 1 and len(textures_list) >= 1:
                    text.create_text(
                        text=get_text_from_language("press left or right\nto switch between textures"),
                        position=(centerx / 2, centery * (1 + (len(text.wrap_text(get_key(textures_list, selected_texture - 1), 16).splitlines()) / 8))),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )

                elif len(textures_list) == 0:
                    text.create_text(
                        text=text.wrap_text(get_text_from_language("no textures found, please copy the assets folder to the textures folder"), 16),
                        position=(centerx / 2, centery * 1),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )
        
        elif menu_options == get_key(title_screen, 3):
            for i in count_list_items(courses):
                course_data = get_key(courses, i)
                
                text.create_text(
                    text=get_key(course_data, 0),
                    position=(centerx / 2, centery * get_key(course_data, 1)),
                    alignment="center",
                    stickxtocamera=True,
                    color=(255, 255, 255) if selected_menu_index == i else (128, 128, 128),
                    scale=0.5
                )

                if selected_menu_index == 0 and len(courses_list) >= 1:
                    text.create_text(
                        text=get_text_from_language("no textures found, please copy the assets folder to the textures folder"),
                        position=(centerx / 2, centery * 1.125),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )

                elif len(courses_list) == 0:
                    text.create_text(
                        text=get_text_from_language("no course packs found, redownload the courses folder from the source"),
                        position=(centerx / 2, centery * 1.25),
                        alignment="center",
                        stickxtocamera=True,
                        scale=0.5
                    )
        
        elif key_exists(title_screen[4:], menu_options):
            for i in count_list_items(menu_options):
                options = get_key(menu_options, i)

                text.create_text(
                    text=text.wrap_text(f"{get_key(characters_name, menu_area - 5)} {get_text_from_language("controls")}", 16),
                    position=(centerx / 2, centery * 0.75),
                    alignment="center",
                    stickxtocamera=True,
                    color=([tuple(get_key(characters_color, menu_area - 5))] * len(get_key(characters_name, menu_area - 5)) + [(255, 255, 255)] * 9),
                    scale=0.5
                )

                text.create_text(
                    text=get_key(options, 0),
                    position=(centerx / 2, centery * (get_key(options, 1) + ((len(text.wrap_text(f"{get_key(characters_name, menu_area - 5)} {get_text_from_language("controls")}", 16).splitlines()) - 1) / 8))),
                    alignment="center",
                    stickxtocamera=True,
                    color=(255, 255, 255) if selected_menu_index == i else (128, 128, 128),
                    scale=0.5
                )
                
                if binding_key and selected_menu_index == i:
                    text.create_text(
                        text=text.wrap_text(get_text_from_language("press esc to cancel binding"), 16),
                        position=(centerx / 2, centery / 16),
                        alignment="center",
                        stickxtocamera=True,
                        color=(255, 255, 255) if selected_menu_index == i else (128, 128, 128),
                        scale=0.5
                    )

        if game_ready or exit_ready:
            logo.draw()
            logo.update()
        
        if dt / 60 >= logo.bounce_time:
            if title:
                bgm_player.play_music(main_music)
                fade_out = True
                title = False
            else:
                text_shift_dt += 1
                for player in intro_players:
                    if key_exists(title_screen[4:], menu_options):
                        control_changing_player = get_key(intro_players, menu_area - 5)
                    player.rect.bottom = title_ground.y
                    player.on_ground = True
                    player.speed = 2
                    player.speedx = 2
                    player.speedy = 0
                    player.fall_timer = 0
                    player.update()
                    player.draw(1 + (1 - cos(pi * player.control_changing_timer / 60)) / 2, (1 - cos(pi * player.control_changing_timer / 60)) / 2 * ((centerx * 0.75) - (player.rect.x - camera.x + (player.rect.width / 2))), (1 - cos(pi * player.control_changing_timer / 60)) / 2 * ((centery / 2) - (player.rect.y - camera.y + player.rect.height - (player.quad_height / 2) + 1)))

    elif game:
        if not everyone_dead:
            if 0 < sum(1 for player in players if player.pipe_timer >= player.pipe_duration * 60) < len([player for player in players if player.dead_timer < 30]):
                pipe_wait_timer = (60 * (pipe_timer - 1)) if (sum(1 for player in players if player.dead_timer >= 30) == len(players)) else min(pipe_wait_timer + 1, (60 * (pipe_timer - 1)))
            elif sum(1 for player in players if player.pipe_timer >= player.pipe_duration * 60) == len([player for player in players if player.dead_timer < 30]):
                pipe_wait_timer = 60 * (pipe_timer - 1)

        pipe_ready = pipe_wait_timer == 60 * (pipe_timer - 1)
        if pipe_ready and not fade_in:
            fade_in = True
            bgm_player.fade_out()

        if not pause:
            dt += 1

        if nor(pause, everyone_dead, any(player.size_change for player in players), any(player.piping for player in players), any(player.clear for player in players), get_nitpick("infinite_time")):
            game_dt += 1
        
        course_time = floor(time + (game_dt / 60)) if get_game_property("use_elapsed_time") else ceil(time - (game_dt / get_game_property("timer_speed")) / 60)

        background_manager.load_background(background)
        background_manager.update()
        background_manager.draw()

        if castle:
            castle.draw()

        if flagpole:
            flagpole.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                flagpole.update()

        for item in fix_list(items):
            if item.is_visible():
                if item.sprouting and item.sprout_timer > 0:
                    item.draw()
                if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                    item.update()
            if item.below_camera():
                items.remove(item)

        if any(player.size_change for player in players):
            for player in players:
                if player.piping:
                    player.draw()
        else:
            for player in players:
                if player.piping:
                    player.draw()

        for tile in tiles:
            if tile.bouncing:
                continue
            tile.draw()
            if not pause:
                tile.update()

        for tile in tiles:
            if tile.bouncing:
                tile.draw()
            if not pause:
                tile.update()

        for item in fix_list(items):
            if item.is_visible():
                if not item.sprouting:
                    item.draw()

        for fireball_list in fireballs_table.values():
            for fireball in fix_list(fireball_list):
                if fireball.is_visible():
                    fireball.draw()
                    if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                        fireball.update()
                else:
                    fireball_list.remove(fireball)

        for enemy in enemies:
            if enemy.is_visible():
                if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                    enemy.update()

        if any(player.size_change for player in players):
            for player in players:
                if not player.piping:
                    player.draw()
                if player.size_change:
                    if nor(pause, pipe_ready):
                        player.update()
        else:
            for player in players:
                if not player.piping:
                    player.draw()
                if nor(pause, pipe_ready):
                    player.update()

        for power_meter in power_meters:
            if not get_game_property("character_properties", "hide_power_meter"):
                power_meter.draw()
                if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                    power_meter.update()

        for enemy in fix_list(enemies):
            if enemy.is_visible():
                enemy.draw()
            else:
                if enemy.shotted:
                    enemies.remove(enemy)
            if enemy.below_camera():
                enemies.remove(enemy)

        if progress_bar and show_progress_bar:
            progress_bar.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                progress_bar.update()

        player_lives = [player.lives for player in players]
        player_sizes = [player.size for player in players]

        if course_time <= 0 and not get_game_property("use_elapsed_time"):
            if everyone_dead:
                text.create_text(
                    text=get_text_from_language("time's up!"),
                    position=(centerx, centery),
                    alignment="center",
                    stickxtocamera=True,
                    stickytocamera=True
                )
            else:
                for player in players:
                    player.dead = True
                    player.dead_speed = -5

        everyone_dead = all(player.dead for player in players)
        if everyone_dead:
            pause = False

        if nor(bgm_player.is_playing("hurry"), everyone_dead, pipe_ready, pause):
            if all(player.star_timer < 1 for player in players) and any(player.star_music for player in players):
                bgm_player.play_music(main_music)
                for player in players:
                    player.star_music = False

            if any(player.star_timer >= 1 for player in players) and not any(player.star_music for player in players):
                bgm_player.play_music(star_music)
                for player in players:
                    player.star_music = True

        if course_time <= 100 and nor(fast_music, get_game_property("use_elapsed_time")):
            if not main_music.endswith("fast"):
                bgm_player.play_music("hurry")
                if exists(load_asset(join("music", f"{main_music}.ogg"))):
                    main_music = f"{main_music}_fast"
                if exists(load_asset(join("music", f"{star_music}.ogg"))):
                    star_music = f"{star_music}_fast"
            if nor(bgm_player.is_playing("hurry"), everyone_dead, pipe_ready, pause):
                bgm_player.play_music(main_music if all(player.star_timer < 1 for player in players) else star_music)
                fast_music = True

        if all(player.dead_timer >= get_game_property("death_timer") * 60 for player in players) and not bgm_player.is_playing(dead_music):
            fade_in = True

        for debris_part in fix_list(debris):
            debris_part.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                debris_part.update()

        for particle in fix_list(particles):
            particle.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                particle.update()

        for overlay in fix_list(overlays):
            overlay.draw()
            if not pause:
                overlay.update()

        if hud:
            hud.draw()

            game_time = "inf" if get_nitpick("infinite_time") else (f"{format_number(floor(course_time // 3600), 2)}:{format_number(floor((course_time // 60) % 60), 2)}:{format_number(floor(course_time % 60), 2)}" if get_game_property("use_elapsed_time") else format_number(course_time, 3))

            text.create_text(
                text=f"x{format_number(hud.coins, 2)}",
                position=(20 + hud.image.get_width(), 16),
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            text.create_text(
                text=format_number(score, 9),
                position=(632, 16),
                alignment="right",
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            text.create_text(
                text=game_time,
                position=(632, 32),
                alignment="right",
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            screen.blit(load_sprite("hudclock"), ((630 - (len(game_time) + 1) * (text.font_size / 2)) - (load_sprite("hudclock").get_width() - (text.font_size / 2)), 32))

            if 0 <= game_dt <= 60 or 180 <= game_dt <= 240:
                course_name_y = SCREEN_HEIGHT - (12 * (sin(radians((game_dt - 30) * 3)) + 1))
            
            if show_course_name and nor(get_nitpick("hide_course_name"), course_name is None):
                text.create_text(
                    text=course_name,
                    position=(centerx, course_name_y),
                    alignment="center",
                    stickxtocamera=True,
                    stickytocamera=True
                )

        if players_hud:
            for player_hud in players_hud:
                player_hud.draw()
                if nor(everyone_dead, pause, pipe_ready):
                    player_hud.update()

                for player in players:
                    text.create_text(
                        text=f"x{"inf" if get_nitpick("infinite_lives") else player.lives}",
                        position=(16 + (get_key(player_hud.sprite_size, 0) // 2), 24 + (player.player_number + 1) * 16),
                        stickxtocamera=True,
                        stickytocamera=True,
                        scale=0.5
                    )

        for overlay_particle in fix_list(overlay_particles):
            overlay_particle.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                overlay_particle.update()

        (sound_player.loop_sound if any(player.pspeed for player in players) and nor(everyone_dead, any(player.piping for player in players)) else sound_player.stop_sound)(pspeed_sound)
        (sound_player.loop_sound if any(player.skidding for player in players) and nor(everyone_dead, any(player.piping for player in players)) else sound_player.stop_sound)(skid_sound)

        pause_menu_options = [
            [get_text_from_language("resume"), 0.625],
            [get_text_from_language("restart as {players} player game").replace("{players}", str(players_ready)), 0.75],
            [get_text_from_language("reboot game"), 0.875],
            [f"{get_text_from_language("music volume:")} {int(mus_vol * 100)}%", 1],
            [f"{get_text_from_language("sound volume:")} {int(snd_vol * 100)}%", 1.125],
            [f"{get_text_from_language("set fps:")} {int(FPS)}", 1.25],
            [get_text_from_language("quit"), 1.375]
        ]

        pause_menu_index = range_number(pause_menu_index, 0, len(pause_menu_options) - 1)
        if not old_pause_menu_index == pause_menu_index:
            sound_player.play_sound(beep_sound)
        old_pause_menu_index = pause_menu_index

        if pause:
            for i in count_list_items(pause_menu_options):
                options = get_key(pause_menu_options, i)

                text.create_text(
                    text=get_key(options, 0),
                    position=(centerx, centery * get_key(options, 1)),
                    alignment="center",
                    stickxtocamera=True,
                    stickytocamera=True,
                    color=(255, 255, 255) if pause_menu_index == i else (128, 128, 128)
                )

        try:
            if nor(any(player.piping for player in players), everyone_dead, pause):
                camera.update([player for player in players if not player.dead], x_range, y_range - 400)
        except ZeroDivisionError:
            pass
    
    elif game_over:
        dt += 1
        text.create_text(
            text=get_text_from_language("game over"),
            position=(centerx, centery),
            alignment="center"
        )
        if dt >= get_game_property("gameover_time") * 60:
            text.create_text(
                text=get_text_from_language("press enter to restart"),
                position=(centerx, SCREEN_HEIGHT // 1.75),
                alignment="center",
                scale=0.5
            )

    if get_nitpick("show_battery"):
        battery = psutil.sensors_battery().percent
        text.create_text(
            text=f"{get_text_from_language("battery:")} {battery}%",
            position=(632, 384 - (text.font_size / 2 if get_nitpick("show_time") else 0)),
            alignment="right", stickxtocamera=True, stickytocamera=True, scale=0.5,
            color=tuple(range_number(c, 0, 255) for c in ((255, 0, 0) if battery < 0 else ((255, min(255, int(255 * (battery / 40))), 0) if battery < 50 else (max(0, int(255 * (1 - ((battery - 50) / 40)))), 255, 0) if battery < 100 else (0, 255, 0))))
        )

    if get_nitpick("show_time"):
        text.create_text(
            text=f"{get_text_from_language("time:")} {system_time.now().strftime('%H:%M:%S')}",
            position=(632, 384), alignment="right", stickxtocamera=True, stickytocamera=True, scale=0.5
        )

    fade_surface.fill((0, 0, 0, a))
    screen.blit(fade_surface, (0, 0))

    if menu and not fade_in:
        logo.draw()
        logo.update()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = menu = title = fade_in = fade_out = binding_key = current_bind = False
        elif event.type == pygame.WINDOWFOCUSLOST and game and nor(pause, fade_in):
            bgm_player.pause_music()
            pause = not pause
            sound_player.pause()
            sound_player.play_sound(pause_sound)
            pause_menu_index = old_pause_menu_index = 0
        elif event.type == pygame.KEYDOWN:
            key, mod = event.key, event.mod
            if game and key == pygame.K_ESCAPE and nor(any(player.piping for player in players), everyone_dead, fade_in):
                bgm_player.pause_music()
                pause = not pause
                sound_player.pause()
                sound_player.play_sound(pause_sound)
                pause_menu_index = old_pause_menu_index = 0
            if game and pause and not fade_in:
                if key == pygame.K_DOWN:
                    pause_menu_index += 1
                elif key == pygame.K_UP:
                    pause_menu_index -= 1
                elif key_exists((pygame.K_LEFT, pygame.K_RIGHT), key):
                    change = 1 if key == pygame.K_RIGHT else -1
                    if pause_menu_index == 1:
                        players_ready += change
                    elif pause_menu_index == 3:
                        mus_vol += change / (4 if mod & pygame.KMOD_CTRL else 20)
                    elif pause_menu_index == 4:
                        snd_vol += change / (4 if mod & pygame.KMOD_CTRL else 20)
                    elif pause_menu_index == 5:
                        FPS += (change * (5 if mod & pygame.KMOD_CTRL else 1))
                elif key == pygame.K_RETURN:
                    if pause_menu_index == 0:
                        pause = False
                        sound_player.pause()
                        sound_player.play_sound(coin_sound)
                        bgm_player.pause_music()
                    elif pause_menu_index == 1:
                        fade_in = reset_ready = True
                        bgm_player.fade_out()
                        sound_player.play_sound(coin_sound)
                    elif pause_menu_index == 2:
                        fade_in = restart_ready = True
                        bgm_player.fade_out()
                        sound_player.play_sound(coin_sound)
                    elif pause_menu_index == 6:
                        fade_in = exit_ready = True
                        bgm_player.fade_out()
                        sound_player.play_sound(coin_sound)
            if key == pygame.K_RETURN and ((menu and menu_options == get_key(title_screen, 0) and selected_menu_index == 0 and nor(title, fade_in, fade_out)) or (game_over and dt >= get_game_property("gameover_time") * 60)) and not game_ready:
                low_gravity = False
                infinite_lives = False
                always_underwater = False
                if get_key(keys, pygame.K_UP):
                    lives = 99
                elif get_key(keys, pygame.K_LEFT):
                    low_gravity = True
                elif get_key(keys, pygame.K_b):
                    infinite_lives = True
                elif get_key(keys, pygame.K_r):
                    always_underwater = True
            if game_over and dt >= get_game_property("gameover_time") * 60 and key == pygame.K_RETURN and not game_ready:
                bgm_player.stop_music()
                sound_player.stop_all_sounds()
                sound_player.play_sound(coin_sound)
                fade_in = game_ready = True
                if not get_key(keys, pygame.K_a):
                    world = 0
            if key == pygame.K_RETURN and mod & pygame.KMOD_ALT:
                fullscreen = not fullscreen
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0))
            if menu and nor(title, fade_in, fade_out, game_ready):
                if binding_key:
                    sound_player.play_sound(shrink_sound if key == pygame.K_ESCAPE else powerup_sound)
                    if not key == pygame.K_ESCAPE:
                        set_key(controls_table, menu_area - 5, get_key(bind_table, selected_menu_index))(key)
                    binding_key = current_bind = False
                    sound_player.stop_sound(sprout_sound)
                else:
                    if key == pygame.K_DOWN:
                        selected_menu_index += 1
                    elif key == pygame.K_UP:
                        selected_menu_index -= 1
                    elif key_exists((pygame.K_LEFT, pygame.K_RIGHT), key):
                        change = 1 if key == pygame.K_RIGHT else -1
                        if menu_options == get_key(title_screen, 0) and selected_menu_index == 0:
                            players_ready += change
                        elif menu_options == get_key(title_screen, 1):
                            if selected_menu_index == 0:
                                players_controls += change
                            elif selected_menu_index == 1:
                                mus_vol += change / (4 if mod & pygame.KMOD_CTRL else 20)
                            elif selected_menu_index == 2:
                                snd_vol += change / (4 if mod & pygame.KMOD_CTRL else 20)
                            elif selected_menu_index == 5:
                                FPS += (change * (5 if mod & pygame.KMOD_CTRL else 1))
                            elif selected_menu_index == 6:
                                selected_language += change
                        elif menu_options == get_key(title_screen, 2) and selected_menu_index == 1 and len(textures) >= 1:
                            selected_texture += change
                        elif menu_options == get_key(title_screen, 3) and selected_menu_index == 1 and len(courses) >= 1:
                            selected_course_pack += change
                    elif key == pygame.K_BACKSPACE and not binding_key:
                        if key_exists(title_screen[1:4], menu_options) or key_exists(title_screen[4:], menu_options):
                            selected_menu_index = old_selected_menu_index = 0
                            menu_area = 1 if menu_options == get_key(title_screen, 1) else 2
                            players_ready = old_players_ready = 1
                            players_controls = old_players_controls = 1
                            sound_player.play_sound(shrink_sound)
                    elif key == pygame.K_RETURN:
                        if menu_options == get_key(title_screen, 0):
                            if selected_menu_index == 1:
                                selected_menu_index = old_selected_menu_index = 0
                                menu_area = 2
                                players_ready = old_players_ready = 1
                                sound_player.play_sound(coin_sound)
                            elif selected_menu_index == 2:
                                fade_in = restart_ready = exit_ready = True
                                bgm_player.fade_out()
                                sound_player.play_sound(coin_sound)
                            elif selected_menu_index == 3:
                                fade_in = exit_ready = True
                                bgm_player.fade_out()
                                sound_player.play_sound(coin_sound)
                            else:
                                fade_in = game_ready = True
                                bgm_player.fade_out()
                                sound_player.play_sound(coin_sound)
                                player_count = players_ready
                                player_lives, player_sizes = [lives] * player_count, [0] * player_count
                        elif menu_options == get_key(title_screen, 1):
                            if key_exists((0, 3, 4, 7), selected_menu_index):
                                if selected_menu_index == 0:
                                    menu_area = players_controls + 4
                                elif selected_menu_index == 3:
                                    menu_area = 4
                                elif selected_menu_index == 4:
                                    menu_area = 3
                                elif selected_menu_index == 7:
                                    menu_area = 1
                                selected_menu_index = old_selected_menu_index = 0
                                players_controls = old_players_controls = 1
                                selected_texture = old_selected_texture = 1
                                selected_course_pack = old_selected_course_pack = 1
                                sound_player.play_sound(coin_sound)
                        elif menu_options == get_key(title_screen, 2):
                            if selected_menu_index == 0:
                                old_asset_directory = asset_directory
                                asset_directory = "assets"
                            elif selected_menu_index == 1:
                                if len(textures_list) == 0:
                                    selected_menu_index = old_selected_menu_index = 0
                                    menu_area = 2
                                    sound_player.play_sound(coin_sound)
                                else:
                                    old_asset_directory = asset_directory
                                    asset_directory = join("textures", get_key(textures_list, selected_texture - 1))
                            else:
                                selected_menu_index = old_selected_menu_index = 0
                                menu_area = 2
                                sound_player.play_sound(coin_sound)
                        elif menu_options == get_key(title_screen, 3):
                            if selected_menu_index == 0:
                                if len(courses_list) == 0:
                                    selected_menu_index = old_selected_menu_index = 0
                                else:
                                    course_directory = f"{get_key(courses_list, selected_course_pack - 1)}"
                                menu_area = 2
                                sound_player.play_sound(coin_sound)
                            else:
                                selected_menu_index = old_selected_menu_index = 0
                                menu_area = 2
                                sound_player.play_sound(coin_sound)
                        elif key_exists(title_screen[4:], menu_options) and not binding_key:
                            if selected_menu_index == len(menu_options) - 1:
                                selected_menu_index = old_selected_menu_index = 0
                                menu_area = 2
                                players_controls = old_players_controls = 1
                                sound_player.play_sound(coin_sound)
                            else:
                                binding_key = True
                                current_bind = get_key(bind_table, selected_menu_index)
                                sound_player.play_sound(sprout_sound)
                                sound_player.stop_sound(powerup_sound)
            if intro and nor(fade_in, konami_complete):
                if event.key == get_key(konami_code, konami_index):
                    konami_index += 1
                    if konami_index == len(konami_code):
                        lives = 50
                        konami_index = 0
                        konami_complete = True
                        intro_dt = 0
                        sound_player.play_sound(konami_sound, oneup_sound)
                        sound_player.stop_sound(coin_sound, intro_sound)
                    else:
                        sound_player.play_sound(coin_sound)
                        sound_player.stop_sound(shrink_sound)
                elif konami_index > 0:
                    konami_index = 0
                    sound_player.play_sound(shrink_sound)

    pygame.display.update()
    bgm_player.update()
    clock.tick(FPS)

pygame.quit()

with open(load_local_file("settings.json"), "w") as settings:
    json.dump(
        {
            "mus_vol": mus_vol,
            "snd_vol": snd_vol,
            **{f"controls{'' if i == 0 else i+1}": get_key(controls_table, i) for i in range(all_players)},
            "fullscreen": fullscreen,
            "fps": FPS,
            "asset_directory": asset_directory,
            "course_directory": course_directory,
            "language": language
        }, settings, indent=4
    )

if restart_ready:
    subprocess.Popen(f'"{sys.executable}" "{abspath(get_key(sys.argv, 0))}"', shell=True)
    sys.exit()