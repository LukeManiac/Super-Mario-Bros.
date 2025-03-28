import pygame, json, math, numpy, psutil
from os.path import dirname, abspath, exists, getsize
from datetime import datetime

pygame.init()
pygame.font.init()
pygame.mixer.init()

infinity = float("inf")
asset_directory = "assets"

def load_local_file(file):
    return f"{dirname(abspath(__file__))}/{file}"

def load_json(path):
    with open(load_local_file(f"{path}.json"), "r") as file:
        return json.load(file)
    
def key_exists(dictionary, key):
    return key in dictionary

def get_game_property(*items):
    data = load_json("assets/game_properties")
    for item in items:
        data = data[item]
    return data

def load_asset(asset):
    return load_local_file(f"{asset_directory}/{asset}")

def load_background(background):
    return pygame.image.load(load_asset(f"backgrounds/{background}.png")).convert_alpha()

def load_sound(sound):
    return pygame.mixer.Sound(load_asset(f"sounds/{sound}.wav"))
    
def load_sprite(sprite):
    return pygame.image.load(load_asset(f"sprites/{sprite}.png")).convert_alpha()
    
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

def create_course(data):
    default_music = {
        "main_music": None,
        "star_music": "star",
        "dead_music": "dead",
        "clear_music": "clear",
    }

    if "music" in data and isinstance(data["music"], dict):
        music_keys = ["main_music", "star_music", "dead_music", "clear_music"]
        for key in music_keys:
            if key in data["music"]:
                globals()[key] = data["music"][key]
            else:
                globals()[key] = default_music[key]

    else:
        for key, value in default_music.items():
            globals()[key] = value

    tiles = []

    if "tiles" in data and isinstance(data["tiles"], dict):
        for class_name, params_list in data["tiles"].items():
            if class_name == "Pipe":
                for params in params_list:
                    tiles.extend(create_pipe(*params))
            elif class_name in globals() and callable(globals()[class_name]):
                for params in params_list:
                    obj_params = [
                        globals()[param] if isinstance(param, str) and param in globals() and callable(globals()[param]) else param
                        for param in (params if isinstance(params, (list, tuple)) else [params])
                    ]
                    obj = globals()[class_name](*obj_params)
                    if hasattr(obj, "spriteset"):
                        obj.spriteset = data.get("spriteset", 0)

                    tiles.append(obj)

    if "castle" in data and isinstance(data["castle"], list):
        globals()["castle"] = data["castle"]

        if "Castle" in globals() and callable(globals()["Castle"]):
            castle_obj = globals()["Castle"](*data["castle"])
            castle_obj.spriteset = data.get("spriteset", 0)
            globals()["castle"] = castle_obj

    if "width" in data and isinstance(data["width"], int):
        globals()["x_range"] = (data["width"] - (SCREEN_WIDTH // 16)) * 16

    if "timelimit" in data and isinstance(data["timelimit"], int):
        globals()["time"] = 100 if nitpicks["hurry_mode"] else data["timelimit"]
        globals()["course_time"] = 100 if nitpicks["hurry_mode"] else data["timelimit"]

    if "spawnpositions" in data and isinstance(data["spawnpositions"], list):
        globals()["spawnposx"], globals()["spawnposy"] = data["spawnpositions"]
    
    globals()["tiles"] = tiles

    for category, items in data.items():
        if category in ("music", "tiles", "spriteset", "spawnpositions", "castle"):
            continue

        object_list = []
        if isinstance(items, dict):
            for class_name, params_list in items.items():
                if class_name in globals() and callable(globals()[class_name]):
                    for params in params_list:
                        obj_params = [
                            globals()[param] if isinstance(param, str) and param in globals() and callable(globals()[param]) else param
                            for param in (params if isinstance(params, (list, tuple)) else [params])
                        ]
                        obj = globals()[class_name](*obj_params)
                        if hasattr(obj, "spriteset"):
                            obj.spriteset = data.get("spriteset", 0)

                        object_list.append(obj)

        globals()[category] = object_list

def create_pipe(x, y, length=2, can_enter=False, new_zone=None, pipe_dir="up", color=1):
    color -= 1
    pipes = []
    id_adjustments = {
        "up": lambda pid: pid,
        "down": lambda pid: pid + (4 if pid in {1, 2} else 0),
        "left": lambda pid: pid + (pid == 3) * 8 + (pid == 4) * 4 + (pid == 1) * 11 + (pid == 2) * 7,
        "right": lambda pid: pid + (pid == 3) * 8 + (pid == 4) * 4 + (pid == 1) * 9 + (pid == 2) * 5,
    }
    coord_adjustments = {
        "up": lambda i, j: (x + i, y + j),
        "down": lambda i, j: (x + i, y - j),
        "left": lambda i, j: (x - j, y - i),
        "right": lambda i, j: (x + j, y - i),
    }

    for i in range(2):
        for j in range(length):
            pipe_id = i + (j * 2) + 1
            while pipe_id >= 5:
                pipe_id -= 2

            px, py = coord_adjustments[pipe_dir](i, j)
            pipes.append(Tile(px, py, f"pipe{id_adjustments[pipe_dir](pipe_id)}", color))
            if can_enter and i == 0 and j == 0:
                pipe_markers.append(PipeMarker(px + (0.5 if pipe_dir == "up" or pipe_dir == "down" else 0), py + (1 if pipe_dir == "left" or pipe_dir == "right" else 0), pipe_dir, new_zone))

    return pipes

def recolor_surface(surface, old_color, new_color):
    recolored = surface.copy()
    pixel_array = pygame.PixelArray(recolored)

    for x in range(recolored.get_width()):
        for y in range(recolored.get_height()):
            pixel = recolored.unmap_rgb(pixel_array[x, y])
            if pixel[:3] == tuple(old_color):
                new_pixel = recolored.map_rgb([*new_color, pixel[3]])
                pixel_array[x, y] = new_pixel

    del pixel_array
    return recolored

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 400
WALK_SPEED = 2.5
RUN_SPEED = 4
JUMP_HOLD_TIME = 10
MIN_SPEEDX = 0.25
MIN_RUN_TIMER = 0
MAX_RUN_TIMER = 75
FPS = 60
FADE_DURATION = 60
SPROUT_SPEED = 1

beep_sound = load_sound("beep")
break_sound = load_sound("break")
bump_sound = load_sound("bump")
coin_sound = load_sound("coin")
dead_sound = load_sound("dead")
fireball_sound = load_sound("fireball")
jump_sound = load_sound("jump")
jumpbig_sound = load_sound("jumpbig")
oneup_sound = load_sound("oneup")
pause_sound = load_sound("pause")
pipe_sound = load_sound("pipe")
powerup_sound = load_sound("powerup")
pspeed_sound = load_sound("pspeed")
shot_sound = load_sound("shot")
skid_sound = load_sound("skid")
sprout_sound = load_sound("sprout")
stomp_sound = load_sound("stomp")

class PipeMarker:
    def __init__(self, x, y, pipe_dir, zone):
        self.x = x * 16
        self.y = y * 16 + 8
        if pipe_dir == "up":
            self.y -= 1
        elif pipe_dir == "down":
            self.y += 1
        elif pipe_dir == "left":
            self.x -= 1
        elif pipe_dir == "right":
            self.x += 1
        self.pipe_dir = pipe_dir
        self.zone = zone
        self.rect = pygame.Rect(self.x, self.y, 16, 16)

class SFXPlayer:
    def __init__(self):
        self.sounds = {}
        self.paused = False

    def play_sound(self, sound, pitch=0):
        if sound not in self.sounds:
            self.sounds[sound] = sound

        pitched_sound = self.change_pitch(self.sounds[sound], pitch)
        pitched_sound.set_volume(snd_vol)
        pitched_sound.stop()
        pitched_sound.play()

    def change_pitch(self, sound, semitones):
        return sound if semitones == 0 else pygame.sndarray.make_sound(
            pygame.sndarray.array(sound)[
                numpy.round(
                    numpy.linspace(
                        0, len(pygame.sndarray.array(sound)) - 1,
                        int(len(pygame.sndarray.array(sound)) / (2 ** (semitones / 12)))
                    )
                ).astype(int)
            ]
        )

    def stop_sound(self, sound):
        if sound in self.sounds:
            self.sounds[sound].stop()

    def stop_all_sounds(self):
        for sound in self.sounds.values():
            sound.stop()

    def loop_sound(self, sound):
        self.sounds[sound] = sound
        if sound in self.sounds and not self.is_playing(self.sounds[sound]):
            self.sounds[sound].set_volume(snd_vol)
            self.sounds[sound].play(-1)

    def set_volume(self, volume):
        for sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)

    def is_playing(self, *sounds):
        return any(sound.get_num_channels() > 0 for sound in sounds)

class BGMPlayer:
    def __init__(self):
        self.loop_point = 0
        self.music = None
        self.music_playing = False
        self.paused = False

    def play_music(self, music):
        if not self.paused:
            self.stop_music()
            self.music = load_asset(f"music/{music}.ogg")
            try:
                self.loop_point = music_table[music]
            except KeyError:
                self.loop_point = False
            pygame.mixer.music.load(self.music)
            pygame.mixer.music.play(-1 if self.loop_point == True else 0)
            self.set_volume(mus_vol)
            if self.loop_point != 0:
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
        pygame.mixer.music.fadeout(int(FADE_DURATION * (1000 / 60)))

    def pause_music(self):
        self.paused = not self.paused
        (pygame.mixer.music.pause if self.paused else pygame.mixer.music.unpause)()

    def update(self):
        if self.music_playing:
            if nor(self.paused, pygame.mixer.music.get_busy()):
                pygame.mixer.music.play(0, self.loop_point)
                self.music_playing = True

    def is_playing(self, music):
        return pygame.mixer.music.get_busy() and self.music == load_asset(f"bgm_{music}.ogg")

class Text:
    def __init__(self):
        self.font_size = 16
        self.font = pygame.font.Font(load_asset("font.ttf"), self.font_size)

    def create_text(self, text, position, color=(255, 255, 255), alignment="left", stickxtocamera=False, stickytocamera=False, scale=1):
        char_offset = 0
        line_offset = 0
        lines = text.split("\n")
        x, y = position
        rendered_lines = []

        if stickxtocamera and camera:
            x += camera.x

        if stickytocamera and camera:
            y += camera.y

        max_line_width = 0

        for line in lines:
            line_width = sum(
                int(self.font.render(char, True, color).get_width() * scale) + char_offset for char in line
            )
            max_line_width = max(max_line_width, line_width)

        for i, line in enumerate(lines):
            rendered_line = []
            offset_x = 0

            for char in line:
                char_surface = self.font.render(char, True, color)
                if scale != 1.0:
                    char_surface = pygame.transform.scale(
                        char_surface,
                        (int(char_surface.get_width() * scale), int(char_surface.get_height() * scale))
                    )
                rendered_line.append((char_surface, offset_x))
                offset_x += char_surface.get_width() + char_offset

            rendered_lines.append((rendered_line, y + i * (int(self.font.get_height() * scale) + line_offset)))

        for rendered_line, line_y in rendered_lines:
            start_x = x
            start_x -= camera.x

            if alignment == "center":
                start_x -= max_line_width // 2
            elif alignment == "right":
                start_x -= max_line_width

            for char_surface, char_x in rendered_line:
                screen.blit(char_surface, (start_x + char_x, line_y))

class Background:
    def __init__(self):
        self.bg_image = None
        self.bg_layers = []
        self.bg_positions = []
        self.layer_width = 0
        self.bg_width = 0
        self.bg_height = 0

    def load_background(self, bgname):
        self.bg_layers_count = background_layers[bgname]
        self.bg_image = load_background(bgname)
        self.bg_width, self.bg_height = self.bg_image.get_size()
        self.layer_width = self.bg_width // self.bg_layers_count
        self.bg_layers = [self.bg_image.subsurface(pygame.Rect(x * self.layer_width, 0, self.layer_width, self.bg_height)) for x in range(self.bg_layers_count)]
        self.bg_positions = [0] * self.bg_layers_count

    def update(self):
        for i in count_list_items(self.bg_layers):
            parallax_factor = 1 - (i / 10)
            self.bg_positions[i] = -(camera.x * parallax_factor) % self.layer_width

    def draw(self):
        for i in count_list_items(self.bg_layers):
            layer_x = self.bg_positions[i]
            while layer_x < SCREEN_WIDTH:
                screen.blit(self.bg_layers[i], (layer_x, SCREEN_HEIGHT - self.bg_height))
                layer_x += self.layer_width
            layer_x = self.bg_positions[i] - self.layer_width
            while layer_x < 0:
                screen.blit(self.bg_layers[i], (layer_x, SCREEN_HEIGHT - self.bg_height))
                layer_x += self.layer_width

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, players, max_x=None):
        self.x = range_number(sum(player.rect.x + player.rect.width for player in players) / len(players) - SCREEN_WIDTH // 2, 0, (max_x if max_x is not None else infinity))
        self.y = range_number(sum(player.rect.y + player.rect.height for player in players) / len(players) - SCREEN_HEIGHT // 2, 0, 0)

class Logo:
    def __init__(self):
        self.x = centerx - 88
        self.y = -88
        self.speedy = 0
        self.timer = 0
        self.bounce_y = 48
        self.bounce_time = 3
        self.spritesheet = load_sprite("logo")

    def update(self):
        self.timer = min(self.timer + 1, self.bounce_time * 60)
        canbounce = self.y < self.bounce_y
        if self.timer < self.bounce_time * 60:
            self.y += self.speedy
            self.speedy += 0.25
        if self.y > self.bounce_y and canbounce and self.speedy != 0 and self.timer > 0:
            sound_player.play_sound(bump_sound)
            self.speedy /= -1.5
            self.y -= 0.25
        if self.timer == self.bounce_time * 60 and self.y > self.bounce_y:
            sound_player.play_sound(bump_sound)
            self.speedy = 0
            self.y = self.bounce_y

    def draw(self):
        screen.blit(self.spritesheet, (self.x, self.y))

class TitleGround:
    def __init__(self):
        self.y = SCREEN_HEIGHT - 24
        self.sprite = load_sprite("ground")

    def draw(self):
        offset_x = -camera.x % 16
        for y in range(2):
            for x in range(0, SCREEN_WIDTH + 32, 16):
                screen.blit(self.sprite, (x + offset_x - 16, self.y + 16 * y - camera.y))

class PowerMeter:
    def __init__(self, player):
        self.frames = [pygame.Rect(0, i * 7, 64, 7) for i in range(8)]
        self.player = player
        self.spritesheet = recolor_surface(load_sprite("powermeter"), [255, 255, 255], self.player.color)
        self.current_frame = 0
        self.frame_swap_timer = 0
        self.swap_state = False

    def update(self):
        if self.player.pspeed:
            self.frame_swap_timer += 1
            if self.frame_swap_timer >= 6:
                self.swap_state = not self.swap_state
                self.frame_swap_timer = 0
            self.current_frame = 7 if self.swap_state else 6
        else:
            self.current_frame = min(int(self.player.run_timer) // int(round(MAX_RUN_TIMER / 7.5)), 7)
            self.frame_swap_timer = 0

    def draw(self):
        screen.blit(self.spritesheet.subsurface(self.frames[self.current_frame]), (48 + 8 * len(str(self.player.lives)), 24 + (self.player.player_number + 1) * 16))

class Score:
    def __init__(self, x, y, points=100):
        self.x, self.y = x, y
        self.frames = [pygame.Rect(0, i * 8, 16, 8) for i in range(9)]
        self.frame_index = {100: 0, 200: 1, 400: 2, 800: 3, 1000: 4, 2000: 5, 4000: 6, 8000: 7, 10000: 8}.get(points, -1)
        self.image = load_sprite("score")
        self.dt = 0
        if not points == 10000:
            globals()["score"] += points

    def update(self):
        self.dt += 1
        if self.dt >= 60:
            overlays.remove(self)

    def draw(self):
        screen.blit(self.image.subsurface(self.frames[self.frame_index]), (self.x, self.y - self.dt))

class CoinAnimation:
    def __init__(self, x, y, **kwargs):
        self.x, self.y = x * 16 + 4, y * 16 - 28
        self.image = load_sprite("coinanim")
        self.sprites = [pygame.Rect(8 * column, 0, 8, 64) for column in range(32)]
        self.dt = 0
        hud.add_coins(1)

    def update(self):
        self.dt += 1
        if self.dt >= 31:
            particles.remove(self)
            overlays.append(Score(self.x - camera.x, self.y - camera.y + 32, 200))

    def draw(self):
        screen.blit(self.image.subsurface(self.sprites[self.dt]), (self.x - camera.x, self.y - camera.y))

class CoinHUD:
    def __init__(self, coins=0):
        self.x, self.y = 16, 16
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
        self.sprites = [[pygame.Rect(x * 16, y * 16, 16, 16) for x in range(2)] for y in range(4)]

    def update(self):
        self.player_number = self.player.player_number + 1
        self.size = max(self.player.size - 1, 0)
        self.star = self.player.star
        self.star_timer = self.player.star_timer
        try:
            self.last_color_index = self.player.last_color_index
            self.time_passed = self.player.time_passed
        except AttributeError:
            pass

    def draw(self):
        try:
            sprite = self.image.subsurface(self.sprites[self.player_number - 1][self.size])
            sprite = pygame.transform.flip(sprite, nitpicks["moonwalking_mario"], False)
            screen.blit(sprite, (12, 20 + self.player_number * 16))

            if self.star:
                star_mask = sprite.copy()
                colors = [
                    (255, 0, 0),
                    (255, 128, 0),
                    (255, 255, 0),
                    (128, 255, 0),
                    (0, 255, 0),
                    (0, 255, 128),
                    (0, 255, 255),
                    (0, 128, 255),
                    (0, 0, 255),
                    (128, 0, 255),
                    (255, 0, 255),
                    (255, 0, 128)
                ]
                cycle_time = 2 if self.star_timer >= 1 else 1

                if pause or everyone_dead:
                    color_index = self.last_color_index if hasattr(player, 'last_color_index') else 0
                else:
                    self.time_passed = pygame.time.get_ticks()
                    color_index = int((self.time_passed % (1250 / cycle_time)) / ((1250 / cycle_time) / len(colors)))
                    self.last_color_index = color_index

                current_color = colors[color_index]
                star_mask.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(star_mask, (12, 20 + self.player_number * 16))
        except AttributeError:
            pass

class Tile:
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False, item=None, item_spawn_anim=True, item_sound=sprout_sound):
        self.x = x * 16
        self.y = y * 16 + 8
        self.og_x, self.og_y = x, y
        self.spriteset = spriteset
        self.img = image
        self.image = load_sprite(image)
        self.img_width, self.img_height = self.image.get_size()
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

        self.broken = False
        
        self.bouncing = False
        self.bounce_timer = 0
        self.bounce_speed = 0
        self.y_offset = 0
        self.can_break_now = False
        self.hit = False
        self.item_spawned = False
        self.item_sound = None if self.item == CoinAnimation else item_sound
        self.player = None
        self.coin_block_timer = 0
        self.coins = 0

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
                    if self.img == "hiddenblock":
                        self.left_collide = True
                        self.right_collide = True
                        self.top_collide = True
                        self.bottom_collide = True
                    if self.item in [Mushroom, FireFlower]:
                        self.item = Mushroom if self.player.size == 0 and not nitpicks["non-progressive_powerups"] else FireFlower
                    if not str(self.item) == "MultiCoin":
                        self.item_spawned = True
                        if self.item == CoinAnimation:
                            particles.append(CoinAnimation(self.og_x, self.og_y - 1, spriteset=self.spriteset, sprout=False))
                        else:
                            items.append(self.item(self.og_x, self.og_y - (0.625 if self.item_spawn_anim else 1), spriteset=self.spriteset, sprout=self.item_spawn_anim))
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

    def break_block(self):
        if self.item is None:
            self.can_break_now = self.breakable
            self.bouncing = True

    def draw(self):
        if 0 <= self.spriteset < self.rows:
            screen.blit(self.image.subsurface(self.sprites[self.spriteset]), (self.x - camera.x, self.y - camera.y + (self.y_offset * (-1 if nitpicks["inverted_block_bounce"] else 1))))

class Ground(Tile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "ground", spriteset)

class HardBlock(Tile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "hardblock", spriteset)

class AnimatedTile(Tile):
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False, item=None, item_spawn_anim=True, item_sound=sprout_sound, anim_speed=1):
        super().__init__(x, y, image, spriteset, left_collide, right_collide, top_collide, bottom_collide, bonk_bounce, breakable, item, item_spawn_anim, item_sound)

        self.cols = self.img_width // self.tile_size
        self.total_frames = self.cols
        self.frame_index = 0
        self.anim_speed = anim_speed

        self.sprites = [[pygame.Rect(col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size) for col in range(self.cols)] for row in range(self.rows)]

    def update(self):
        super().update()
        self.frame_index = int((dt / (60 / self.cols) / self.anim_speed) % self.total_frames)

    def draw(self):
        if 0 <= self.spriteset < self.rows and nor(self.image is None, self.broken):
            screen.blit(
                self.image.subsurface(self.sprites[self.spriteset if not self.hit else 0][self.frame_index if nor(self.broken, self.hit) else 0]),
                (self.x - camera.x, self.y - camera.y + (self.y_offset * (-1 if nitpicks["inverted_block_bounce"] else 1)))
            )

class Brick(AnimatedTile):
    def __init__(self, x, y, item=None, item_spawn_anim=True, spriteset=1, item_sound=sprout_sound):
        super().__init__(x, y, "brick", spriteset, bonk_bounce=True, breakable=True, item=item, item_spawn_anim=item_spawn_anim, item_sound=item_sound)

    def update(self):
        super().update()

class QuestionBlock(AnimatedTile):
    def __init__(self, x, y, item=CoinAnimation, item_spawn_anim=True, spriteset=1, item_sound=sprout_sound):
        super().__init__(x, y, "questionblock", spriteset, bonk_bounce=True, item=item, item_spawn_anim=False if item == CoinAnimation else item_spawn_anim, item_sound=item_sound)

    def update(self):
        super().update()

class HiddenBlock(AnimatedTile):
    def __init__(self, x, y, item=CoinAnimation, item_spawn_anim=True, spriteset=1, item_sound=sprout_sound):
        super().__init__(x, y, "hiddenblock", spriteset, bonk_bounce=True, item=item, item_spawn_anim=False if item == CoinAnimation else item_spawn_anim, item_sound=item_sound, left_collide=False, right_collide=False, top_collide=False)

    def update(self):
        super().update()

class Coin(AnimatedTile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "coin", spriteset=spriteset, anim_speed=0.75)

    def update(self):
        super().update()

        for tile in tiles:
            if tile.rect.colliderect(self.rect.move(0, 16)) and tile.bouncing and tile.top_collide:
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
        self.gravity = 0.25
        self.quad = self.image.subsurface(self.sprites[self.spriteset][0])

    def update(self):
        self.x += self.speedx
        self.y += self.speedy
        self.speedy += self.gravity
        self.sprite = int(self.speedx > 0)
        self.angle -= self.speedx * 2
        self.quad = self.image.subsurface(self.sprites[self.spriteset][self.sprite])
        self.rotated_image = pygame.transform.rotate(self.image.subsurface(self.sprites[self.spriteset][self.sprite]), self.angle)
        if self.y >= SCREEN_HEIGHT + 16:
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
        self.gravity = 0.25
        self.size = 1
        self.sprouting = sprout
        self.sprout_timer = 0
        self.spriteset = spriteset - (0 if sprout else 1)
        self.sprites = [pygame.Rect(0, 16 * i, 16, 16) for i in range(4)]

    def update(self):
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
                        self.speedy = -math.pi if tile.bouncing else 0
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            self.rect.topleft = (self.x, self.y)

    def is_visible(self):
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))
        )
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        screen.blit(self.sprite.subsurface(self.sprites[self.spriteset]), (self.x - camera.x, self.y - camera.y))

