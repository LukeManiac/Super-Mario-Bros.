import pygame, json
from os.path import dirname, abspath, exists, getsize
import math

pygame.init()
pygame.font.init()
pygame.joystick.init()
pygame.mixer.init()

main_directory = dirname(abspath(__file__))
infinity = float("inf")

def load_asset(asset):
    global main_directory
    return f"{main_directory}/assets/{asset}"

def load_background(background):
    return pygame.image.load(load_asset(f"bg_{background}.png")).convert_alpha()
    
def load_sprite(sprite):
    return pygame.image.load(load_asset(f"spr_{sprite}.png")).convert_alpha()

def load_sound(sound):
    return pygame.mixer.Sound(load_asset(f"snd_{sound}.wav"))
    
def range_number(num, minval, maxval):
    return min(max(num, minval), maxval)

def check_player_condition(players, condition):
    return any(condition(player) for player in players)

def is_playing(sound):
    return sound.get_num_channels() > 0

def nand(*conditions):
    return not all(conditions)

def nor(*conditions):
    return not any(conditions)

def get_chars(string, chars):
    return string[:chars]

def get_last_chars(string, chars):
    return string[-chars:]

def create_text(text, position, color=(255, 255, 255), alignment="left", stickxtocamera=False, stickytocamera=False):
    char_offset = 0
    line_offset = 0
    lines = text.split("\n")
    x, y = position
    rendered_lines = []

    if stickxtocamera:
        x += camera.x

    if stickytocamera:
        y += camera.y

    max_line_width = 0

    for line in lines:
        line_width = sum(font.render(char, True, color).get_width() + char_offset for char in line)
        max_line_width = max(max_line_width, line_width)

    for i, line in enumerate(lines):
        rendered_line = []
        offset_x = 0

        for char in line:
            char_surface = font.render(char, True, color)
            rendered_line.append((char_surface, offset_x))
            offset_x += char_surface.get_width() + char_offset

        rendered_lines.append((rendered_line, y + i * (font.get_height() + line_offset)))

    for rendered_line, line_y in rendered_lines:
        start_x = x - camera.x
        if alignment == "center":
            start_x -= max_line_width // 2
        elif alignment == "right":
            start_x -= max_line_width

        for char_surface, char_x in rendered_line:
            screen.blit(char_surface, (start_x + char_x, line_y))

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 400
WALK_SPEED = 2.5
RUN_SPEED = 4
JUMP_HOLD_TIME = 10
MIN_SPEEDX = math.pi / 10
MIN_RUN_TIMER = 0
MAX_RUN_TIMER = 75
FPS = 100
FRAME_SPEED = 10

class SFXPlayer:
    def __init__(self):
        self.sounds = {}

    def play_sound(self, sound):
        self.sounds[sound] = sound
        if sound in self.sounds:
            self.sounds[sound].set_volume(snd_vol)
            self.sounds[sound].stop()
            self.sounds[sound].play()

    def stop_sound(self, sound):
        if sound in self.sounds:
            self.sounds[sound].stop()

    def loop_sound(self, sound):
        if sound in self.sounds:
            self.sounds[sound].set_volume(snd_vol)
            self.sounds[sound].play(-1)

    def set_volume(self, volume):
        for sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)

class BGMPlayer:
    def __init__(self):
        self.loop_point = 0
        self.music_playing = False
        self.music_length = 0

    def play_music(self, music):
        self.stop_music()
        pygame.mixer.music.load(load_asset(f"bgm_{music}.ogg"))
        self.loop_point = dict(music_table)[music]
        if self.loop_point != 0:
            pygame.mixer.music.play(0)
            self.loop_point = self.loop_point / 1000
            self.music_playing = True
        else:
            if self.loop_point:
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.play(0)

    def stop_music(self):
        self.music_playing = False
        pygame.mixer.music.stop()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def update(self):
        if self.music_playing:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(0, self.loop_point)
                self.music_playing = True

