import pygame, json
from os import path
from math import pi

pygame.init()
pygame.font.init()
pygame.joystick.init()
pygame.mixer.init()

def load_asset(asset):
    return f"{path.dirname(path.abspath(__file__))}/assets/{asset}"

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

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 360
WALK_SPEED = 2.5
RUN_SPEED = 4
JUMP_HOLD_TIME = 10
MIN_SPEEDX = pi / 10
MIN_RUN_TIMER = 0
MAX_RUN_TIMER = 75
FPS = 60
FADE_DURATION = FPS

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
        self.music_path = None
        self.replay_enabled = False

    def play_music(self, music, loop_point=0):
        self.music_path = load_asset(f"bgm_{music}.ogg")
        pygame.mixer.music.load(self.music_path)
        pygame.mixer.music.play(loops=-1 if self.loop_point == 0 else 0)
        if loop_point:
            self.loop_point = loop_point / 1000
            self.music_playing = True
            self.music_length = pygame.mixer.Sound(self.music_path).get_length()
            self.replay_enabled = False

    def stop_music(self):
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
    def __init__(self, max_y):
        self.x = 0
        self.y = 0
        self.max_y = max_y
    
    def update(self, players):        
        self.x = max(0, sum(player.rect.x + player.rect.width for player in players) / len(players) - SCREEN_WIDTH // 2)
        self.y = max(0, min(sum(player.rect.y + player.rect.height for player in players) / len(players) - SCREEN_HEIGHT // 2, self.max_y))

class Logo:
    def __init__(self):
        self.x = centerx - 88
        self.y = -88
        self.speedy = 0
        self.timer = 0
        self.bounce_time = 3
        self.spritesheet = load_sprite("logo")

    def update(self):
        self.timer = min(self.timer + 1, self.bounce_time * FPS)
        canbounce = self.y < 64
        if self.timer < self.bounce_time * FPS:
            self.y += self.speedy
            self.speedy += 0.25
        if self.y > 64 and canbounce and self.speedy != 0 and self.timer > 0:
            sound_player.play_sound(bump_sound)
            self.speedy /= -1.5
            self.y -= 0.25
        if self.timer == self.bounce_time * FPS and self.y > 64:
            sound_player.play_sound(bump_sound)
            self.speedy = 0
            self.y = 64

    def draw(self):
        screen.blit(self.spritesheet, (self.x, self.y))

class TitleGround:
    def __init__(self, y):
        self.y = y
        self.sprite = load_sprite("groundtile")

    def check_collision(self, mario):
        mario.on_ground = mario.rect.bottom >= self.y
        if mario.rect.bottom >= self.y:
            mario.rect.bottom = self.y

    def draw(self):
        offset_x = -camera.x % 16
        for y in range(2):
            for x in range(0, SCREEN_WIDTH + 32, 16):
                screen.blit(self.sprite, (x + offset_x - 16, self.y + 16 * y - camera.y))

class Ground:
    def __init__(self, y):
        self.y = y

    def check_collision(self, mario):
        mario.on_ground = mario.rect.bottom >= self.y
        if mario.rect.bottom >= self.y:
            mario.rect.bottom = self.y

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
        
class Player:
    def __init__(self, x, y, character="mario", acceleration=0.1, max_jump=4, controls_enabled=True, speedx=0):
        self.spritesheet = load_sprite(character)
        self.controls_enabled = controls_enabled
        self.character = character
        self.rect = pygame.Rect(x, y, 20, 102)
        self.speedx = speedx
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
        self.color = {
            "mario": (247, 57, 16),
            "luigi": (33, 173, 16),
            "yellowtoad": (230, 158, 18),
            "bluetoad": (80, 80, 255)
        }
        self.sprites = [[pygame.Rect(x * 20, y * 34, 20, 34) for x in range(18)] for y in range(3)]
        self.size = 1
        self.acceleration = acceleration
        self.max_jump = max_jump
        self.skidding = False
        self.gravity = 0.25
        self.min_jump = 1
        self.run_timer = 0
        self.jump_lock = False
        self.update_hitbox()
        self.rect.y -= self.rect.height
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

    def update(self, ground):
        if self.controls_enabled:
            self.left = self.controls["left"]
            self.right = self.controls["right"]
            self.crouch = self.controls["down"] if self.on_ground else self.crouch
            self.run = self.controls["run"]
            self.jump = self.controls["jump"]
            self.speed = RUN_SPEED if self.run else WALK_SPEED

        self.update_hitbox()

        if self.on_ground and self.controls_enabled and not self.crouch:
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
            self.run_timer = range_number(self.run_timer + 1 if abs(self.speedx) == RUN_SPEED else self.run_timer - 1, MIN_RUN_TIMER, MAX_RUN_TIMER)
        else:
            if not self.pspeed:
                self.run_timer = max(self.run_timer - 1, MIN_RUN_TIMER)

        new_x = self.rect.x + self.speedx

        if new_x < camera.x and self.speedx < 0:
            self.speedx = 0
        elif new_x + self.rect.width > camera.x + SCREEN_WIDTH and self.speedx > 0:
            self.speedx = 0
        else:
            self.rect.x = new_x

        self.rect.y += self.speedy
        self.rect.x = max(camera.x, min(self.rect.x, camera.x + SCREEN_WIDTH - self.rect.width))
        self.rect.y = max(camera.y, min(self.rect.y, camera.y + SCREEN_HEIGHT - self.rect.height))
        
        ground.check_collision(self)
        if self.on_ground:
            self.speedy = 0
            if self.crouch:
                if self.speedx > 0:
                    self.speedx -= self.acceleration
                elif self.speedx < 0:
                    self.speedx += self.acceleration

        if self.crouch:
            self.anim_state = 3 if self.speedy > 0 else 2
        elif self.skidding:
            self.anim_state = 10
        elif self.speedy < 0:
            self.anim_state = 16 if self.pspeed else 11
        elif self.speedy >= 0 and nor(self.on_ground, self.crouch):
            self.anim_state = 17 if self.pspeed else 12
        elif self.speedx == 0 and self.on_ground and not self.crouch:
            self.anim_state = 1
            self.speedx = 0
        elif abs(self.speedx) > 0 and self.on_ground and not self.pspeed:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = 4 + int(self.frame_timer // 6) % 6
        elif self.pspeed and self.on_ground:
            self.frame_timer += abs(self.speedx) / 1.25
            self.anim_state = 13 + int(self.frame_timer // 6) % 3

    def draw(self):
        sprite = self.spritesheet.subsurface(self.sprites[self.size][self.anim_state - 1])
        sprite = pygame.transform.flip(sprite, not self.facing_right, False)
        draw_x = self.rect.x - camera.x + (((1 if self.character == "mario" else 2 if self.character == "luigi" else 0) if self.anim_state == 16 or self.anim_state == 17 else 0) * (1 if not self.facing_right else -1))
        draw_y = self.rect.y - camera.y + self.rect.height - 32
        screen.blit(sprite, (draw_x, draw_y))

mus_vol = 1
snd_vol = 1
vsync = False
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
    "up": pygame.K_KP_8,
    "down": pygame.K_KP_5,
    "left": pygame.K_KP_4,
    "right": pygame.K_KP_6,
    "run": pygame.K_b,
    "jump": pygame.K_q,
    "pause": pygame.K_KP_0
}
fullscreen = False
deadzone = 0.5

if path.exists(f"{path.dirname(path.abspath(__file__))}/settings.json"):
    with open(f"{path.dirname(path.abspath(__file__))}/settings.json", "r") as file:
        data = json.load(file)
        mus_vol = data.get("mus_vol", mus_vol)
        snd_vol = data.get("snd_vol", snd_vol)
        vsync = data.get("vsync", vsync)
        controls = data.get("controls", controls)
        controls2 = data.get("controls2", controls2)
        controls3 = data.get("controls3", controls3)
        controls4 = data.get("controls4", controls4)
        deadzone = data.get("deadzone", deadzone)
        fullscreen = data.get("fullscreen", fullscreen)

running = True
centerx = SCREEN_WIDTH / 2
centery = SCREEN_HEIGHT / 2
font = pygame.font.Font(f"{path.dirname(path.abspath(__file__))}/font.ttf", 16)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
clock = pygame.time.Clock()
pygame.display.set_icon(load_sprite("icon"))
pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
player_dist = 20
intro_players = [Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, character=c, controls_enabled=False, speedx=1.25, **a) for i, (c, a) in enumerate([("mario", {}), ("luigi", {"acceleration": 0.05, "max_jump": 5}), ("yellowtoad", {"acceleration": 0.2}), ("bluetoad", {"acceleration": 0.25})])]
camera = Camera(24)
bgm_player = BGMPlayer()
sound_player = SFXPlayer()
title_ground = TitleGround(SCREEN_HEIGHT)
background_manager = Background()
beep_sound = load_sound("beep")
bump_sound = load_sound("bump")
coin_sound = load_sound("coin")
jump_sound = load_sound("jump")
jumpbig_sound = load_sound("jumpbig")
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
dt = 0
menu_area = 1
menu = True
title = True
binding_key = False
current_bind = False

if pygame.joystick.get_count() > 0:
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        joystick.init()

while running:
    if menu:
        bgm_player.set_volume(mus_vol)
        sound_player.set_volume(snd_vol)
        pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
        vsync_text = "on" if vsync else "off"
        title_screen = [
            [
                ["1 player game", centery],
                ["2 player game", centery * 1.125],
                ["3 player game", centery * 1.25],
                ["4 player game", centery * 1.375],
                ["options", centery * 1.5]
            ],
            [
                ["controls (p1)", centery],
                ["controls (p2)", centery * 1.1],
                ["controls (p3)", centery * 1.2],
                ["controls (p4)", centery * 1.3],
                ["music volume:", centery * 1.4, mus_vol],
                ["sound volume:", centery * 1.5, snd_vol],
                ["vsync:", centery * 1.6, vsync_text],
                ["back", centery * 1.75]
            ],
            [
                ["up (p1):", centery, controls["up"]],
                ["down (p1):", centery * 1.1, controls["down"]],
                ["left (p1):", centery * 1.2, controls["left"]],
                ["right (p1):", centery * 1.3, controls["right"]],
                ["run (p1):", centery * 1.4, controls["run"]],
                ["jump (p1):", centery * 1.5, controls["jump"]],
                ["pause (p1):", centery * 1.6, controls["pause"]],
                ["back", centery * 1.75]
            ],
            [
                ["up (p2):", centery, controls2["up"]],
                ["down (p2):", centery * 1.1, controls2["down"]],
                ["left (p2):", centery * 1.2, controls2["left"]],
                ["right (p2):", centery * 1.3, controls2["right"]],
                ["run (p2):", centery * 1.4, controls2["run"]],
                ["jump (p2):", centery * 1.5, controls2["jump"]],
                ["pause (p2):", centery * 1.6, controls2["pause"]],
                ["back", centery * 1.75]
            ],
            [
                ["up (p3):", centery, controls3["up"]],
                ["down (p3):", centery * 1.1, controls3["down"]],
                ["left (p3):", centery * 1.2, controls3["left"]],
                ["right (p3):", centery * 1.3, controls3["right"]],
                ["run (p3):", centery * 1.4, controls3["run"]],
                ["jump (p3):", centery * 1.5, controls3["jump"]],
                ["pause (p3):", centery * 1.6, controls3["pause"]],
                ["back", centery * 1.75]
            ],
            [
                ["up (p4):", centery, controls4["up"]],
                ["down (p4):", centery * 1.1, controls4["down"]],
                ["left (p4):", centery * 1.2, controls4["left"]],
                ["right (p4):", centery * 1.3, controls4["right"]],
                ["run (p4):", centery * 1.4, controls4["run"]],
                ["jump (p4):", centery * 1.5, controls4["jump"]],
                ["pause (p4):", centery * 1.6, controls4["pause"]],
                ["back", centery * 1.75]
            ]
        ]
        dt += 1
        screen.fill((0, 0, 0))
        background_manager.load_background("ground", 4)
        background_manager.update()
        background_manager.draw()
        keys = pygame.key.get_pressed()

        menu_options = title_screen[menu_area - 1]

        with open(f"{path.dirname(path.abspath(__file__))}/settings.json", "w") as settings:
            json.dump(
                {
                    "mus_vol": mus_vol,
                    "snd_vol": snd_vol,
                    "vsync": vsync,
                    "controls": controls,
                    "controls2": controls2,
                    "controls3": controls3,
                    "controls4": controls4,
                    "deadzone": deadzone,
                    "fullscreen": fullscreen
                }, settings)
        
        controls_table = [controls, controls2, controls3, controls4]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                    fullscreen = not fullscreen
                    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
                if nor(title, fade_in, fade_out):
                    if binding_key:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                sound_player.play_sound(pipe_sound)
                            else:
                                sound_player.play_sound(powerup_sound)
                                controls_table[menu_area - 3][selected_menu_index] = event.key
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
                                sound_player.play_sound(beep_sound)
                            elif selected_menu_index == 5:
                                snd_vol -= 0.1
                                sound_player.play_sound(beep_sound)
                    elif event.key == controls["right"]:
                        if menu_options == title_screen[1]:
                            if selected_menu_index == 4:
                                mus_vol += 0.1
                                sound_player.play_sound(beep_sound)
                            elif selected_menu_index == 5:
                                snd_vol += 0.1
                                sound_player.play_sound(beep_sound)
                    elif event.key == controls["jump"]:
                        if menu_options == title_screen[0]:
                            if selected_menu_index == 4:
                                selected_menu_index = 0
                                old_selected_menu_index = 0
                                menu_area = 2
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
                            elif selected_menu_index == 6:
                                vsync = not vsync
                                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0), vsync=vsync)
                                sound_player.play_sound(coin_sound)
                            elif selected_menu_index == 7:
                                selected_menu_index = 0
                                old_selected_menu_index = 0
                                menu_area = 1
                                sound_player.play_sound(coin_sound)
                        elif menu_options == title_screen[2] or menu_options == title_screen[3] or menu_options == title_screen[4] or menu_options == title_screen[5]:
                            if selected_menu_index == 7:
                                selected_menu_index = 0
                                old_selected_menu_index = 0
                                menu_area = 2
                                sound_player.play_sound(coin_sound)
                            else:
                                bind_table = ["left", "right", "up", "down", "run", "jump", "pause"]
                                binding_key = True
                                current_bind = bind_table[selected_menu_index]
                                sound_player.play_sound(sprout_sound)
                                sound_player.stop_sound(powerup_sound)
        
            if event.type == pygame.JOYBUTTONDOWN:
                joystick = joysticks[event.joy]
                if binding_key:
                    if current_bind:
                        if current_bind in controls_table[event.joy]:
                            controls[selected_menu_index] = joystick.get_button(event.button)
                    binding_key = False
                    current_bind = False
                    sound_player.play_sound(powerup_sound)
                    sound_player.stop_sound(sprout_sound)

            if event.type == pygame.JOYAXISMOTION:
                joystick = joysticks[event.joy]
                if abs(joystick.get_axis(0)) > deadzone:
                    if binding_key:
                        controls_table[event.joy][selected_menu_index] = event.axis
                    else:
                        pass

        selected_menu_index = range_number(selected_menu_index, 0, len(menu_options) - 1)
        mus_vol = round(range_number(mus_vol, 0, 1) * 10) / 10
        snd_vol = round(range_number(snd_vol, 0, 1) * 10) / 10
        if old_selected_menu_index != selected_menu_index:
            sound_player.play_sound(beep_sound)
        old_selected_menu_index = selected_menu_index
        
        for player in intro_players:
            player.update(title_ground)
        
        camera.update(intro_players)
        
        title_ground.draw()

        for player in intro_players:
            player.draw()

        pspeed_sound.set_volume(0 if is_playing(jump_sound) or is_playing(jumpbig_sound) else 1)

        if fade_in:
            fade_out = False
            a += 255 / FADE_DURATION
            if a >= 255:
                a = 255
                fade_in = False

        elif fade_out:
            fade_in = False
            a -= 255 / FADE_DURATION
            if a <= 0:
                a = 0
                fade_out = False

        if menu_options == title_screen[0]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                text = options[0]
                y = options[1]
                
                display_text = text
                if i == selected_menu_index:
                    display_text = f"> {display_text} <"

                create_text(
                    text=display_text.upper(),
                    position=(centerx, y),
                    alignment="center",
                    stickxtocamera=True
                )
        elif menu_options == title_screen[1]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                text = options[0]
                y = options[1]
                if len(options) == 3:
                    state = str(options[2])
                    if i == 4 or i == 5:
                        state = f"{int(float(state) * 100)}%"
                    display_state = state
                    if i == selected_menu_index:
                        display_state = f"{display_state} <"

                    create_text(
                        text=display_state.upper(),
                        position=(centerx * 1.5 + (18 if get_last_chars(display_state, 2) == " <" else 0), y),
                        alignment="right",
                        stickxtocamera=True
                    )
                
                display_text = text
                if i == selected_menu_index:
                    display_text = f"> {display_text}"
                    if (selected_menu_index >= 0 and selected_menu_index <= 3) or selected_menu_index == 7:
                        display_text = f"{display_text} <"

                create_text(
                    text=display_text.upper(),
                    position=(centerx / 2 - (18 if get_chars(display_text, 2) == "> " else 0), y),
                    alignment="left",
                    stickxtocamera=True
                )
        elif menu_options == title_screen[2] or menu_options == title_screen[3] or menu_options == title_screen[4] or menu_options == title_screen[5]:
            for i in range(len(menu_options)):
                options = menu_options[i]
                text = options[0]
                y = options[1]
                if len(options) == 3:
                    state = "waiting for key..." if binding_key and selected_menu_index == i else pygame.key.name(options[2])
                    if binding_key and selected_menu_index == i:
                        create_text(
                            text="PRESS ESC TO CANCEL BINDING",
                            position=(centerx, centery * 0.875),
                            alignment="center",
                            stickxtocamera=True
                        )
                    display_state = state
                    if i == selected_menu_index:
                        display_state = f"{display_state} <"

                    create_text(
                        text=display_state.upper(),
                        position=(centerx * 1.5 + (18 if get_last_chars(display_state, 2) == " <" else 0), y),
                        alignment="right",
                        stickxtocamera=True
                    )
                
                display_text = text
                if i == selected_menu_index:
                    display_text = f"> {display_text}"
                    if selected_menu_index == 7:
                        display_text = f"{display_text} <"

                create_text(
                    text=display_text.upper(),
                    position=(centerx / 2 - (18 if get_chars(display_text, 2) == "> " else 0), y),
                    alignment="left",
                    stickxtocamera=True
                )

        if dt / FPS >= logo.bounce_time + 1:
            logo.draw()
            logo.update()

        fade_surface.fill((0, 0, 0, a))
        screen.blit(fade_surface, (0, 0))

        if dt / FPS < logo.bounce_time + 1:
            logo.draw()
            logo.update()
        
        if dt / FPS >= logo.bounce_time and title:
            bgm_player.play_music("title")
            fade_out = True
            title = False
        
        bgm_player.update()
        pygame.display.flip()
        clock.tick(FPS)

pygame.quit()