class OneUp(Mushroom):
    def __init__(self, x, y, sprout=False, spriteset=1):
        super().__init__(x, y, sprout, spriteset)
        self.lives = 1
        self.sprite = load_sprite("oneup")
        self.sprites = [pygame.Rect(0, 16 * i, 16, 16) for i in range(4)]

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
        self.spriteset = spriteset - (0 if sprout else 1)
        self.sprite = load_sprite("fireflower")
        self.sprites = [[pygame.Rect(i * 16, j * 16, 16, 16) for i in range(4)] for j in range(4)]
        self.speedx = 0
        self.speedy = -0.5 if sprout else 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25
        self.size = 2
        self.frame_index = 0
        self.sprouting = sprout
        self.sprout_timer = 0
        self.dt = 0

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt / 4) % 4)
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
                        self.speedy = -math.pi if tile.bouncing else 0
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

    def is_visible(self):
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))
        )
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        screen.blit(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), (self.x - camera.x, self.y - camera.y))

class Star:
    def __init__(self, x, y, sprout=False, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8 + (8 if sprout else 0)
        self.bounce = 2.5
        self.sprite = load_sprite("star")
        self.speedx = 0 if sprout else 1
        self.speedy = -0.5 if sprout else -self.bounce
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.125
        self.size = 1
        self.sprouting = sprout
        self.sprout_timer = 0
        self.sprites = [[pygame.Rect(16 * i, 16 * j, 16, 16) for i in range(4)] for j in range(4)]
        self.spriteset = spriteset - (0 if sprout else 1)
        self.frame_index = 0
        self.dt = 0

    def update(self):
        self.dt += 1
        self.frame_index = int((self.dt / 4 % 4))
        if self.sprouting:
            self.sprout_timer += 1
            self.y += self.speedy / 2

            if self.sprout_timer >= SPROUT_SPEED * 60:
                self.sprouting = False
                self.speedx = 1
                self.speedy = -self.bounce
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
                        self.speedy = -self.bounce
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            self.rect.topleft = (self.x, self.y)

    def is_visible(self):
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))
        )
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        screen.blit(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), (self.x - camera.x, self.y - camera.y))