class Background:
    def __init__(self):
        self.bg_image = None
        self.bg_layers = []
        self.bg_positions = []
        self.layer_width = 0
        self.bg_height = 0

    def load_background(self, bgname, bglayers=1):
        self.bg_image = load_background(bgname)
        self.bg_width, self.bg_height = self.bg_image.get_size()
        self.layer_width = self.bg_width // bglayers
        self.bg_layers = [self.bg_image.subsurface(pygame.Rect(x * self.layer_width, 0, self.layer_width, self.bg_height)) for x in range(bglayers)]
        self.bg_positions = [0] * bglayers

    def update(self):
        for i in range(len(self.bg_layers)):
            parallax_factor = 1 - (i / 10)
            self.bg_positions[i] = -(camera.x * parallax_factor) % self.layer_width

    def draw(self):
        for i in range(len(self.bg_layers)):
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

    def update(self, players, max_x, max_y):
        self.x = range_number(
            sum(player.rect.x + player.rect.width + player.speedx for player in players) / len(players) - SCREEN_WIDTH // 2,
            0, (max_x if max_x else float('inf'))
        )
        self.y = range_number(
            sum(player.rect.y + player.rect.height + player.speedy for player in players) / len(players) - SCREEN_HEIGHT // 2,
            0, (max_y if max_y else float('inf'))
        )

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
        self.y = SCREEN_HEIGHT - 8
        self.sprite = load_sprite("ground")

    def check_collision(self, mario):
        mario.on_ground = mario.rect.bottom >= self.y
        if mario.rect.bottom >= self.y:
            mario.rect.bottom = self.y

    def draw(self):
        offset_x = -camera.x % 16
        for y in range(2):
            for x in range(0, SCREEN_WIDTH + 32, 16):
                screen.blit(self.sprite, (x + offset_x - 16, self.y + 16 * y - camera.y))

class PowerMeter:
    def __init__(self, player):
        self.frames = [pygame.Rect(0, i * 7, 64, 7) for i in range(8)]
        self.player = player
        self.spritesheet = load_sprite("powermeter")
        self.spritesheet = self.recolor_spritesheet((player.color[player.character]))
        self.current_frame = 0
        self.frame_swap_timer = 0
        self.swap_state = False

    def recolor_spritesheet(self, new_color):
        recolored = self.spritesheet.copy()
        pixel_array = pygame.PixelArray(recolored)

        for x in range(recolored.get_width()):
            for y in range(recolored.get_height()):
                pixel = recolored.unmap_rgb(pixel_array[x, y])
                if pixel[:3] == (255, 255, 255):
                    alpha = pixel[3]
                    new_pixel = new_color + (alpha,)
                    pixel_array[x, y] = recolored.map_rgb(new_pixel)

        del pixel_array
        return recolored

    def update(self):
        if self.player.pspeed:
            self.frame_swap_timer += 1
            if self.frame_swap_timer >= 6:
                self.swap_state = not self.swap_state
                self.frame_swap_timer = 0
            self.current_frame = 7 if self.swap_state else 6
        else:
            self.current_frame = min(self.player.run_timer // int(round(MAX_RUN_TIMER / 7.5)), 7)
            self.frame_swap_timer = 0

    def draw(self):
        sprite = self.spritesheet.subsurface(self.frames[self.current_frame])
        draw_x = self.player.rect.x - 18 - camera.x
        draw_y = self.player.rect.y - camera.y - 12
        if self.player.controls_enabled:
            screen.blit(sprite, (draw_x, draw_y))

class Tile:
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False):
        self.x = x * 16
        self.y = y * 16
        self.spriteset = spriteset - 1
        self.image = load_sprite(image)
        self.img_width, self.img_height = self.image.get_size()
        self.tile_size = 16
        self.rect = pygame.Rect(x, y, 16, self.tile_size)
        self.cols = 1
        self.rows = self.img_height // self.tile_size
        self.sprites = [pygame.Rect(0, row * self.tile_size, 16, self.tile_size) for row in range(self.rows)]

        self.left_collide = left_collide
        self.right_collide = right_collide
        self.top_collide = top_collide
        self.bottom_collide = bottom_collide
        self.bonk_bounce = bonk_bounce
        
        self.bouncing = False
        self.bounce_timer = 0
        self.bounce_speed = 0
        self.y_offset = 0

    def check_collision(self, player):
        if self.rect.colliderect(player.rect):
            dx_left = player.rect.right - self.rect.left
            dx_right = self.rect.right - player.rect.left
            dy_top = player.rect.bottom - self.rect.top
            dy_bottom = self.rect.bottom - player.rect.top

            min_dx, min_dy = min(dx_left, dx_right), min(dy_top, dy_bottom)

            if min_dx < min_dy:
                if dx_left < dx_right and self.left_collide:
                    player.rect.right = self.rect.left
                    player.speedx = 0
                elif dx_right < dx_left and self.right_collide:
                    player.rect.left = self.rect.right
                    player.speedx = 0
            else:
                if dy_top < dy_bottom and self.top_collide:
                    player.rect.bottom = self.rect.top
                    player.speedy = 0
                    player.on_ground = True
                elif dy_bottom < dy_top and self.bottom_collide:
                    player.rect.top = self.rect.bottom
                    player.speedy = 0
                    sound_player.play_sound(bump_sound)

                    if self.bonk_bounce:
                        self.bouncing = True
                        self.bounce_speed = -2
                        self.y_offset = 0

    def update(self):
        if self.bouncing:
            self.y_offset += self.bounce_speed
            self.bounce_speed += 0.25

            if self.y_offset >= 0:
                self.y_offset = 0
                self.bouncing = False

    def draw(self):
        if 0 <= self.spriteset < self.rows:
            screen.blit(self.image.subsurface(self.sprites[self.spriteset]), (self.x - camera.x, self.y - camera.y + self.y_offset))