class Fireball:
    def __init__(self, player):
        self.x = (player.rect.left + player.rect.right) / 2 - 4
        self.y = player.rect.top
        self.bounce = math.pi
        self.speedx = RUN_SPEED * (1.25 if player.facing_right else -1.25)
        self.speedy = self.bounce * (-1 if player.up else 1)
        self.rect = pygame.Rect(self.x, self.y, 8, 8)
        self.sprite = load_sprite("fireball")
        self.sprites = [[pygame.Rect(i * 16, j * 16, 16, 16) for i in range(4)] for j in range(4)]
        self.spriteset = player.player_number - 1
        self.angle = 0
        self.frame_index = 0
        self.frame_timer = 0
        self.destroyed = False
        self.gravity = 0.5
        self.player = player
        self.dt = 0

    def update(self):
        self.dt += 1
        if self.destroyed:
            self.frame_timer += 1
            self.frame_index = math.floor(min(self.frame_timer / 4, 3))
            if self.frame_timer >= 15:
                [fireballs, fireballs2, fireballs3, fireballs4][self.player.player_number - 1].remove(self)
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
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height and self.y < camera.y + SCREEN_HEIGHT + self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height and self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))
        )

    def draw(self):
        if self.dt > 0:
            screen.blit(pygame.transform.rotate(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), self.angle), (self.x - camera.x, self.y - camera.y - 3))

class Goomba:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.spriteset = spriteset
        self.properties = get_game_property("enemies", "goomba")
        self.sprite = load_sprite("goomba")
        self.total_frames = sum(self.properties["frames"].values())
        self.spr_width, self.spr_height = self.sprite.get_size()
        self.quad_width = self.spr_width // self.total_frames
        self.sprites = [[pygame.Rect(i * self.quad_width, j * self.spr_height // 4, self.quad_width, self.spr_height // 4) for i in range(self.total_frames)] for j in range(4)]
        self.speedx = -math.pi / 4
        self.speedy = 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25
        self.frame_index = 0
        self.stomped = False
        self.shotted = False
        self.angle = 0
        self.dt = 0

    def update(self):
        if self.shotted:
            self.angle -= self.speedx * 4
            self.x += self.speedx
            self.y += self.speedy
            self.speedy += self.gravity
            self.frame_index = self.properties["frames"]["normal"] + int((self.dt * self.properties["frame_speeds"]["shot"]) % self.properties["frames"]["shot"])
            if self.rect.top >= SCREEN_HEIGHT:
                enemies.remove(self)
        else:
            if self.stomped:
                self.frame_index = self.properties["frames"]["normal"] + (self.properties["frames"]["shot"] if key_exists(self.properties["frames"], "shot") else 0) + int((self.dt * self.properties["frame_speeds"]["stomp"]) % self.properties["frames"]["stomp"])
                self.dt += 0.5
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
                            if tile.bouncing:
                                self.shot()
                                overlays.append(Score(self.x - camera.x, self.y - camera.y))
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
                self.frame_index = int((self.dt * self.properties["frame_speeds"]["normal"]) % self.properties["frames"]["normal"])

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
        self.speedx = 2 if self.speedx < 0 else -2
        self.speedy = -math.pi

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
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height))
        )
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        image = pygame.transform.rotate(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), self.angle)
        image = pygame.transform.flip(image, xor((self.speedx > 0 and not self.shotted), nitpicks["moonwalking_enemies"]), False)
        screen.blit(image, (self.x - camera.x, self.y - camera.y + 1))

class Koopa:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.properties = get_game_property("enemies", "koopa")
        self.spriteset = spriteset
        self.sprite = load_sprite("koopa")
        self.total_frames = sum(self.properties["frames"].values())
        self.spr_width, self.spr_height = self.sprite.get_size()
        self.quad_width = self.spr_width // self.total_frames
        self.sprites = [[pygame.Rect(i * self.quad_width, j * self.spr_height // 4, self.quad_width, self.spr_height // 4) for i in range(self.total_frames)] for j in range(4)]
        self.speedx = -math.pi / 4
        self.speedy = 0
        self.shell_speed = 3.75
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25
        self.frame_index = 0
        self.stomped = False
        self.shotted = False
        self.angle = 0
        self.dt = 0
        self.combo = 0

    def update(self):
        if self.shotted:
            self.angle -= self.speedx * 4
            self.speedy += self.gravity
            self.frame_index = int((self.dt * self.properties["frame_speeds"]["shell"]) % self.properties["frames"]["shell"]) if self.properties["shell_death_anim"] else 0
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
                        if tile.bouncing:
                            self.whack_upside_down()
                    elif self.speedy < 0 and tile.bottom_collide:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                    break

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect) and self is not enemy:
                    if self.stomped and self.speedx != 0:
                        enemy.shot(self)
                        overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, [100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000][self.combo]))
                        if self.combo == 8:
                            for player in players:
                                player.lives += 1
                        sound_player.play_sound(shot_sound, self.combo * 2)
                        self.combo = min(self.combo + 1, 8)
                    elif not self.stomped:
                        if self.speedx > 0:
                            self.x = enemy.rect.left - self.rect.width
                        elif self.speedx < 0:
                            self.x = enemy.rect.right
                        self.speedx *= -1
                    break

            self.rect.topleft = (self.x, self.y)

            self.frame_index = int((self.dt * (abs(self.speedx) if self.stomped else 1) * self.properties["frame_speeds"]["shell" if self.stomped else "normal"]) % self.properties["frames"]["shell" if self.stomped else "normal"])

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
        self.speedx = 2 if self.speedx < 0 else -2
        self.speedy = -math.pi

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
        return (
            ((self.x > camera.x - self.rect.width and self.x < camera.x + SCREEN_WIDTH + self.rect.width) or
            (self.x + self.rect.width > camera.x - self.rect.width and self.x + self.rect.width < camera.x + SCREEN_WIDTH + self.rect.width)) and
            ((self.y > camera.y - self.rect.height) or
            (self.y + self.rect.height > camera.y - self.rect.height))
        )
    
    def below_camera(self):
        return nor((self.y < camera.y + SCREEN_HEIGHT + self.rect.height), (self.y + self.rect.height < camera.y + SCREEN_HEIGHT + self.rect.height))

    def draw(self):
        image = pygame.transform.rotate(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index + (2 if self.stomped or self.shotted else 0)]), self.angle)
        image = pygame.transform.flip(image, xor((self.speedx > 0 and not self.shotted), nitpicks["moonwalking_enemies"]), False)
        screen.blit(image, (self.x - camera.x, self.y - camera.y + ((16 - self.properties["quadcentery"]) * math.cos(math.radians(self.angle)))))

class Castle:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 - 56
        self.spriteset = spriteset
        self.image = load_sprite("castle")
        self.sprites = [pygame.Rect(0, 80 * i, 80, 80) for i in range(4)]

    def draw(self):
        screen.blit(self.image.subsurface(self.sprites[self.spriteset]), (self.x - camera.x, self.y - camera.y))

class Player:
    def __init__(self, x, y, lives=3, size=0, controls_enabled=True, walk_cutscene=False, player_number=1):
        self.properties = get_game_property("character_properties")
        self.character_data = self.properties["character_data"][player_number]
        self.frame_group = self.character_data["frames"]
        self.frame_loops = self.character_data["frame_loops"]
        self.frame_speeds = self.character_data["frame_speeds"]
        self.frame_data = {}
        self.prev_key = 0
        for key in ["idle", "crouch", "crouchfall", "walk", "skid", "jump", "fall", "run", "runjump", "runfall", "fire", "pipe", "climb"]:
            self.frame_data[key] = self.frame_group[key] + self.prev_key
            self.prev_key = self.frame_data[key]
        self.acceleration = self.character_data["acceleration"]
        self.max_jump = self.character_data["max_jump"]
        self.color = self.character_data["color"]
        self.death_anim = self.properties["pre_death_anim_jump"]
        self.sync_crouch = self.properties["sync_crouch_fall_anim"]
        self.midair_turn = self.properties["midair_turn"]
        self.quad_width, self.quad_height = self.properties["quad_width"], self.properties["quad_height"]
        self.spritesheet = load_sprite(f"p{player_number + 1}")
        self.controls_enabled = controls_enabled
        self.can_control = controls_enabled
        self.player_number = player_number
        self.speedx = 0
        self.speedy = 0
        self.jump_speedx = 0
        self.frame_timer = 0
        self.on_ground = False
        self.facing_right = True
        self.crouch_timer = 0
        self.crouch_fall_timer = 0
        self.pipe_timer = 0
        self.skid_timer = 0
        self.idle_timer = 0
        self.jumping_timer = 0
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
        self.run_lock = False
        self.img_width, self.img_height = self.spritesheet.get_size()
        self.rect = pygame.Rect(x, y, self.img_width, self.img_height)
        self.sprites = [
            [
                pygame.Rect(
                x * self.quad_width,
                y * self.quad_height,
                self.quad_width,
                self.quad_height
                )
            for x in range(self.img_width // self.quad_width)
            ]
            for y in range(self.img_height // self.quad_height)
        ]
        self.size = size
        self.walk_cutscene = walk_cutscene
        self.controls = [controls, controls2, controls3, controls4][player_number]
        self.skidding = False
        self.gravity = 0.25
        self.min_jump = 1
        self.run_timer = 0
        self.update_hitbox()
        self.rect.y -= self.rect.height - (0 if self.size == 0 else 12)
        self.fall_timer = 0
        self.fall_duration = 0.125
        self.falling = True
        self.pspeed = False
        self.player_number = player_number
        self.size_change = []
        self.size_change_timer = 0
        self.old_controls = False
        self.fire_timer = 0
        self.fire_duration = 10
        self.fire_lock = False
        self.speed = 0
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
        self.star = False
        self.star_timer = 0
        self.star_combo = 0
        self.star_music = False
        self.piping = False
        self.pipe_dir = False
        self.pipe_timer = 0
        self.pipe_speed = 0.5
        self.pipe_marker = None
        self.clear = False
        self.kicked_shell = False
        self.kicked_timer = 0
        self.update_hitbox()

    def add_life(self):
        if nitpicks["infinite_lives"]:
            for player in players:
                player.lives += 1
        else:
            self.lives += 1
        if not sound_player.is_playing(oneup_sound):
            sound_player.play_sound(oneup_sound)

    def update_hitbox(self):
        prev_bottom = self.rect.bottom
        new_width, new_height = (12, 8 if self.size == 0 else 16) if self.down else (12, 16 if self.size == 0 else 24)
        self.rect.width, self.rect.height = new_width, new_height
        self.rect.bottom = prev_bottom

    def update(self):
        if self.dead:
            if self.dead_timer == 0:
                self.frame_timer = 0
                self.size = 0
                self.piping = False
                self.run_timer = 0
                self.pspeed = False
                self.star = False
                self.star_timer = 0
                self.star_combo = 0
                self.star_music = False
                if not nitpicks["infinite_lives"]:
                    self.lives -= 1
                self.all_dead = everyone_dead
                if everyone_dead:
                    bgm_player.stop_music()
                    sound_player.stop_all_sounds()
                sound_player.play_sound(dead_sound)
            self.dead_timer += 1
            if self.dead_timer >= 30:
                if not self.dead_music:
                    self.speedy = self.dead_speed
                    if self.all_dead:
                        bgm_player.play_music(dead_music)
                self.speedy += self.gravity / 2
                self.rect.y += self.speedy
                self.dead_music = True
                if self.dead_timer >= 150 and self.lives > 0 and not everyone_dead:
                    furthest_player = max([player for player in players if not player.dead], key=lambda player: player.rect.x)
                    self.rect.x = furthest_player.rect.x
                    self.rect.bottom = furthest_player.rect.bottom
                    self.speedx = 0
                    self.speedy = 0
                    self.fall_timer = 0 if furthest_player.fall_timer < furthest_player.fall_duration else self.fall_duration
                    self.jump_timer = 0 if furthest_player.fall_timer < furthest_player.fall_duration else 1
                    self.shrunk = True
                    self.anim_state = 0
                    self.dead_timer = 0
                    self.dead_music = False
                    self.dead = False
        else:
            self.left = (keys[self.controls["left"]]) if self.controls_enabled and self.can_control and not self.piping else False
            self.right = (keys[self.controls["right"]]) if self.controls_enabled and self.can_control and not self.piping else False
            self.up = (keys[self.controls["up"]]) if self.controls_enabled and self.can_control and not self.piping else False
            self.down = (keys[self.controls["down"]] if self.fall_timer < self.fall_duration else self.down) if self.controls_enabled and self.can_control and not self.piping else False
            self.down_key = (keys[self.controls["down"]]) if self.controls_enabled and self.can_control and not self.piping else False
            self.run = (keys[self.controls["run"]]) if self.controls_enabled and self.can_control and not self.piping else False
            self.jump = (keys[self.controls["jump"]]) if self.controls_enabled and self.can_control and not self.piping else False

            if self.kicked_shell:
                self.kicked_timer += 1
                if self.kicked_timer >= 20:
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
                if self.rect.colliderect(pipe_marker.rect) and nor(self.piping, self.dead, self.size_change):
                    if self.down_key and self.rect.bottom + 2 >= pipe_marker.rect.top >= self.rect.bottom - 2 and pipe_marker.rect.left - 5 <= self.rect.x <= pipe_marker.rect.right - 9 and pipe_marker.pipe_dir == "up":
                        self.speedx = 0
                        self.speedy = self.pipe_speed
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and player.pipe_marker != pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.up and self.rect.top + 2 >= pipe_marker.rect.bottom >= self.rect.top - 2 and pipe_marker.rect.left - 5 <= self.rect.x <= pipe_marker.rect.right - 9 and pipe_marker.pipe_dir == "down":
                        self.speedx = 0
                        self.speedy = -self.pipe_speed
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and player.pipe_marker != pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.right and self.rect.right - 2 <= pipe_marker.rect.left <= self.rect.right + 2 and self.fall_timer < self.fall_duration and pipe_marker.pipe_dir == "left":
                        self.speedx = self.pipe_speed
                        self.speedy = 0
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and player.pipe_marker != pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

                    elif self.left and self.rect.left - 2 <= pipe_marker.rect.right <= self.rect.left + 2 and self.fall_timer < self.fall_duration and pipe_marker.pipe_dir == "right":
                        self.speedx = -self.pipe_speed
                        self.speedy = 0
                        if self.pipe_marker is None:
                            if any(player.pipe_marker is not None and player.pipe_marker != pipe_marker for player in players):
                                continue
                            self.pipe_marker = pipe_marker
                            self.piping = True
                            sound_player.play_sound(pipe_sound)

            if self.piping:
                self.pipe_timer = min(self.pipe_timer + 1, 60)
                if self.pipe_timer <= 60:
                    self.rect.x += self.speedx
                    self.rect.y += self.speedy
                if abs(self.speedx) < MIN_SPEEDX:
                    self.anim_state = self.frame_data["fire"] + ((int(self.pipe_timer * self.frame_speeds["pipe"]) % self.frame_group["pipe"]) if self.frame_loops["pipe"] else min(int(self.pipe_timer * self.frame_speeds["pipe"]), self.frame_group["pipe"] + 1))
                else:
                    self.frame_timer += abs(self.speedx) / 1.25
                    self.anim_state = self.frame_data["crouchfall"] + ((int(self.frame_timer * self.frame_speeds["walk"]) % self.frame_group["walk"]) if self.frame_loops["walk"] else min(int(self.frame_timer * self.frame_speeds["walk"]), self.frame_group["walk"] - 1))
                return

            if self.on_ground:
                self.speed = (RUN_SPEED * (1.25 if self.pspeed else 1) if self.run else WALK_SPEED) * (1.25 if self.star else 1)
            else:
                if not self.run and abs(self.speedx) > WALK_SPEED:
                    self.speedx -= self.acceleration if self.speedx > 0 else -self.acceleration
                    if abs(self.speedx) < WALK_SPEED:
                        self.speedx = WALK_SPEED if self.speedx > 0 else -WALK_SPEED

            self.run_lock = self.run and not self.prev_run

            if self.size == 2 and len([fireballs, fireballs2, fireballs3, fireballs4][self.player_number - 1]) < max_fireballs and not self.down:
                if self.run:
                    if self.fire_timer < self.fire_duration:
                        if self.fire_timer == 0:
                            sound_player.play_sound(fireball_sound)
                            [fireballs, fireballs2, fireballs3, fireballs4][self.player_number - 1].append(Fireball(self))
                        self.fire_timer += 1
                        if self.fire_timer == self.fire_duration:
                            self.fire_lock = True
                elif not self.run:
                    if 0 < self.fire_timer < self.fire_duration:
                        self.fire_timer += 1
                    else:
                        self.fire_timer = 0
                        self.fire_lock = False
                elif self.fire_timer == self.fire_duration:
                    self.fire_timer = 0
                    self.fire_lock = False
            else:
                self.fire_timer = self.fire_duration

            if not self.size_change:
                self.update_hitbox()

            if self.fall_timer < self.fall_duration:
                if self.down:
                    self.speedx *= (1 - self.acceleration)
                else:
                    if self.left and not self.right:
                        self.speedx = max(self.speedx - self.acceleration, -self.speed)
                        self.facing_right = False
                    elif self.right and not self.left:
                        self.speedx = min(self.speedx + self.acceleration, self.speed)
                        self.facing_right = True
                    else:
                        if not self.walk_cutscene:
                            self.speedx *= (1 - self.acceleration)
                            if abs(self.speedx) < MIN_SPEEDX:
                                self.speedx = 0
            else:
                if self.left and not self.right:
                    self.speedx = max(self.speedx - self.acceleration, -self.speed)
                    if self.midair_turn:
                        self.facing_right = False
                elif self.right and not self.left:
                    self.speedx = min(self.speedx + self.acceleration, self.speed)
                    if self.midair_turn:
                        self.facing_right = True

            if self.fall_timer < self.fall_duration and self.jump and not self.jump and self.jump_timer == 0:
                self.speedy = -self.min_jump
                self.jump_timer = 1
            elif self.jump and 0 < self.jump_timer < JUMP_HOLD_TIME:
                if self.jump_timer == 1:
                    self.fall_timer = self.fall_duration
                    self.jump_speedx = 1 if self.stomp_jump else abs(self.speedx)
                    if not self.stomp_jump:
                        sound_player.play_sound(jump_sound if self.size == 0 else jumpbig_sound)
                self.max_speedx_jump = (self.max_jump + (2 if self.pspeed else 1) / 2) if self.jump_speedx >= 1 else self.max_jump
                self.speedy = max(self.speedy - self.max_speedx_jump, -self.max_speedx_jump)
                self.jump_timer += 1
            elif not self.jump:
                self.jump_timer = 1 if self.fall_timer < self.fall_duration else 0

            self.pspeed = self.run_timer >= MAX_RUN_TIMER

            if self.fall_timer < self.fall_duration:
                self.stomp_jump = False
                self.stomp_combo = False

            if self.can_control:
                if self.fall_timer < self.fall_duration and self.controls_enabled:
                    if abs(self.speedx) >= RUN_SPEED:
                        self.run_timer = range_number(self.run_timer + (3 if self.star else 1), MIN_RUN_TIMER, MAX_RUN_TIMER)
                    else:
                        self.run_timer = range_number(self.run_timer - (3 if self.star else 0.5), MIN_RUN_TIMER, MAX_RUN_TIMER)
                elif not self.run_timer == MAX_RUN_TIMER:
                    self.run_timer = range_number(self.run_timer - (3 if self.star else 0.5), MIN_RUN_TIMER, MAX_RUN_TIMER)

            if self.rect.left <= camera.x:
                self.rect.left = camera.x
                if self.rect.x <= camera.x and ((self.speedx < 0 and not self.facing_right) or (self.speedx < 0 and self.facing_right)):
                    self.speedx = 0

            if self.rect.right >= camera.x + SCREEN_WIDTH:
                self.rect.right = camera.x + SCREEN_WIDTH
                if self.rect.x >= camera.x + SCREEN_WIDTH - self.rect.width and ((self.speedx > 0 and self.facing_right) or (self.speedx > 0 and not self.facing_right)):
                    self.speedx = 0

            if self.rect.top < camera.y:
                self.rect.top = camera.y
                self.speedy = 0
                self.jump_timer = 0

            new_rect = self.rect.copy()
            new_rect.x += self.speedx

            for tile in tiles:
                if tile.broken:
                    continue
                if new_rect.colliderect(tile.rect):
                    if self.speedx > 0 and tile.left_collide:
                        self.rect.right = tile.rect.left
                        self.speedx = 0
                    elif self.speedx < 0 and tile.right_collide:
                        self.rect.left = tile.rect.right
                        self.speedx = 0
                    break

            self.rect.x += self.speedx
            self.rect.y += self.speedy
            self.on_ground = False

            self.rect.x = range_number(self.rect.x, 0, camera.x + SCREEN_WIDTH)
            self.speedy = min(self.speedy, 5)

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
                        elif self.speedy < 0 and self.rect.top <= tile.rect.bottom and tile.bottom_collide:
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
                                    tile.bouncing = True
                                    tile.bounce_speed = -1
                                    tile.y_offset = 0
                                    tile.player = self
                                if not self.size == 0:
                                    tile.break_block()
                                if str(tile.item) == "MultiCoin":
                                    tile.coins += 1
                                    tile.item_spawned = tile.coin_block_timer >= 5 or tile.coins >= 10
                                    particles.append(CoinAnimation(tile.og_x, tile.og_y - 1, spriteset=tile.spriteset, sprout=False))

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect) and not self.size_change:
                    if self.star:
                        enemy.shot(self)
                        overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, [100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000][self.star_combo]))
                        if self.star_combo == 8:
                            self.add_life()
                        sound_player.play_sound(shot_sound, self.star_combo * 2)
                        self.star_combo = min(self.star_combo + 1, 8)
                    else:
                        if isinstance(enemy, Koopa):
                            if self.speedy > 0 and self.rect.bottom - enemy.rect.top < 8:
                                if not enemy.stomped:
                                    enemy.stomp()
                                    overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, [100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000][self.stomp_combo]))
                                    if self.stomp_combo == 8:
                                        self.add_life()
                                    sound_player.play_sound(stomp_sound, self.stomp_combo)
                                    self.stomp_combo = min(self.stomp_combo + 1, 8)
                                    self.stomp_jump = True
                                    self.speedy = -self.max_jump
                                    self.jump_timer = 1
                                    self.on_ground = False
                                    self.fall_timer = self.fall_duration

                                elif enemy.speedx == 0:
                                    self.kicked_shell = True
                                    if self.rect.centerx < enemy.rect.centerx:
                                        enemy.speedx = enemy.shell_speed
                                    else:
                                        enemy.speedx = -enemy.shell_speed
                                    overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y))
                                    sound_player.play_sound(shot_sound)

                                elif not self.kicked_shell:
                                    if self.rect.right > enemy.rect.left and self.rect.left < enemy.rect.right:
                                        if self.speedy > 0 and self.rect.bottom - enemy.rect.top < 8:
                                            enemy.stomp()
                                            overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, [100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000][self.stomp_combo]))
                                            if self.stomp_combo == 8:
                                                self.add_life()
                                            sound_player.play_sound(stomp_sound, self.stomp_combo)
                                            self.stomp_combo = min(self.stomp_combo + 1, 8)
                                            self.stomp_jump = True
                                            self.speedy = -self.max_jump
                                            self.jump_timer = 1
                                            self.on_ground = False
                                            self.fall_timer = self.fall_duration
                                        elif not self.shrunk:
                                            if self.size == 0:
                                                self.dead_speed = -5
                                                self.dead = True
                                            else:
                                                self.shrunk = True
                                                target_size = 0 if nitpicks["classic_powerdown"] else self.size - 1
                                                self.size_change_timer = 0
                                                self.size_change = [target_size, self.size, target_size, self.size, target_size, self.size, target_size]
                                                sound_player.play_sound(pipe_sound)

                            elif self.on_ground:
                                if self.rect.right > enemy.rect.left and self.rect.left < enemy.rect.right:
                                    if enemy.speedx == 0:
                                        if self.rect.centerx < enemy.rect.centerx:
                                            enemy.speedx = enemy.shell_speed + (self.speedx * 0.25)
                                        else:
                                            enemy.speedx = -(enemy.shell_speed + (self.speedx * 0.25))
                                        overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y))
                                        sound_player.play_sound(shot_sound)
                                    else:
                                        if not self.shrunk:
                                            if self.size == 0:
                                                self.dead_speed = -5
                                                self.dead = True
                                            else:
                                                self.shrunk = True
                                                target_size = 0 if nitpicks["classic_powerdown"] else self.size - 1
                                                self.size_change_timer = 0
                                                self.size_change = [target_size, self.size, target_size, self.size, target_size, self.size, target_size]
                                                sound_player.play_sound(pipe_sound)

                            elif self.speedy < 0 and self.rect.top - enemy.rect.bottom < 8 and enemy.speedx == 0:
                                self.kicked_shell = True
                                if self.rect.centerx < enemy.rect.centerx:
                                    enemy.speedx = enemy.shell_speed
                                else:
                                    enemy.speedx = -enemy.shell_speed
                                overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y))
                                sound_player.play_sound(shot_sound)

                        elif isinstance(enemy, Goomba) and self.speedy > 0 and self.rect.bottom - enemy.rect.top < 8:
                            enemy.stomp()
                            self.stomp_jump = True
                            self.speedy = -self.max_jump
                            self.jump_timer = 1
                            self.on_ground = False
                            self.fall_timer = self.fall_duration
                            overlays.append(Score(self.rect.x - camera.x, self.rect.y - camera.y, [100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000][self.stomp_combo]))
                            if self.stomp_combo == 8:
                                self.add_life()
                            sound_player.play_sound(stomp_sound, self.stomp_combo)
                            self.stomp_combo = min(self.stomp_combo + 1, 8)

                        elif not self.shrunk:
                            if self.size == 0:
                                self.dead_speed = -5
                                self.dead = True
                            else:
                                self.shrunk = True
                                target_size = 0 if nitpicks["classic_powerdown"] else self.size - 1
                                self.size_change_timer = 0
                                self.size_change = [target_size, self.size, target_size, self.size, target_size, self.size, target_size]
                                sound_player.play_sound(pipe_sound)

            for item in items:
                if not isinstance(item, CoinAnimation):
                    if isinstance(item, OneUp):
                        if self.rect.colliderect(item.rect) and not item.sprouting:
                            overlays.append(Score(item.x - camera.x, item.y - camera.y, 10000))
                            self.add_life()
                            items.remove(item)
                            sound_player.play_sound(oneup_sound)
                    elif isinstance(item, Star):
                        if self.rect.colliderect(item.rect) and not item.sprouting:
                            overlays.append(Score(item.x - camera.x, item.y - camera.y, 1000))
                            self.star = True
                            self.star_timer = 12
                            items.remove(item)
                            sound_player.play_sound(powerup_sound)
                    else:
                        if self.rect.colliderect(item.rect) and not item.sprouting:
                            overlays.append(Score(item.x - camera.x, item.y - camera.y, 1000))
                            if nand((isinstance(item, Mushroom) and self.size != 0), (isinstance(item, (Mushroom, FireFlower)) and self.size == 2)):
                                if self.size != item.size:
                                    old_size = self.size
                                    self.size_change_timer = 0
                                    self.size_change = [item.size, old_size, item.size, old_size, item.size, old_size, item.size]

                            items.remove(item)
                            sound_player.play_sound(powerup_sound)

            self.star_timer = (self.star_timer - 1/60) if self.star else 0
            if self.star and self.star_timer <= 0:
                    self.star_timer = 0
                    self.star = False

            self.rect.y = max(self.rect.y, camera.y)

            if self.rect.top >= SCREEN_HEIGHT + self.rect.height + 16:
                self.dead = True
                self.dead_speed = 0

            self.skidding = (self.fall_timer < self.fall_duration and ((self.speedx < 0 and self.facing_right) or (self.speedx > 0 and not self.facing_right)) and nor(self.down, 1 <= self.anim_state <= self.frame_data["idle"]))

            if self.on_ground:
                self.speedy = 0
                self.fall_timer = 0
                self.falling = True
            else:
                self.speedy += self.gravity
                self.fall_timer += 0.025
                if not self.falling:
                    self.falling = True
                    self.fall_timer = 0

            self.prev_run = self.run

        self.falling_condition = self.speedy > 0 and self.fall_timer >= self.fall_duration

        self.crouch_timer = (self.crouch_timer + 1) if self.down and (self.sync_crouch and not self.falling_condition) else 0
        self.crouch_fall_timer = (self.crouch_fall_timer + 1) if self.down and self.falling_condition else 0
        self.pipe_timer = (self.pipe_timer + 1) if self.piping else 0
        self.skid_timer = (self.skid_timer + 1) if self.skidding else 0
        self.jumping_timer = (self.jumping_timer + 1) if self.speedy < 0 else 0
        self.idle_timer = (self.idle_timer + 1) if abs(self.speedx) < MIN_SPEEDX else 0

        if self.down:
            self.anim_state = self.frame_data["crouch" if self.falling_condition else "idle"] + ((int(((self.crouch_fall_timer if self.falling_condition else self.crouch_timer) if self.sync_crouch else self.crouch_timer) * self.frame_speeds["crouchfall" if self.falling_condition else "crouch"]) % self.frame_group["crouchfall" if self.falling_condition else "crouch"]) if self.frame_loops["crouchfall" if self.falling_condition else "crouch"] else min(int(((self.crouch_fall_timer if self.falling_condition else self.crouch_timer) if self.sync_crouch else self.crouch_timer) * self.frame_speeds["crouchfall" if self.falling_condition else "crouch"]), self.frame_group["crouchfall" if self.falling_condition else "crouch"] - 1))
            self.frame_timer = 0
        elif self.dead:
            self.frame_timer += 1 if self.dead_timer >= 30 and not self.death_anim else 0
            self.anim_state = self.frame_data["runfall"] + ((int(self.frame_timer * self.frame_speeds["dead"]) % self.frame_group["dead"]) if self.frame_loops["dead"] else min(int(self.frame_timer * self.frame_speeds["dead"]), self.frame_group["dead"] - 1))
        elif self.size == 2 and 0 < self.fire_timer < self.fire_duration and not self.fire_lock:
            self.anim_state = self.frame_data["climb"] + int((self.fire_timer * self.frame_group["fire"]) / self.fire_duration)
            self.frame_timer = 0
        elif self.skidding:
            self.anim_state = self.frame_data["walk"] + ((int(self.skid_timer * self.frame_speeds["skid"]) % self.frame_group["skid"]) if self.frame_loops["skid"] else min(int(self.skid_timer * self.frame_speeds["skid"]), self.frame_group["skid"] - 1))
            self.frame_timer = 0
        elif self.speedy < 0:
            self.anim_state = self.frame_data["run" if self.pspeed else "skid"] + ((int(self.jumping_timer * self.frame_speeds["runjump" if self.pspeed else "jump"]) % self.frame_group["runjump" if self.pspeed else "jump"]) if self.frame_loops["runjump" if self.pspeed else "jump"] else min(int(self.jumping_timer * self.frame_speeds["runjump" if self.pspeed else "jump"]), self.frame_group["runjump" if self.pspeed else "jump"] - 1))
            self.frame_timer = 0
        elif self.speedy > 0 and self.fall_timer >= self.fall_duration and nor(self.on_ground, self.down):
            self.anim_state = self.frame_data["runjump" if self.pspeed else "jump"] + ((int(self.fall_timer * self.frame_speeds["runfall" if self.pspeed else "fall"]) % self.frame_group["runfall" if self.pspeed else "fall"]) if self.frame_loops["runfall" if self.pspeed else "fall"] else min(int(self.fall_timer * self.frame_speeds["runfall" if self.pspeed else "fall"]), self.frame_group["runfall" if self.pspeed else "fall"] - 1))
            self.frame_timer = 0
        elif abs(self.speedx) < MIN_SPEEDX and self.on_ground:
            self.anim_state = (int(self.idle_timer * self.frame_speeds["idle"]) % self.frame_group["idle"]) if self.frame_loops["idle"] else min(int(self.idle_timer * self.frame_speeds["idle"]), self.frame_group["idle"] - 1)
            self.frame_timer = 0
        elif abs(self.speedx) > MIN_SPEEDX * 2 and self.fall_timer < self.fall_duration and not self.pspeed:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = self.frame_data["crouchfall"] + ((int(self.frame_timer * self.frame_speeds["walk"]) % self.frame_group["walk"]) if self.frame_loops["walk"] else min(int(self.frame_timer * self.frame_speeds["walk"]), self.frame_group["walk"] - 1))
        elif self.pspeed and self.fall_timer < self.fall_duration:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = self.frame_data["fall"] + ((int(self.frame_timer * self.frame_speeds["run"]) % self.frame_group["run"]) if self.frame_loops["run"] else min(int(self.frame_timer * self.frame_speeds["run"]), self.frame_group["run"] - 1))

    def draw(self):
        if self.can_draw:
            sprite = self.spritesheet.subsurface(self.sprites[self.size][self.anim_state])
            sprite = pygame.transform.flip(sprite, xor((not self.facing_right), nitpicks["moonwalking_mario"]), False)
            draw_x = self.rect.x - camera.x - 4
            draw_y = self.rect.y - camera.y + self.rect.height - 34
            screen.blit(sprite, (draw_x, draw_y))

            if self.star:
                star_mask = sprite.copy()
                colors = [
                    (255, 0, 0),
                    (255, 128, 0),
                    (255, 255, 0),
                    (128, 255, 0),
                    (0, 255, 0),
                    (0, 255, 128),
                    (0, 255, 255),
                    (0, 128, 255),
                    (0, 0, 255),
                    (128, 0, 255),
                    (255, 0, 255),
                    (255, 0, 128)
                ]
                cycle_time = 2 if self.star_timer >= 1 else 1

                if pause:
                    color_index = self.last_color_index if hasattr(self, 'last_color_index') else 0
                else:
                    self.time_passed = pygame.time.get_ticks()
                    color_index = int((self.time_passed % (1250 / cycle_time)) / ((1250 / cycle_time) / len(colors)))
                    self.last_color_index = color_index

                current_color = colors[color_index]
                star_mask.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(star_mask, (draw_x, draw_y))