class AnimatedTile(Tile):
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False):
        super().__init__(x, y, image, spriteset, left_collide, right_collide, top_collide, bottom_collide, bonk_bounce)

        self.cols = self.img_width // self.tile_size
        self.total_frames = self.cols
        self.frame_index = 0

        self.sprites = [
            [pygame.Rect(col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size) for col in range(self.cols)]
            for row in range(self.rows)
        ]

    def update(self):
        super().update()
        self.frame_index = int((dt / (FPS / self.cols)) % self.total_frames)

    def draw(self):
        if 0 <= self.spriteset < self.rows and 0 <= self.frame_index < self.cols:
            screen.blit(
                self.image.subsurface(self.sprites[self.spriteset][self.frame_index]),
                (self.x - camera.x, self.y - camera.y),
            )

    def check_collision(self, player):
        super().check_collision(player)

class Brick(AnimatedTile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "brick", spriteset, bonk_bounce=True)

class Player:
    def __init__(self, x, y, size=0, walk_frames=6, run_frames=3, character="mario", acceleration=0.1, max_jump=4, controls_enabled=True, walk_cutscene=False):
        self.spritesheet = load_sprite(character)
        self.controls_enabled = controls_enabled
        self.character = character
        self.speedx = 0
        self.speedy = 0
        self.frame_timer = 0
        self.on_ground = False
        self.facing_right = True
        self.jump_timer = 0
        self.anim_state = 1
        self.left = False
        self.right = False
        self.down = False
        self.crouch = False
        self.jump = False
        self.walk_frames = walk_frames
        self.run_frames = run_frames
        self.color = {
            "mario": (247, 57, 16),
            "luigi": (33, 173, 16),
            "yellowtoad": (230, 158, 18),
            "bluetoad": (80, 80, 255)
        }
        self.img_width, self.img_height = self.spritesheet.get_size()
        self.rect = pygame.Rect(x, y, self.img_width, self.img_height)
        self.sprites = [[pygame.Rect(x * 20, y * 34, 20, 34) for x in range(self.img_width // 20)] for y in range(self.img_height // 34)]
        self.size = size
        self.acceleration = acceleration
        self.max_jump = max_jump
        self.walk_cutscene = walk_cutscene
        self.skidding = False
        self.gravity = 0.25
        self.min_jump = 1
        self.run_timer = 0
        self.jump_lock = False
        self.update_hitbox()
        self.rect.y -= self.rect.height
        self.carrying_item = False
        self.controls_table = {
            "mario": controls,
            "luigi": controls2,
            "yellowtoad": controls3,
            "bluetoad": controls4
        }
        self.controls = self.controls_table[character]

    def update_hitbox(self):
        prev_bottom = self.rect.bottom

        new_width, new_height = (16, 16 if self.size == 0 else 32) if not self.crouch else (16, 8 if self.size == 0 else 16)

        self.rect.width, self.rect.height = new_width, new_height
        self.rect.bottom = prev_bottom

    def update(self):
        if self.controls_enabled:
            self.left = keys[self.controls["left"]]
            self.right = keys[self.controls["right"]]
            self.run = keys[self.controls["run"]]
            self.jump = keys[self.controls["jump"]]
            self.crouch = keys[self.controls["down"]] if self.on_ground else self.crouch
            self.speed = RUN_SPEED if self.run else WALK_SPEED

        self.update_hitbox()

        if self.on_ground and not self.walk_cutscene:
            if self.left and not self.right:
                self.speedx = max(self.speedx - self.acceleration, -self.speed)
                self.facing_right = False if self.on_ground else self.facing_right
            elif self.right and not self.left:
                self.speedx = min(self.speedx + self.acceleration, self.speed)
                self.facing_right = True if self.on_ground else self.facing_right
            else:
                if abs(self.speedx) <= MIN_SPEEDX:
                    self.speedx = 0
                else:
                    self.speedx *= (1 - self.acceleration)
        else:
            if self.left and not self.right:
                if self.speedx > 0:  
                    self.speedx -= self.acceleration
                self.speedx = max(self.speedx - self.acceleration, -self.speed)  
            elif self.right and not self.left:
                if self.speedx < 0:  
                    self.speedx += self.acceleration  
                self.speedx = min(self.speedx + self.acceleration, self.speed)

        if self.on_ground and self.jump_timer == 0 and self.jump and not self.jump:
            self.speedy = -self.min_jump
            self.jump_timer = 1
        elif self.jump and self.jump_timer > 0 and self.jump_timer < JUMP_HOLD_TIME:
            if self.jump_timer <= 1:
                sound_player.play_sound(jump_sound if self.size == 0 else jumpbig_sound)
            self.speedy = max(self.speedy - self.max_jump, -self.max_jump)
            self.jump_timer += 1
        elif not self.jump:
            self.jump_timer = 1 if self.on_ground else 0

        self.speedx = range_number(self.speedx, -RUN_SPEED, RUN_SPEED)
        self.speedy += self.gravity
        self.skidding = self.on_ground and ((self.speedx < 0 and self.facing_right) or (self.speedx > 0 and not self.facing_right)) and not self.crouch
        self.pspeed = self.run_timer >= MAX_RUN_TIMER

        if self.on_ground and self.controls_enabled:
            self.run_timer = MAX_RUN_TIMER if nitpicks["always_pspeed"] else range_number(self.run_timer + 1 if abs(self.speedx) == RUN_SPEED else self.run_timer - 1, MIN_RUN_TIMER, MAX_RUN_TIMER)
        else:
            if not self.pspeed:
                self.run_timer = max(self.run_timer - 1, MIN_RUN_TIMER)

        new_x = self.rect.x + self.speedx
        self.rect.x = new_x

        if tiles:
            for tile in tiles:
                tile.check_collision(self)

        if self.rect.x < camera.x:
            self.rect.x = camera.x
            self.speedx = 0
        elif self.rect.x + self.rect.width > camera.x + SCREEN_WIDTH:
            self.rect.x = camera.x + SCREEN_WIDTH - self.rect.width
            self.speedx = 0

        if self.rect.y < camera.y:
            self.rect.y = camera.y
            self.speedy = 0
        elif self.rect.y + self.rect.height > camera.y + SCREEN_HEIGHT:
            self.rect.y = camera.y + SCREEN_HEIGHT - self.rect.height
            self.speedy = 0
            self.on_ground = True

        if self.crouch and self.on_ground:
            self.speedx *= (1 - self.acceleration)

        self.rect.y += self.speedy
        self.rect.x = range_number(camera.x + SCREEN_WIDTH - self.rect.width, camera.x, self.rect.x)
        self.rect.y = range_number(camera.y + SCREEN_HEIGHT - self.rect.height, camera.y, self.rect.y)
        
        self.on_ground = False
        title_ground.check_collision(self)

        if tiles:
            for tile in tiles:
                tile.check_collision(self)
        
        if self.on_ground:
            self.speedy = 0
            if self.crouch:
                if self.speedx > 0:
                    self.speedx -= self.acceleration
                elif self.speedx < 0:
                    self.speedx += self.acceleration

        if self.crouch:
            self.anim_state = (3 if self.speedy > 0 else 2) + (8 + self.walk_frames + self.run_frames if self.carrying_item else 0)
        elif self.skidding:
            if self.carrying_item:
                self.frame_timer += abs(self.speedx) / 1.25
                self.anim_state = (12 + self.walk_frames + self.run_frames if self.carrying_item else 4) + int(self.frame_timer // FRAME_SPEED) % self.walk_frames
            else:
                self.anim_state = 4 + self.walk_frames
        elif self.speedy < 0:
            self.anim_state = ((12 + self.walk_frames + self.run_frames + (2 if self.pspeed else 0)) if self.carrying_item else (7 + self.run_frames if self.pspeed else 5)) + self.walk_frames
        elif self.speedy >= 0 and nor(self.on_ground, self.crouch):
            self.anim_state = ((13 + self.walk_frames + self.run_frames + (2 if self.pspeed else 0)) if self.carrying_item else (8 + self.run_frames if self.pspeed else 6)) + self.walk_frames
        elif self.speedx == 0 and self.on_ground and not self.crouch:
            self.anim_state = (9 + self.walk_frames + self.run_frames) if self.carrying_item else 1
            self.speedx = 0
        elif abs(self.speedx) > 0 and self.on_ground and not self.pspeed or self.carrying_item:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = (12 + self.walk_frames + self.run_frames if self.carrying_item else 4) + int(self.frame_timer // FRAME_SPEED) % self.walk_frames
        elif self.pspeed and self.on_ground and not self.carrying_item:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = 7 + self.walk_frames + int(self.frame_timer // FRAME_SPEED) % self.run_frames

    def draw(self):
        sprite = self.spritesheet.subsurface(self.sprites[self.size][self.anim_state - 1])
        sprite = pygame.transform.flip(sprite, (not self.facing_right) ^ nitpicks["moonwalking_mario"], nitpicks["upside_down_mario"])

        draw_x = self.rect.x - camera.x + (((1 if self.character == "mario" else 2 if self.character == "luigi" else 0) if self.anim_state == 7 + self.run_frames + self.walk_frames or self.anim_state == 8 + self.run_frames + self.walk_frames or self.anim_state == 14 + self.run_frames + self.walk_frames * 2 or self.anim_state == 15 + self.run_frames + self.walk_frames * 2 else 0) * (1 if (not self.facing_right) ^ nitpicks["moonwalking_mario"] else -1))

        draw_y = self.rect.y - camera.y + self.rect.height - 33
        screen.blit(sprite, (draw_x, draw_y))

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
deadzone = 0.5

if exists(f"{main_directory}/settings.json") and not getsize(f"{main_directory}/settings.json") == 0:
    with open(f"{main_directory}/settings.json", "r") as file:
        data = json.load(file)
        mus_vol = data.get("mus_vol", mus_vol)
        snd_vol = data.get("snd_vol", snd_vol)
        controls = data.get("controls", controls)
        controls2 = data.get("controls2", controls2)
        controls3 = data.get("controls3", controls3)
        controls4 = data.get("controls4", controls4)
        deadzone = data.get("deadzone", deadzone)
        fullscreen = data.get("fullscreen", fullscreen)

if not exists(f"{main_directory}/nitpicks.json"):
    with open(f"{main_directory}/nitpicks.json", "w") as nitpicks:
        json.dump(
            {
                "upside_down_mario": False,
                "upside_down_enemies": False,
                "moonwalking_mario": False,
                "moonwalking_enemies": False,
                "always_pspeed": False
            }, nitpicks, indent=4
        )

with open(f"{main_directory}/nitpicks.json", "r") as file:
    nitpicks = json.load(file)

music_table = [
    ["overworld", 2136],
    ["title", 3736]
]
running = True
centerx = SCREEN_WIDTH / 2
centery = SCREEN_HEIGHT / 2
font_size = 16
font = pygame.font.Font(f"{main_directory}/font.ttf", font_size)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
clock = pygame.time.Clock()
pygame.display.set_icon(load_sprite("icon"))
pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
player_dist = 20
intro_players = [Player(
    x=centerx - player_dist / 2 + player_dist * i,
    y=SCREEN_HEIGHT,
    character=character,
    size=1,
    **properties)
    for i, (character, properties) in enumerate(
        [
            ("mario", {}),
            ("luigi", {"acceleration": 0.05, "max_jump": 5}),
            ("yellowtoad", {"acceleration": 0.2}),
            ("bluetoad", {"acceleration": 0.25})
        ]
    )
]
camera = Camera()
bgm_player = BGMPlayer()
sound_player = SFXPlayer()
title_ground = TitleGround()
background_manager = Background()
tiles = []
beep_sound = load_sound("beep")
bump_sound = load_sound("bump")
coin_sound = load_sound("coin")
jump_sound = load_sound("jump")
jumpbig_sound = load_sound("jumpbig")
oneup_sound = load_sound("oneup")
pipe_sound = load_sound("pipe")
powerup_sound = load_sound("powerup")
pspeed_sound = load_sound("pspeed")
skid_sound = load_sound("skid")
sprout_sound = load_sound("sprout")
fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
a = 255
fade_in = False
fade_out = False

logo = Logo()

selected_menu_index = 0
old_selected_menu_index = 0
old_mus_vol = mus_vol
old_snd_vol = snd_vol
old_deadzone = deadzone
dt = 0
menu_area = 1
menu = True
title = True
bind_table = ["up", "down", "left", "right", "run", "jump", "pause"]
binding_key = False
current_bind = False
game_ready = False
exit_ready = False

if pygame.joystick.get_count() > 0:
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        joystick.init()

while running:
    bgm_player.set_volume(mus_vol)
    sound_player.set_volume(snd_vol)
    SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
    pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
    current_fps = FPS if clock.get_fps() == 0 else clock.get_fps()
    screen.fill((0, 0, 0))
    keys = pygame.key.get_pressed()
    
    controls_table = [controls, controls2, controls3, controls4]

    mus_vol = round(range_number(mus_vol, 0, 1) * 10) / 10
    snd_vol = round(range_number(snd_vol, 0, 1) * 10) / 10
    deadzone = round(range_number(deadzone, 0.1, 1) * 10) / 10
    if nand(old_mus_vol == mus_vol, old_snd_vol == snd_vol, old_deadzone == deadzone):
        sound_player.play_sound(beep_sound)
    old_mus_vol = mus_vol
    old_snd_vol = snd_vol
    old_deadzone = deadzone
    pspeed_sound.set_volume(0 if is_playing(jump_sound) or is_playing(jumpbig_sound) else 1)

    with open(f"{main_directory}/settings.json", "w") as settings:
        json.dump(
            {
                "mus_vol": mus_vol,
                "snd_vol": snd_vol,
                "controls": controls,
                "controls2": controls2,
                "controls3": controls3,
                "controls4": controls4,
                "deadzone": deadzone,
                "fullscreen": fullscreen
            }, settings, indent=4)

    if fade_in:
        fade_out = False
        a += 255 / FPS
        if a >= 255:
            a = 255
            fade_in = False
            if exit_ready:
                running = False
                menu = False
                title = False
                fade_in = False
                fade_out = False

    elif fade_out:
        fade_in = False
        a -= 255 / FPS
        if a <= 0:
            a = 0
            fade_out = False

    if menu:
        title_screen = [
            [
                ["1 player game", centery * 0.75],
                ["2 player game", centery * 0.875],
                ["3 player game", centery],
                ["4 player game", centery * 1.125],
                ["options", centery * 1.25],
                ["quit", centery * 1.375]
            ],
            [
                ["controls (mario)", centery * 0.75, (247, 57, 16)],
                ["controls (luigi)", centery * 0.875, (33, 173, 16)],
                ["controls (yellow toad)", centery, (230, 158, 18)],
                ["controls (blue toad)", centery * 1.125, (80, 80, 255)],
                [f"music volume: {int(mus_vol * 100)}%", centery * 1.25],
                [f"sound volume: {int(snd_vol * 100)}%", centery * 1.375],
                [f"deadzone: {deadzone}", centery * 1.5],
                ["back", centery * 1.625]
            ],
            [
                [f"{bind_table[0]} (mario): {pygame.key.name(controls[bind_table[0]])}", centery * 0.75],
                [f"{bind_table[1]} (mario): {pygame.key.name(controls[bind_table[1]])}", centery * 0.875],
                [f"{bind_table[2]} (mario): {pygame.key.name(controls[bind_table[2]])}", centery],
                [f"{bind_table[3]} (mario): {pygame.key.name(controls[bind_table[3]])}", centery * 1.125],
                [f"{bind_table[4]} (mario): {pygame.key.name(controls[bind_table[4]])}", centery * 1.25],
                [f"{bind_table[5]} (mario): {pygame.key.name(controls[bind_table[5]])}", centery * 1.375],
                [f"{bind_table[6]} (mario): {pygame.key.name(controls[bind_table[6]])}", centery * 1.5],
                ["back", centery * 1.625]
            ],
            [
                [f"{bind_table[0]} (luigi): {pygame.key.name(controls2[bind_table[0]])}", centery * 0.75],
                [f"{bind_table[1]} (luigi): {pygame.key.name(controls2[bind_table[1]])}", centery * 0.875],
                [f"{bind_table[2]} (luigi): {pygame.key.name(controls2[bind_table[2]])}", centery],
                [f"{bind_table[3]} (luigi): {pygame.key.name(controls2[bind_table[3]])}", centery * 1.125],
                [f"{bind_table[4]} (luigi): {pygame.key.name(controls2[bind_table[4]])}", centery * 1.25],
                [f"{bind_table[5]} (luigi): {pygame.key.name(controls2[bind_table[5]])}", centery * 1.375],
                [f"{bind_table[6]} (luigi): {pygame.key.name(controls2[bind_table[6]])}", centery * 1.5],
                ["back", centery * 1.625]
            ],
            [
                [f"{bind_table[0]} (yellow toad): {pygame.key.name(controls3[bind_table[0]])}", centery * 0.75],
                [f"{bind_table[1]} (yellow toad): {pygame.key.name(controls3[bind_table[1]])}", centery * 0.875],
                [f"{bind_table[2]} (yellow toad): {pygame.key.name(controls3[bind_table[2]])}", centery],
                [f"{bind_table[3]} (yellow toad): {pygame.key.name(controls3[bind_table[3]])}", centery * 1.125],
                [f"{bind_table[4]} (yellow toad): {pygame.key.name(controls3[bind_table[4]])}", centery * 1.25],
                [f"{bind_table[5]} (yellow toad): {pygame.key.name(controls3[bind_table[5]])}", centery * 1.375],
                [f"{bind_table[6]} (yellow toad): {pygame.key.name(controls3[bind_table[6]])}", centery * 1.5],
                ["back", centery * 1.625]
            ],
            [
                [f"{bind_table[0]} (blue toad): {pygame.key.name(controls4[bind_table[0]])}", centery * 0.75],
                [f"{bind_table[1]} (blue toad): {pygame.key.name(controls4[bind_table[1]])}", centery * 0.875],
                [f"{bind_table[2]} (blue toad): {pygame.key.name(controls4[bind_table[2]])}", centery],
                [f"{bind_table[3]} (blue toad): {pygame.key.name(controls4[bind_table[3]])}", centery * 1.125],
                [f"{bind_table[4]} (blue toad): {pygame.key.name(controls4[bind_table[4]])}", centery * 1.25],
                [f"{bind_table[5]} (blue toad): {pygame.key.name(controls4[bind_table[5]])}", centery * 1.375],
                [f"{bind_table[6]} (blue toad): {pygame.key.name(controls4[bind_table[6]])}", centery * 1.5],
                ["back", centery * 1.625]
            ]
        ]
        dt += 1
        background_manager.load_background("ground", 4)
        background_manager.update()
        background_manager.draw()

        menu_options = title_screen[menu_area - 1]
        selected_menu_index = range_number(selected_menu_index, 0, len(menu_options) - 1)
        if old_selected_menu_index != selected_menu_index:
            sound_player.play_sound(beep_sound)
        old_selected_menu_index = selected_menu_index
        
        camera.update(intro_players, False, 15)
        
        title_ground.draw()

        if tiles:
            for tile in tiles:
                tile.draw()
                tile.update()

        for player in intro_players:
            player.draw()
            player.update()

        if menu_options == title_screen[0]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                create_text(
                    text=display_text.upper(),
                    position=(centerx, options[1]),
                    alignment="center",
                    stickxtocamera=True
                )
        elif menu_options == title_screen[1]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                create_text(
                    text=display_text.upper(),
                    position=(centerx, options[1]),
                    alignment="center",
                    stickxtocamera=True,
                    color=options[2] if len(options) == 3 else (255, 255, 255)
                )
        elif menu_options == title_screen[2] or menu_options == title_screen[3] or menu_options == title_screen[4] or menu_options == title_screen[5]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                if binding_key and selected_menu_index == i:
                    create_text(
                        text="PRESS ESC TO CANCEL BINDING",
                        position=(centerx, centery * 1.875),
                        alignment="center",
                        stickxtocamera=True
                    )
                
                display_text = f"> {options[0]} <" if i == selected_menu_index else options[0]

                create_text(
                    text=display_text.upper(),
                    position=(centerx, options[1]),
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

    fade_surface.fill((0, 0, 0, a))
    screen.blit(fade_surface, (0, 0))

    if nor(game_ready, exit_ready):
        logo.draw()
        logo.update()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            menu = False
            title = False
            fade_in = False
            fade_out = False
        elif event.type == pygame.KEYDOWN:
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
                            mus_vol -= 0.1
                        elif selected_menu_index == 5:
                            snd_vol -= 0.1
                        elif selected_menu_index == 6:
                            deadzone -= 0.1
                elif event.key == controls["right"]:
                    if menu_options == title_screen[1]:
                        if selected_menu_index == 4:
                            mus_vol += 0.1
                        elif selected_menu_index == 5:
                            snd_vol += 0.1
                        elif selected_menu_index == 6:
                            deadzone += 0.1
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
                            bgm_player.stop_music()
                            sound_player.play_sound(coin_sound)
                        else:
                            fade_in = True
                            game_ready = True
                            bgm_player.stop_music()
                            sound_player.play_sound(coin_sound)
                            player_count = selected_menu_index + 1
                    elif menu_options == title_screen[1]:
                        if selected_menu_index >= 0 and selected_menu_index < 4:
                            menu_area = selected_menu_index + 3
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            sound_player.play_sound(coin_sound)
                        elif selected_menu_index == 7:
                            selected_menu_index = 0
                            old_selected_menu_index = 0
                            menu_area = 1
                            sound_player.play_sound(coin_sound)
                    elif menu_options == title_screen[2] or menu_options == title_screen[3] or menu_options == title_screen[4] or menu_options == title_screen[5] and not binding_key:
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
    
        elif event.type == pygame.JOYBUTTONDOWN and binding_key:
            joystick = joysticks[event.joy]
            if binding_key:
                if current_bind:
                    if current_bind in controls_table[event.joy]:
                        controls_table[event.joy][bind_table[selected_menu_index]] = joystick.get_button(event.button)
                binding_key = False
                current_bind = False
                sound_player.play_sound(powerup_sound)
                sound_player.stop_sound(sprout_sound)

        elif event.type == pygame.JOYAXISMOTION and binding_key:
            joystick = joysticks[event.joy]
            if abs(joystick.get_axis(0)) > deadzone:
                controls_table[event.joy][bind_table[selected_menu_index]] = event.axis
            else:
                binding_key = False
                current_bind = False
                sound_player.play_sound(powerup_sound)
                sound_player.stop_sound(sprout_sound)
    
    bgm_player.update()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

with open(f"{main_directory}/settings.json", "w") as settings:
    json.dump(
        {
            "mus_vol": mus_vol,
            "snd_vol": snd_vol,
            "controls": controls,
            "controls2": controls2,
            "controls3": controls3,
            "controls4": controls4,
            "deadzone": deadzone,
            "fullscreen": fullscreen
        }, settings, indent=4
    )