mus_vol = 1
snd_vol = 1
controls = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "run": pygame.K_z,
    "jump": pygame.K_x,
    "pause": pygame.K_RETURN
}
controls2 = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "run": pygame.K_c,
    "jump": pygame.K_v,
    "pause": pygame.K_p
}
controls3 = {
    "up": pygame.K_i,
    "down": pygame.K_j,
    "left": pygame.K_k,
    "right": pygame.K_l,
    "run": pygame.K_m,
    "jump": pygame.K_n,
    "pause": pygame.K_o
}
controls4 = {
    "up": pygame.K_HOME,
    "down": pygame.K_END,
    "left": pygame.K_DELETE,
    "right": pygame.K_PAGEDOWN,
    "run": pygame.K_INSERT,
    "jump": pygame.K_PAGEUP,
    "pause": pygame.K_BREAK
}
fullscreen = False

if exists(load_local_file("settings.json")) and not getsize(load_local_file("settings.json")) == 0:
    data = load_json("settings")
    mus_vol = data["mus_vol"]
    snd_vol = data["snd_vol"]
    controls = data["controls"]
    controls2 = data["controls2"]
    controls3 = data["controls3"]
    controls4 = data["controls4"]
    fullscreen = data["fullscreen"]

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
    "non-progressive_powerups"
]

if exists(load_local_file("nitpicks.json")):
    data = load_json("nitpicks")
        
    for key in nitpicks_list:
        if key not in data:
            data[key] = False
    
with open(load_local_file("nitpicks.json"), "w") as nitpicks:
    json.dump(data if exists(load_local_file("nitpicks.json")) else {key: False for key in nitpicks_list}, nitpicks, indent=4)

nitpicks = load_json("nitpicks")
music_table = get_game_property("loop_points")
background_layers = get_game_property("background_layers")

running = True
centerx = SCREEN_WIDTH / 2
centery = SCREEN_HEIGHT / 2
characters_data = get_game_property("character_properties", "character_data")
characters_name = [char["name"] for char in characters_data]
characters_color = [char["color"] for char in characters_data]
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
clock = pygame.time.Clock()
pygame.display.set_icon(pygame.image.load(load_asset("icon.ico")))
pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})" if nitpicks["show_fps"] else "Super Mario Bros. for Python")
player_dist = 20
intro_players = [Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, controls_enabled=False, size=1, player_number=i) for i in count_list_items(characters_name)]
camera = Camera()
bgm_player = BGMPlayer()
sound_player = SFXPlayer()
title_ground = TitleGround()
background_manager = Background()
text = Text()
logo = Logo()
tiles = []
pipe_markers = []
items = []
enemies = []
fireballs = []
fireballs2 = []
fireballs3 = []
fireballs4 = []
debris = []
power_meters = []
particles = []
overlays = []
player_lives = []
players_hud = []
world = 0
course = 0
lives = 3
score = 0
time = 0
pipe_wait_timer = 0
castle = None
x_range = None
spawnposx = None
spawnposy = None
main_music = None
star_music = None
dead_music = None
clear_music = None
hud = None
fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
a = 255
fade_in = False
fade_out = False

selected_menu_index = 0
pause_menu_index = 0
old_selected_menu_index = 0
old_pause_menu_index = 0
old_mus_vol = mus_vol
old_snd_vol = snd_vol
pipe_timer = 5
dt = 0
menu_area = 1
menu = True
title = True
bind_table = ["up", "down", "left", "right", "run", "jump", "pause"]
binding_key = False
current_bind = False
game_ready = False
exit_ready = False
game = False
everyone_dead = False
numerical_change = 0.05
pause = False
coins = 0
max_fireballs = infinity if nitpicks["infinite_fireballs"] else 2
game_over = False
fast_music = False

while running:
    bgm_player.set_volume(mus_vol)
    sound_player.set_volume(snd_vol)
    SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
    pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})" if nitpicks["show_fps"] else "Super Mario Bros. for Python")
    current_fps = FPS if clock.get_fps() == 0 else clock.get_fps()
    screen.fill((0, 0, 0))
    keys = pygame.key.get_pressed()
    
    controls_table = [controls, controls2, controls3, controls4]

    mus_vol = round(range_number(mus_vol, 0, 1) * (1 / numerical_change)) / (1 / numerical_change)
    snd_vol = round(range_number(snd_vol, 0, 1) * (1 / numerical_change)) / (1 / numerical_change)
    if nand(old_mus_vol == mus_vol, old_snd_vol == snd_vol):
        sound_player.play_sound(beep_sound)
    old_mus_vol = mus_vol
    old_snd_vol = snd_vol

    with open(load_local_file("settings.json"), "w") as settings:
        json.dump(
            {
                "mus_vol": mus_vol,
                "snd_vol": snd_vol,
                "controls": controls,
                "controls2": controls2,
                "controls3": controls3,
                "controls4": controls4,
                "fullscreen": fullscreen
            }, settings, indent=4)

    if fade_in:
        fade_out = False
        a += 255 / FADE_DURATION
        if a >= 255:
            a = 255
            fade_in = False
            if exit_ready:
                running = False
                menu = False
                title = False
                fade_in = False
                fade_out = False
                binding_key = False
                current_bind = False
            elif game_ready:
                menu = False
                game = True
                game_ready = False
                everyone_dead = False
                game_over = False
                fast_music = False
                fade_out = True
                intro_players = None
                logo = None
                title_ground = None
                castle = None
                dt = 0
                time = 0
                pipe_wait_timer = 0
                players = []
                power_meters = []
                tiles = []
                pipe_markers = []
                items = []
                enemies = []
                fireballs = []
                fireballs2 = []
                fireballs3 = []
                fireballs4 = []
                debris = []
                particles = []
                overlays = []
                player_lives = []
                hud = CoinHUD()
                course += 1
                while not exists(load_local_file(f"courses/{world}-{course}.json")):
                    course = 1
                    world += 1
                create_course(load_json(f"courses/{world}-{course}"))
                if time > 100:
                    bgm_player.play_music(main_music)
                for i in range(player_count):
                    players.append(Player(x=spawnposx + i * 8, y=spawnposy, player_number=i, lives=lives))
                    power_meters.append(PowerMeter(players[i]))
                    players_hud.append(PlayerHUD(players[i]))
            elif everyone_dead:
                if all(player.lives == 0 for player in players):
                    fade_out = True
                    game_over = True
                    game = False
                    bgm_player.play_music("gameover")
                    world = 0
                    course = 0
                    dt = 0
                    pipe_wait_timer = 0
                else:
                    fade_out = True
                    everyone_dead = False
                    game_over = False
                    fast_music = False
                    game = True
                    castle = None
                    dt = 0
                    time = 0
                    players = []
                    power_meters = []
                    tiles = []
                    pipe_markers = []
                    items = []
                    enemies = []
                    fireballs = []
                    fireballs2 = []
                    fireballs3 = []
                    fireballs4 = []
                    debris = []
                    particles = []
                    overlays = []
                    create_course(load_json(f"courses/{world}-{course}"))
                    if time > 100:
                        bgm_player.play_music(main_music)
                    for i in range(player_count):
                        if player_lives[i] == 0:
                            player_lives[i] = 3
                        players.append(Player(x=spawnposx + i * 8, y=spawnposy, player_number=i, lives=player_lives[i]))
                        power_meters.append(PowerMeter(players[i]))
                        players_hud.append(PlayerHUD(players[i]))

    elif fade_out:
        fade_in = False
        a -= 255 / FADE_DURATION
        if a <= 0:
            a = 0
            fade_out = False

    if menu:
        title_screen = [
            [
                ["1 player game", 0.75],
                ["2 player game", 0.875],
                ["3 player game", 1],
                ["4 player game", 1.125],
                ["options", 1.25],
                ["quit", 1.375]
            ],
            [
                [f"controls ({characters_name[0]})", 0.75, tuple(characters_color[0])],
                [f"controls ({characters_name[1]})", 0.875, tuple(characters_color[1])],
                [f"controls ({characters_name[2]})", 1, tuple(characters_color[2])],
                [f"controls ({characters_name[3]})", 1.125, tuple(characters_color[3])],
                [f"music volume: {int(mus_vol * 100)}%", 1.25],
                [f"sound volume: {int(snd_vol * 100)}%", 1.375],
                ["load texture", 1.5],
                ["back", 1.625]
            ],
            [
                [f"{bind_table[0]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[0]])}", 0.75],
                [f"{bind_table[1]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[1]])}", 0.875],
                [f"{bind_table[2]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[2]])}", 1],
                [f"{bind_table[3]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[3]])}", 1.125],
                [f"{bind_table[4]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[4]])}", 1.25],
                [f"{bind_table[5]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[5]])}", 1.375],
                [f"{bind_table[6]} ({characters_name[0]}): {pygame.key.name(controls[bind_table[6]])}", 1.5],
                ["back", 1.625]
            ],
            [
                [f"{bind_table[0]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[0]])}", 0.75],
                [f"{bind_table[1]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[1]])}", 0.875],
                [f"{bind_table[2]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[2]])}", 1],
                [f"{bind_table[3]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[3]])}", 1.125],
                [f"{bind_table[4]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[4]])}", 1.25],
                [f"{bind_table[5]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[5]])}", 1.375],
                [f"{bind_table[6]} ({characters_name[1]}): {pygame.key.name(controls2[bind_table[6]])}", 1.5],
                ["back", 1.625]
            ],
            [
                [f"{bind_table[0]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[0]])}", 0.75],
                [f"{bind_table[1]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[1]])}", 0.875],
                [f"{bind_table[2]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[2]])}", 1],
                [f"{bind_table[3]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[3]])}", 1.125],
                [f"{bind_table[4]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[4]])}", 1.25],
                [f"{bind_table[5]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[5]])}", 1.375],
                [f"{bind_table[6]} ({characters_name[2]}): {pygame.key.name(controls3[bind_table[6]])}", 1.5],
                ["back", 1.625]
            ],
            [
                [f"{bind_table[0]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[0]])}", 0.75],
                [f"{bind_table[1]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[1]])}", 0.875],
                [f"{bind_table[2]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[2]])}", 1],
                [f"{bind_table[3]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[3]])}", 1.125],
                [f"{bind_table[4]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[4]])}", 1.25],
                [f"{bind_table[5]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[5]])}", 1.375],
                [f"{bind_table[6]} ({characters_name[3]}): {pygame.key.name(controls4[bind_table[6]])}", 1.5],
                ["back", 1.625]
            ]
        ]
        dt += 1
        background_manager.load_background("ground")
        background_manager.update()
        background_manager.draw()

        menu_options = title_screen[menu_area - 1]
        selected_menu_index = range_number(selected_menu_index, 0, len(menu_options) - 1)
        if old_selected_menu_index != selected_menu_index:
            sound_player.play_sound(beep_sound)
        old_selected_menu_index = selected_menu_index
        
        camera.update(intro_players)
        
        title_ground.draw()

        for player in intro_players:
            player.rect.bottom = title_ground.y
            player.on_ground = True
            player.speedy = 0
            player.fall_timer = 0
            player.draw()
            player.update()

        if menu_options == title_screen[0]:
            for i in count_list_items(menu_options):
                options = menu_options[i]
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                text.create_text(
                    text=display_text.upper(),
                    position=(centerx, centery * options[1]),
                    alignment="center",
                    stickxtocamera=True
                )
        elif menu_options == title_screen[1]:
            for i in count_list_items(menu_options):
                options = menu_options[i]
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                text.create_text(
                    text=display_text.upper(),
                    position=(centerx, centery * options[1]),
                    alignment="center",
                    stickxtocamera=True,
                    color=options[2] if len(options) == 3 else (255, 255, 255)
                )
        elif menu_options == title_screen[2] or menu_options == title_screen[3] or menu_options == title_screen[4] or menu_options == title_screen[5]:
            for i in count_list_items(menu_options):
                options = menu_options[i]
                if binding_key and selected_menu_index == i:
                    text.create_text(
                        text="PRESS ESC TO CANCEL BINDING",
                        position=(centerx, centery * 1.875),
                        alignment="center",
                        stickxtocamera=True
                    )
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                text.create_text(
                    text=display_text.upper(),
                    position=(centerx, centery * options[1]),
                    alignment="center",
                    stickxtocamera=True
                )

        if game_ready or exit_ready:
            logo.draw()
            logo.update()
        
        if dt / 60 >= logo.bounce_time and title:
            bgm_player.play_music("title")
            fade_out = True
            title = False
            for player in intro_players:
                player.speedx = 2
                player.walk_cutscene = True

    elif game:
        if 0 < sum(1 for player in players if player.pipe_timer == 60) < len(players):
            pipe_wait_timer = (60 * (pipe_timer - 1)) if (sum(1 for player in players if player.dead_timer >= 30) == len(players) - 1) else min(pipe_wait_timer + 1, (60 * (pipe_timer - 1)))
        elif sum(1 for player in players if player.pipe_timer == 60) == len(players):
            pipe_wait_timer = (60 * (pipe_timer - 1))

        pipe_ready = pipe_wait_timer == (60 * (pipe_timer - 1))
        if pipe_ready and not fade_in:
            fade_in = True
            bgm_player.fade_out()
        
        if not pause:
            dt += 1

        if nor(pause, everyone_dead, any(player.size_change for player in players), any(player.piping for player in players), any(player.clear for player in players), nitpicks["infinite_time"]):
            course_time = math.ceil(time - dt/60)

        background_manager.load_background("ground")
        background_manager.update()
        background_manager.draw()

        try:
            if not any(player.piping for player in players):
                camera.update([player for player in players if not player.dead], x_range)
        except ZeroDivisionError:
            pass

        if castle:
            castle.draw()

        for power_meter in power_meters:
            power_meter.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                power_meter.update()

        for item in items[:]:
            if item.is_visible():
                if (item.sprouting and item.sprout_timer > 0) or not item.sprouting:
                    item.draw()
                if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                    item.update()
            if item.below_camera():
                items.remove(item)

        if any(p.size_change for p in players):
            for player in players:
                if player.piping:
                    player.draw()
        else:
            for player in players:
                if player.piping:
                    player.draw()

        for tile in tiles:
            tile.draw()
            if not pause:
                tile.update()

        for fireball_group in [fireballs, fireballs2, fireballs3, fireballs4]:
            for fireball in fireball_group[:]:
                if fireball.is_visible():
                    fireball.draw()
                    if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                        fireball.update()
                else:
                    fireball_group.remove(fireball)

        for enemy in enemies:
            if enemy.is_visible():
                if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                    enemy.update()

        if any(p.size_change for p in players):
            for player in players:
                if not player.piping:
                    player.draw()
                if player.size_change and not pause:
                    player.update()
        else:
            for player in players:
                if not player.piping:
                    player.draw()
                if not pause:
                    player.update()

        for enemy in enemies[:]:
            if enemy.is_visible():
                enemy.draw()
            else:
                if enemy.shotted:
                    enemies.remove(enemy)
            if enemy.below_camera():
                enemies.remove(enemy)

        player_lives = [player.lives for player in players]

        if course_time <= 0:
            if everyone_dead:
                text.create_text(
                text="TIME'S UP!",
                position=(centerx, centery),
                alignment="center",
                stickxtocamera=True,
                stickytocamera=True
            )
            else:
                player.dead = True
                player.dead_speed = -5

        everyone_dead = all(player.dead for player in players)
        if everyone_dead:
            pause = False

        if nor(bgm_player.is_playing("hurry"), everyone_dead, pipe_ready, pause):
            if all(player.star_timer < 1 for player in players) and any(player.star_music for player in players):
                bgm_player.play_music(main_music)
                player.star_music = False

            if any(player.star_timer >= 1 for player in players) and not any(player.star_music for player in players):
                bgm_player.play_music(star_music)
                player.star_music = True

        if course_time <= 100 and not fast_music:
            if not main_music.endswith("fast"):
                bgm_player.play_music("hurry")
                main_music = f"{main_music}fast"
                star_music = f"{star_music}fast"
            if nor(bgm_player.is_playing("hurry"), everyone_dead, pipe_ready, pause):
                bgm_player.play_music(main_music if all(player.star_timer < 1 for player in players) else star_music)
                fast_music = True

        if all(player.dead_timer >= 300 for player in players) and not bgm_player.is_playing(dead_music):
            fade_in = True

        for debris_part in debris[:]:
            debris_part.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                debris_part.update()

        for particle in particles[:]:
            particle.draw()
            if nor(any(player.size_change for player in players), everyone_dead, pause, pipe_ready):
                particle.update()

        for overlay in overlays[:]:
            overlay.draw()
            if not pause:
                overlay.update()

        if hud:
            hud.draw()

            text.create_text(
                text=f"x{hud.coins:02}",
                position=(24, 16),
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            text.create_text(
                text=f"{score:09}",
                position=(632, 16),
                alignment="right",
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            text.create_text(
                text=f"{course_time:03}",
                position=(632, 32),
                alignment="right",
                stickxtocamera=True,
                stickytocamera=True,
                scale=0.5
            )

            screen.blit(load_sprite("hudclock"), (622 - (len(str(format_number(course_time, 3))) * (text.font_size / 2)), 32))

        if players_hud:
            for player_hud in players_hud:
                player_hud.draw()
                if nor(everyone_dead, pause):
                    player_hud.update()

                for player in players:
                    text.create_text(
                        text=f"x{player.lives}",
                        position=(32, 24 + (player.player_number + 1) * 16),
                        stickxtocamera=True,
                        stickytocamera=True,
                        scale=0.5
                    )

        (sound_player.loop_sound if any(player.pspeed for player in players) and nor(sound_player.is_playing(jump_sound, jumpbig_sound), everyone_dead, pause, any(player.piping for player in players)) else sound_player.stop_sound)(pspeed_sound)
        (sound_player.loop_sound if any(player.skidding for player in players) and nor(everyone_dead, pause, any(player.piping for player in players)) else sound_player.stop_sound)(skid_sound)

        pause_menu_options = [
            ["resume", 0.8125],
            [f"music volume: {int(mus_vol * 100)}%", 0.9375],
            [f"sound volume: {int(snd_vol * 100)}%", 1.0625],
            ["quit", 1.1875]
        ]

        if pause:
            for i in count_list_items(pause_menu_options):
                options = pause_menu_options[i]

                display_text = f"> {options[0]} <" if i == pause_menu_index else options[0]

                text.create_text(
                    text=display_text,
                    position=(centerx, centery * options[1]),
                    alignment="center",
                    stickxtocamera=True,
                    stickytocamera=True
                )
        pause_menu_index = range_number(pause_menu_index, 0, 3)
        if old_pause_menu_index != pause_menu_index:
            sound_player.play_sound(beep_sound)
        old_pause_menu_index = pause_menu_index
    
    elif game_over:
        dt += 1
        text.create_text(
            text="GAME OVER",
            position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            alignment="center"
        )
        if dt >= 60 and not bgm_player.is_playing("gameover"):
            text.create_text(
                text="PRESS ANY KEY TO RESTART",
                position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.75),
                alignment="center",
                scale=0.5
            )

    if nitpicks["show_battery"]:
        battery = psutil.sensors_battery().percent
        if battery < 0:
            color = (255, 0, 0)
        elif battery < 50:
            color = (255, math.floor(255 * (battery / 40)), 0)
        elif battery < 100:
            color = (math.floor(255 * (1 - ((battery - 50) / 40))), 255, 0)
        else:
            color = (0, 255, 0)
        
        text.create_text(
            text=f"Battery: {battery}%",
            position=(632, 384 - ((text.font_size / 2) if nitpicks["show_time"] else 0)),
            alignment="right",
            stickxtocamera=True,
            stickytocamera=True,
            color=(range_number(color[0], 0, 255), range_number(color[1], 0, 255), range_number(color[2], 0, 255)),
            scale=0.5
        )

    if nitpicks["show_time"]:
        currenttime = datetime.now().strftime("%H:%M:%S")
        text.create_text(
            text=f"Time: {currenttime}",
            position=(632, 384),
            alignment="right",
            stickxtocamera=True,
            stickytocamera=True,
            scale=0.5
        )
    
    fade_surface.fill((0, 0, 0, a))
    screen.blit(fade_surface, (0, 0))

    if menu and not game_ready:
        logo.draw()
        logo.update()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            menu = False
            title = False
            fade_in = False
            fade_out = False
            binding_key = False
            current_bind = False
        elif event.type == pygame.KEYDOWN:
            if game and (event.key == controls["pause"] or event.key == controls2["pause"] or event.key == controls3["pause"] or event.key == controls4["pause"]) and nor(any(player.piping for player in players), everyone_dead):
                if not nitpicks["play_music_in_pause"]:
                    bgm_player.pause_music()
                pause = not pause
                sound_player.play_sound(pause_sound)
                pause_menu_index = 0
                old_pause_menu_index = 0
            if game and pause and not fade_in:
                if event.key == controls["down"]:
                    pause_menu_index += 1
                elif event.key == controls["up"]:
                    pause_menu_index -= 1
                elif event.key == controls["left"]:
                    if pause_menu_index == 1:
                        mus_vol -= numerical_change
                    elif pause_menu_index == 2:
                        snd_vol -= numerical_change
                elif event.key == controls["right"]:
                    if pause_menu_index == 1:
                        mus_vol += numerical_change
                    elif pause_menu_index == 2:
                        snd_vol += numerical_change
                elif event.key == controls["jump"]:
                    if pause_menu_index == 0:
                        pause = False
                        bgm_player.pause_music()
                        sound_player.play_sound(coin_sound)
                    elif pause_menu_index == 3:
                        fade_in = True
                        exit_ready = True
                        bgm_player.fade_out()
                        sound_player.play_sound(coin_sound)
            if game_over and dt >= 60 and nor(bgm_player.is_playing("gameover"), game_ready):
                bgm_player.stop_music()
                sound_player.stop_all_sounds()
                sound_player.play_sound(coin_sound)
                fade_in = True
                game_ready = True
            if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                fullscreen = not fullscreen
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
            if menu and nor(title, fade_in, fade_out, game_ready):
                if binding_key:
                    if event.key == pygame.K_ESCAPE:
                        sound_player.play_sound(pipe_sound)
                    else:
                        sound_player.play_sound(powerup_sound)
                        controls_table[menu_area - 3][bind_table[selected_menu_index]] = event.key
                    binding_key = False
                    current_bind = False
                    sound_player.stop_sound(sprout_sound)
                else:
                    if event.key == controls["down"]:
                        selected_menu_index += 1
                    elif event.key == controls["up"]:
                        selected_menu_index -= 1
                if event.key == controls["left"]:
                    if menu_options == title_screen[1]:
                        if selected_menu_index == 4:
                            mus_vol -= numerical_change
                        elif selected_menu_index == 5:
                            snd_vol -= numerical_change
                elif event.key == controls["right"]:
                    if menu_options == title_screen[1]:
                        if selected_menu_index == 4:
                            mus_vol += numerical_change
                        elif selected_menu_index == 5:
                            snd_vol += numerical_change
                elif event.key == controls["run"] and not binding_key:
                    if menu_options == title_screen[1]:
                        selected_menu_index = 0
                        old_selected_menu_index = 0
                        menu_area = 1
                        sound_player.play_sound(pipe_sound)
                    elif menu_options == title_screen[2]:
                        selected_menu_index = 0
                        old_selected_menu_index = 0
                        menu_area = 2
                        sound_player.play_sound(pipe_sound)
                elif event.key == controls["jump"]:
                    if menu_options == title_screen[0]:
                        if selected_menu_index == 4:
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            menu_area = 2
                            sound_player.play_sound(coin_sound)
                        elif selected_menu_index == 5:
                            fade_in = True
                            exit_ready = True
                            bgm_player.fade_out()
                            sound_player.play_sound(coin_sound)
                        else:
                            fade_in = True
                            game_ready = True
                            bgm_player.fade_out()
                            sound_player.play_sound(coin_sound)
                            player_count = selected_menu_index + 1
                    elif menu_options == title_screen[1]:
                        if selected_menu_index >= 0 and selected_menu_index < 4:
                            menu_area = selected_menu_index + 3
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            sound_player.play_sound(coin_sound)
                        elif selected_menu_index == len(menu_options) - 1:
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            menu_area = 1
                            sound_player.play_sound(coin_sound)
                    elif menu_options in title_screen[2:6] and not binding_key:
                        if selected_menu_index == 7:
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            menu_area = 2
                            sound_player.play_sound(coin_sound)
                        else:
                            binding_key = True
                            current_bind = bind_table[selected_menu_index]
                            sound_player.play_sound(sprout_sound)
                            sound_player.stop_sound(powerup_sound)

    bgm_player.update()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

with open(load_local_file("settings.json"), "w") as settings:
    json.dump(
        {
            "mus_vol": mus_vol,
            "snd_vol": snd_vol,
            "controls": controls,
            "controls2": controls2,
            "controls3": controls3,
            "controls4": controls4,
            "fullscreen": fullscreen
        }, settings, indent=4
    )