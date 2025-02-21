import pygame, json, math
from os.path import dirname, abspath, exists, getsize

pygame.init()
pygame.font.init()
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

def is_playing(sound):
    return sound.get_num_channels() > 0

def nand(*conditions):
    return not all(conditions)

def nor(*conditions):
    return not any(conditions)

def get_first_chars(string, chars):
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

def create_pipe(x, y, length, pipe_dir="up", color=1):
    pipes = []
    if pipe_dir == "up":
        for i in range(2):
            for j in range(length):
                pipe_id = i + (j * 2) + 1
                while pipe_id >= 5:
                    pipe_id -= 2
                pipes.append(Tile(x + i, y + j, f"pipe{pipe_id}", color))
    elif pipe_dir == "down":
        for i in range(2):
            for j in range(length):
                pipe_id = i + (j * 2) + 1
                while pipe_id >= 5:
                    pipe_id -= 2
                pipes.append(Tile(x + i, y - j, f"pipe{pipe_id + (4 if pipe_id == 1 or pipe_id == 2 else 0)}", color))
    elif pipe_dir == "left":
        for i in range(2):
            for j in range(length):
                pipe_id = i + (j * 2) + 1
                while pipe_id >= 5:
                    pipe_id -= 2
                pipes.append(Tile(x - j, y - i, f"pipe{pipe_id + (pipe_id == 3) * 8 + (pipe_id == 4) * 4 + (pipe_id == 1) * 11 + (pipe_id == 2) * 7}", color))
    elif pipe_dir == "right":
        for i in range(2):
            for j in range(length):
                pipe_id = i + (j * 2) + 1
                while pipe_id >= 5:
                    pipe_id -= 2
                pipes.append(Tile(x + j, y - i, f"pipe{pipe_id + (pipe_id == 3) * 8 + (pipe_id == 4) * 4 + (pipe_id == 1) * 9 + (pipe_id == 2) * 5}", color))
    return pipes

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 400
WALK_SPEED = 2.5
RUN_SPEED = 4
JUMP_HOLD_TIME = 10
MIN_SPEEDX = math.pi / 10
MIN_RUN_TIMER = 0
MAX_RUN_TIMER = 75
FPS = 60
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
        self.sounds[sound] = sound
        if sound in self.sounds and not is_playing(self.sounds[sound]):
            self.sounds[sound].set_volume(snd_vol)
            self.sounds[sound].play(-1)

    def set_volume(self, volume):
        for sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)

class BGMPlayer:
    def __init__(self):
        self.loop_point = 0
        self.music_playing = False

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
                pygame.mixer.music.play(-1, self.loop_point)
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
            sum(player.rect.x + player.rect.width for player in players) / len(players) - SCREEN_WIDTH // 2,
            0, (max_x if max_x else infinity)
        )
        self.y = range_number(
            sum(player.rect.y + player.rect.height for player in players) / len(players) - SCREEN_HEIGHT // 2,
            0, (max_y if max_y else infinity)
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

    def check_collision(self, obj, speedy=0):
        obj.on_ground = obj.rect.bottom >= self.y
        if obj.rect.bottom >= self.y:
            obj.rect.bottom = self.y
            obj.y = self.y - 16
            
            if obj.speedy > 0:
                obj.speedy = speedy

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
        screen.blit(self.spritesheet.subsurface(self.frames[self.current_frame]), (12, 32 + self.player.player_number * 12))

class Tile:
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False):
        self.x = x * 16
        self.y = y * 16 + 8
        self.spriteset = spriteset - 1
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

        self.broken = False
        
        self.bouncing = False
        self.bounce_timer = 0
        self.bounce_speed = 0
        self.y_offset = 0
        self.can_break_now = False

    def update(self):
        if self.bouncing:
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
        self.can_break_now = self.breakable
        self.bouncing = True

    def draw(self):
        if 0 <= self.spriteset < self.rows and not self.broken:
            screen.blit(self.image.subsurface(self.sprites[self.spriteset]), (self.x - camera.x, self.y - camera.y + (self.y_offset * (-1 if nitpicks["inverted_block_bounce"] else 1))))

class AnimatedTile(Tile):
    def __init__(self, x, y, image, spriteset, left_collide=True, right_collide=True, top_collide=True, bottom_collide=True, bonk_bounce=False, breakable=False):
        super().__init__(x, y, image, spriteset, left_collide, right_collide, top_collide, bottom_collide, bonk_bounce, breakable)

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
        if 0 <= self.spriteset < self.rows and 0 <= self.frame_index < self.cols and not self.broken:
            screen.blit(self.image.subsurface(self.sprites[self.spriteset][self.frame_index]), (self.x - camera.x, self.y - camera.y + (self.y_offset * (-1 if nitpicks["inverted_block_bounce"] else 1))))

class Brick(AnimatedTile):
    def __init__(self, x, y, spriteset=1):
        super().__init__(x, y, "brick", spriteset, bonk_bounce=True, breakable=True)

    def update(self):
        super().update()

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
    
    def draw(self):
        if self.rotated_image:
            screen.blit(self.rotated_image, (self.x - camera.x, self.y - camera.y))

class Mushroom:
    def __init__(self, x, y):
        self.x, self.y = x * 16, y * 16 + 8
        self.sprite = load_sprite("mushroom")
        self.speedx = 2
        self.speedy = 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25
        self.size = 1

    def update(self):
        self.x += self.speedx
        self.rect.topleft = (self.x, self.y)

        for tile in tiles:
            if tile.broken:
                continue
            if self.rect.colliderect(tile.rect):
                if self.speedx > 0:
                    self.x = tile.rect.left - self.rect.width
                elif self.speedx < 0:
                    self.x = tile.rect.right
                self.speedx *= -1
                break

        self.y += self.speedy
        self.speedy += self.gravity
        self.rect.topleft = (self.x, self.y)

        title_ground.check_collision(self)
        self.rect.topleft = (self.x, self.y)

        for tile in tiles:
            if tile.broken:
                continue
            if self.rect.colliderect(tile.rect):
                if self.speedy > 0:
                    self.y = tile.rect.top - self.rect.height
                    self.speedy = -math.pi if tile.bouncing else 0
                elif self.speedy < 0:
                    self.y = tile.rect.bottom
                    self.speedy = 0
                break

        self.rect.topleft = (self.x, self.y)

    def is_visible(self):
        return (
            ((self.x > camera.x and self.x < camera.x + SCREEN_WIDTH) or
            (self.x + self.rect.width > camera.x and self.x + self.rect.width < camera.x + SCREEN_WIDTH)) and
            ((self.y > camera.y and self.y < camera.y + SCREEN_HEIGHT) or
            (self.y + self.rect.height > camera.y and self.y + self.rect.height < camera.y + SCREEN_HEIGHT))
        )

    def draw(self):
        screen.blit(self.sprite, (self.x - camera.x, self.y - camera.y))

class FireFlower:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.spriteset = spriteset - 1
        self.sprite = load_sprite("fireflower")
        self.sprites = [[pygame.Rect(i * 16, j * 16, 16, 16) for i in range(4)] for j in range(4)]
        self.speedx = 0
        self.speedy = 0
        self.rect = pygame.Rect(self.x, self.y, 16, 16)
        self.gravity = 0.25
        self.size = 2
        self.frame_index = 0

    def update(self):
        self.rect.topleft = (self.x, self.y)

        self.y += self.speedy
        self.speedy += self.gravity
        self.rect.topleft = (self.x, self.y)

        title_ground.check_collision(self)
        self.rect.topleft = (self.x, self.y)

        for tile in tiles:
            if tile.broken:
                continue
            if self.rect.colliderect(tile.rect):
                if self.speedy > 0:
                    self.y = tile.rect.top - self.rect.height
                    self.speedy = -math.pi if tile.bouncing else 0
                elif self.speedy < 0:
                    self.y = tile.rect.bottom
                    self.speedy = 0
                break

        self.rect.topleft = (self.x, self.y)
        self.frame_index = int((dt / 4) % 4)

    def is_visible(self):
        return (
            ((self.x > camera.x and self.x < camera.x + SCREEN_WIDTH) or
            (self.x + self.rect.width > camera.x and self.x + self.rect.width < camera.x + SCREEN_WIDTH)) and
            ((self.y > camera.y and self.y < camera.y + SCREEN_HEIGHT) or
            (self.y + self.rect.height > camera.y and self.y + self.rect.height < camera.y + SCREEN_HEIGHT))
        )

    def draw(self):
        screen.blit(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), (self.x - camera.x, self.y - camera.y))

class Fireball:
    def __init__(self, player):
        self.x = player.rect.centerx - player.rect.width / 2
        self.y = player.rect.bottom - player.rect.width
        self.bounce = 2.5
        self.speedx = RUN_SPEED * (1.25 if player.facing_right else -1.25)
        self.speedy = self.bounce
        self.rect = pygame.Rect(self.x, self.y, 8, 8)
        self.sprite = load_sprite("fireball")
        self.sprites = [[pygame.Rect(i * 16, j * 16, 16, 16) for i in range(4)] for j in range(4)]
        self.spriteset = player.player_number - 1
        self.angle = 0
        self.frame_index = 0
        self.frame_timer = 0
        self.destroyed = False
        self.gravity = 0.25
        self.player = player

    def update(self):
        if self.destroyed:
            self.frame_timer += 1
            self.frame_index = math.floor(min(self.frame_timer / 5, 3))
            if self.frame_timer >= 20:
                fireball_table = [fireballs, fireballs2, fireballs3, fireballs4]
                fireball_table[self.player.player_number - 1].remove(self)
        else:
            self.angle -= 12 * (-1 if self.speedx < 0 else 1)

            self.x += self.speedx
            self.rect.topleft = (self.x, self.y)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedx > 0:
                        self.x = tile.rect.left - self.rect.width
                    elif self.speedx < 0:
                        self.x = tile.rect.right
                    self.destroy()
                    return

            self.y += self.speedy
            self.speedy += self.gravity
            self.rect.topleft = (self.x, self.y)

            title_ground.check_collision(self, -self.bounce)

            for tile in tiles:
                if tile.broken:
                    continue
                if self.rect.colliderect(tile.rect):
                    if self.speedy > 0:
                        self.y = tile.rect.top - self.rect.height
                        self.speedy = -self.bounce
                    elif self.speedy < 0:
                        self.y = tile.rect.bottom
                        self.speedy = 0
                        self.destroy()
                        return
                    break

            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    self.destroy()
                    enemy.shot()

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
            ((self.x > camera.x and self.x < camera.x + SCREEN_WIDTH) or
            (self.x + self.rect.width > camera.x and self.x + self.rect.width < camera.x + SCREEN_WIDTH)) and
            ((self.y > camera.y and self.y < camera.y + SCREEN_HEIGHT) or
            (self.y + self.rect.height > camera.y and self.y + self.rect.height < camera.y + SCREEN_HEIGHT))
        )

    def draw(self):
        screen.blit(pygame.transform.rotate(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), self.angle), (self.x - camera.x, self.y - camera.y - 3))

class Goomba:
    def __init__(self, x, y, spriteset=1):
        self.x, self.y = x * 16, y * 16 + 8
        self.spriteset = spriteset - 1
        self.sprite = load_sprite("goomba")
        self.sprites = [[pygame.Rect(i * 20, j * 20, 20, 20) for i in range(23)] for j in range(4)]
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
            self.frame_index = 20
            if self.rect.top >= SCREEN_HEIGHT:
                enemies.remove(self)
        else:
            if self.stomped:
                self.frame_index = min(int((self.dt / 5) + 21), 22)
                self.dt += 1
                if self.dt >= 30:
                    enemies.remove(self)
            else:
                self.dt = dt
                self.x += self.speedx
                self.rect.topleft = (self.x, self.y)

                for tile in tiles:
                    if tile.broken:
                        continue
                    if self.rect.colliderect(tile.rect):
                        if self.speedx > 0:
                            self.x = tile.rect.left - self.rect.width
                        elif self.speedx < 0:
                            self.x = tile.rect.right
                        self.speedx *= -1
                        break

                self.y += self.speedy
                self.speedy += self.gravity
                self.rect.topleft = (self.x, self.y)

                title_ground.check_collision(self)
                self.rect.topleft = (self.x, self.y)

                for tile in tiles:
                    if tile.broken:
                        continue
                    if self.rect.colliderect(tile.rect):
                        if self.speedy > 0:
                            self.y = tile.rect.top - self.rect.height
                            self.speedy = 0
                            if tile.bouncing:
                                self.shot()
                        elif self.speedy < 0:
                            self.y = tile.rect.bottom
                            self.speedy = 0
                        break

                self.rect.topleft = (self.x, self.y)
                self.frame_index = int((self.dt / 5) % 20)

    def stomp(self):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.stomped = True
        self.shotted = False
        self.dt = 0
        sound_player.play_sound(stomp_sound)

    def shot(self):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.shotted = True
        self.stomped = False
        self.speedx = 2 if self.speedx < 0 else -2
        self.speedy = -math.pi * 2
        sound_player.play_sound(shot_sound)

    def is_visible(self):
        return (
            ((self.x > camera.x and self.x < camera.x + SCREEN_WIDTH) or
            (self.x + self.rect.width > camera.x and self.x + self.rect.width < camera.x + SCREEN_WIDTH)) and
            ((self.y > camera.y and self.y < camera.y + SCREEN_HEIGHT) or
            (self.y + self.rect.height > camera.y and self.y + self.rect.height < camera.y + SCREEN_HEIGHT))
        )

    def draw(self):
        rotated_image = pygame.transform.rotate(self.sprite.subsurface(self.sprites[self.spriteset][self.frame_index]), self.angle)
        new_rect = rotated_image.get_rect(center=(self.x - camera.x + 10, self.y - camera.y + 10 - 3))
        screen.blit(rotated_image, new_rect.topleft)

class Player:
    def __init__(self, x, y, size=0, walk_frames=6, run_frames=3, character="mario", controls_enabled=True, walk_cutscene=False, player_number=1):
        self.spritesheet = load_sprite(character)
        self.controls_enabled = controls_enabled
        self.can_control = controls_enabled
        self.character = character
        self.speedx = 0
        self.speedy = 0
        self.jump_speedx = 0
        self.frame_timer = 0
        self.on_ground = False
        self.facing_right = True
        self.jump_timer = 0
        self.anim_state = 1
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.run = False
        self.jump = False
        self.prev_run = False
        self.run_lock = False
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
        self.walk_cutscene = walk_cutscene
        self.properties = {
            "mario": [controls, 0.1, 4],
            "luigi": [controls2, 0.05, 5],
            "yellowtoad": [controls3, 0.2, 4],
            "bluetoad": [controls4, 0.25, 4]
        }
        self.controls, self.acceleration, self.max_jump = self.properties[character]
        self.skidding = False
        self.gravity = 0.25
        self.min_jump = 1
        self.run_timer = 0
        self.update_hitbox()
        self.rect.y -= self.rect.height
        self.carrying_item = False
        self.fall_timer = 0
        self.fall_duration = 0.125
        self.falling = True
        self.pspeed = False
        self.player_number = player_number
        self.grow_animation = []
        self.grow_timer = 0
        self.old_controls = False
        self.fire_timer = 0
        self.fire_duration = 5
        self.fire_lock = False

    def update_hitbox(self):
        prev_bottom = self.rect.bottom
        new_width, new_height = (16, 16 if self.size == 0 else 24) if not self.down else (16, 8 if self.size == 0 else 16)
        self.rect.width, self.rect.height = new_width, new_height
        self.rect.bottom = prev_bottom

    def update(self):
        self.left = (keys[self.controls["left"]]) if self.controls_enabled and self.can_control else False
        self.right = (keys[self.controls["right"]]) if self.controls_enabled and self.can_control else False
        self.up = (keys[self.controls["up"]]) if self.controls_enabled and self.can_control else False
        self.down = (keys[self.controls["down"]] if self.fall_timer < self.fall_duration else self.down) if self.controls_enabled and self.can_control else False
        self.run = (keys[self.controls["run"]]) if self.controls_enabled and self.can_control else False
        self.jump = (keys[self.controls["jump"]]) if self.controls_enabled and self.can_control else False
        self.speed = RUN_SPEED if self.run else WALK_SPEED

        self.run_lock = self.run and not self.prev_run

        fireball_table = [fireballs, fireballs2, fireballs3, fireballs4]

        if self.size == 2 and len(fireball_table[self.player_number - 1]) < max_fireballs:
            if self.run:
                if self.fire_timer < self.fire_duration:
                    if self.fire_timer == 0:
                        sound_player.play_sound(fireball_sound)
                        fireball_table[self.player_number - 1].append(Fireball(self))
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

        self.update_hitbox()

        if self.fall_timer < self.fall_duration:
            if self.down:
                self.speedx *= (1 - self.acceleration)
            else:
                if self.left and not self.right:
                    self.speedx = max(self.speedx - self.acceleration, -self.speed)
                    self.facing_right = False if self.fall_timer < self.fall_duration else self.facing_right
                elif self.right and not self.left:
                    self.speedx = min(self.speedx + self.acceleration, self.speed)
                    self.facing_right = True if self.fall_timer < self.fall_duration else self.facing_right
                else:
                    if not self.walk_cutscene:
                        self.speedx *= (1 - self.acceleration)
                        if abs(self.speedx) < MIN_SPEEDX:
                            self.speedx = 0
        else:
            if self.left and not self.right:
                self.speedx = max(self.speedx - self.acceleration, -self.speed)
            elif self.right and not self.left:
                self.speedx = min(self.speedx + self.acceleration, self.speed)

        if self.fall_timer < self.fall_duration and self.jump and not self.jump and self.jump_timer == 0:
            self.speedy = -self.min_jump
            self.jump_timer = 1
        elif self.jump and 0 < self.jump_timer < JUMP_HOLD_TIME:
            if self.jump_timer == 1 and self.fall_timer < self.fall_duration:
                sound_player.play_sound(jump_sound if self.size == 0 else jumpbig_sound)
                self.fall_timer = self.fall_duration
                self.jump_speedx = abs(self.speedx)
            self.max_speedx_jump = (self.max_jump + 1) if self.jump_speedx >= 1 else self.max_jump
            self.speedy = max(self.speedy - self.max_speedx_jump, -self.max_speedx_jump)
            self.jump_timer += 1
        elif not self.jump:
            self.jump_timer = 1 if self.fall_timer < self.fall_duration else 0

        self.pspeed = self.run_timer >= MAX_RUN_TIMER

        if self.can_control:
            if self.fall_timer < self.fall_duration and self.controls_enabled:
                if abs(self.speedx) == RUN_SPEED:
                    self.run_timer = range_number(self.run_timer + 1, MIN_RUN_TIMER, MAX_RUN_TIMER)
                else:
                    self.run_timer = range_number(self.run_timer - 1, MIN_RUN_TIMER, MAX_RUN_TIMER)
            elif not self.run_timer == MAX_RUN_TIMER:
                self.run_timer = range_number(self.run_timer - 1, MIN_RUN_TIMER, MAX_RUN_TIMER)

        if self.rect.left <= camera.x:
            self.rect.left = camera.x
            if self.rect.x <= camera.x and ((self.speedx < 0 and not self.facing_right and self.fall_timer >= self.fall_duration) or (self.speedx < 0 and self.facing_right and self.fall_timer < self.fall_duration)) or not self.right:
                self.speedx = 0

        if self.rect.right >= camera.x + SCREEN_WIDTH:
            self.rect.right = camera.x + SCREEN_WIDTH
            if self.rect.x >= camera.x + SCREEN_WIDTH and ((self.speedx > 0 and self.facing_right and self.fall_timer >= self.fall_duration) or (self.speedx > 0 and not self.facing_right and self.fall_timer < self.fall_duration)) or not self.left:
                self.speedx = 0

        if self.rect.top < camera.y:
            self.rect.top = camera.y
            self.speedy = 0
            self.jump_timer = 0

        self.rect.x += self.speedx
        for tile in tiles:
            if self.rect.colliderect(tile.rect) and not tile.broken:
                if self.speedx >= 0 and self.rect.right >= tile.rect.left:
                    self.rect.right = tile.rect.left
                    self.speedx = 0
                elif self.speedx <= 0 and self.rect.left <= tile.rect.right:
                    self.rect.left = tile.rect.right
                    self.speedx = 0

        self.rect.y += self.speedy
        self.on_ground = False
        title_ground.check_collision(self)
        for tile in tiles:
            if self.rect.colliderect(tile.rect) and not tile.broken:
                if self.speedy > 0 and self.rect.bottom >= tile.rect.top:
                    self.rect.bottom = tile.rect.top
                    self.speedy = 0
                    self.on_ground = True
                    self.falling = False
                    self.fall_timer = 0
                elif self.speedy < 0 and self.rect.top <= tile.rect.bottom:
                    self.rect.top = tile.rect.bottom
                    self.jump_timer = 0
                    self.speedy = 0
                    sound_player.play_sound(bump_sound)
                    if tile.bonk_bounce:
                        tile.bouncing = True
                        tile.bounce_speed = -2
                        tile.y_offset = 0
                    if not self.size == 0:
                        tile.break_block()

        if self.grow_animation:
            if self.can_control:
                self.old_controls = [self.left, self.right, self.up, self.down, self.run, self.jump, self.speedx, self.speedy, self.jump_timer, self.run_timer, self.fall_timer, self.falling, self.fire_timer]
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
            self.falling = False
            self.fire_timer = 0
            if self.grow_timer % 5 == 0:
                self.size = self.grow_animation.pop(0)
                self.update_hitbox()
            self.grow_timer += 1
        else:
            if self.controls_enabled and not self.can_control:
                self.left, self.right, self.up, self.down, self.run, self.jump, self.speedx, self.speedy, self.jump_timer, self.run_timer, self.fall_timer, self.falling, self.fire_timer = self.old_controls
            self.can_control = True
        
        for item in items:
            if self.rect.colliderect(item.rect):
                if self.size != item.size:
                    self.grow_timer = 0
                    old_size = 0 if self.size == 0 and item.size == 1 else self.size
                    self.grow_animation = [item.size, old_size, item.size, old_size, item.size, old_size, item.size]
                
                items.remove(item)
                sound_player.play_sound(powerup_sound)

        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                # Check if the player is falling and lands on top of the enemy
                if self.speedy > 0 and self.rect.bottom - enemy.rect.top < 5:
                    enemy.stomp()
                    
                    # Apply jump physics
                    self.speedy = -self.max_jump  # Bounce upwards with max jump strength
                    self.jump_timer = 1  # Reset jump timer to allow jump extension
                    self.on_ground = False  # Prevent player from being immediately grounded
                    self.fall_timer = self.fall_duration  # Reset fall timer for smooth bounce transition

        self.rect.x = range_number(camera.x + SCREEN_WIDTH - self.rect.width, camera.x, self.rect.x)
        self.rect.y = range_number(camera.y + SCREEN_HEIGHT - self.rect.height, camera.y, self.rect.y)

        self.skidding = (self.fall_timer < self.fall_duration and ((self.speedx < 0 and self.facing_right) or (self.speedx > 0 and not self.facing_right)) and not self.down)

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

        if self.can_control:
            if self.down:
                self.frame_timer = 0
                self.anim_state = (3 if self.speedy > 0 and self.fall_timer >= self.fall_duration else 2) + (8 + self.walk_frames + self.run_frames if self.carrying_item else 0)
            elif self.size == 2 and 0 < self.fire_timer < self.fire_duration and not self.fire_lock and not self.down:
                self.frame_timer = 0
                self.anim_state = self.walk_frames * 2 + self.run_frames + 17
            elif self.skidding:
                self.frame_timer = (self.frame_timer + abs(self.speedx) / 1.25) if self.carrying_item else 0
                self.anim_state = (12 + self.walk_frames + self.run_frames if self.carrying_item else 4) + int(self.frame_timer // FRAME_SPEED) % self.walk_frames if self.carrying_item else 4 + self.walk_frames
            elif self.speedy < 0:
                self.frame_timer = 0
                self.anim_state = ((12 + self.walk_frames + self.run_frames + (2 if self.pspeed else 0)) if self.carrying_item else (7 + self.run_frames if self.pspeed else 5)) + self.walk_frames
            elif self.speedy > 0 and self.fall_timer >= self.fall_duration and nor(self.on_ground, self.down):
                self.frame_timer = 0
                self.anim_state = ((13 + self.walk_frames + self.run_frames + (2 if self.pspeed else 0)) if self.carrying_item else (8 + self.run_frames if self.pspeed else 6)) + self.walk_frames
            elif self.speedx == 0 and self.on_ground and not self.down:
                self.frame_timer = 0
                self.anim_state = (9 + self.walk_frames + self.run_frames) if self.carrying_item else 1
                self.speedx = 0
            elif abs(self.speedx) > MIN_SPEEDX * 2 and self.fall_timer < self.fall_duration and (not self.pspeed or self.carrying_item):
                self.frame_timer += abs(self.speedx) / 1.25
                self.anim_state = (12 + self.walk_frames + self.run_frames if self.carrying_item else 4) + int(self.frame_timer // FRAME_SPEED) % self.walk_frames
            elif self.pspeed and self.fall_timer < self.fall_duration and not self.carrying_item:
                self.frame_timer += abs(self.speedx) / 1.25
                self.anim_state = 7 + self.walk_frames + int(self.frame_timer // FRAME_SPEED) % self.run_frames
        else:
            self.anim_state = 1
        
        self.prev_run = self.run

    def draw(self):
        sprite = self.spritesheet.subsurface(self.sprites[self.size][self.anim_state - 1])
        sprite = pygame.transform.flip(sprite, (not self.facing_right) ^ nitpicks["moonwalking_mario"], nitpicks["upside_down_mario"])
        draw_x = self.rect.x - camera.x - 2 + (((1 if self.character == "mario" else 2 if self.character == "luigi" else 0) if self.anim_state == 7 + self.run_frames + self.walk_frames or self.anim_state == 8 + self.run_frames + self.walk_frames or self.anim_state == 14 + self.run_frames + self.walk_frames * 2 or self.anim_state == 15 + self.run_frames + self.walk_frames * 2 else 0) * (1 if (not self.facing_right) ^ nitpicks["moonwalking_mario"] else -1))
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

nitpicks_list = [
    "upside_down_mario",
    "upside_down_enemies",
    "moonwalking_mario",
    "moonwalking_enemies",
    "inverted_block_bounce",
    "inverted_colors",
    "infinite_fireballs"
]

if exists(f"{main_directory}/nitpicks.json"):
    with open(f"{main_directory}/nitpicks.json", "r") as nitpicks:
        data = json.load(nitpicks)
        
    for key in nitpicks_list:
        if key not in data:
            data[key] = False
    
with open(f"{main_directory}/nitpicks.json", "w") as nitpicks:
    json.dump(data if exists(f"{main_directory}/nitpicks.json") else {key: False for key in nitpicks_list}, nitpicks, indent=4)

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
characters_table = ["mario", "luigi", "yellowtoad", "bluetoad"]
font = pygame.font.Font(f"{main_directory}/font.ttf", font_size)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE | (pygame.FULLSCREEN if fullscreen else 0))
clock = pygame.time.Clock()
pygame.display.set_icon(load_sprite("icon"))
pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
player_dist = 20
intro_players = [Player(x=centerx - player_dist / 2 + player_dist * i, y=SCREEN_HEIGHT, character=characters_table[i], controls_enabled=False, size=1) for i in range(len(characters_table))]
camera = Camera()
bgm_player = BGMPlayer()
sound_player = SFXPlayer()
title_ground = TitleGround()
background_manager = Background()
tiles = []
items = []
enemies = []
fireballs = []
fireballs2 = []
fireballs3 = []
fireballs4 = []
debris = []
lives = []
beep_sound = load_sound("beep")
break_sound = load_sound("break")
bump_sound = load_sound("bump")
coin_sound = load_sound("coin")
fireball_sound = load_sound("fireball")
jump_sound = load_sound("jump")
jumpbig_sound = load_sound("jumpbig")
oneup_sound = load_sound("oneup")
pipe_sound = load_sound("pipe")
powerup_sound = load_sound("powerup")
pspeed_sound = load_sound("pspeed")
shot_sound = load_sound("shot")
skid_sound = load_sound("skid")
sprout_sound = load_sound("sprout")
stomp_sound = load_sound("stomp")
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
game = False
numerical_change = 0.05
max_fireballs = infinity if nitpicks["infinite_fireballs"] else 2

while running:
    bgm_player.set_volume(mus_vol)
    sound_player.set_volume(snd_vol)
    SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
    pygame.display.set_caption(f"Super Mario Bros. for Python (FPS: {round(clock.get_fps())})")
    current_fps = FPS if clock.get_fps() == 0 else clock.get_fps()
    screen.fill((0, 0, 0))
    keys = pygame.key.get_pressed()
    
    controls_table = [controls, controls2, controls3, controls4]

    mus_vol = round(range_number(mus_vol, 0, 1) * (1 / numerical_change)) / (1 / numerical_change)
    snd_vol = round(range_number(snd_vol, 0, 1) * (1 / numerical_change)) / (1 / numerical_change)
    deadzone = round(range_number(deadzone, 0.1, 1) * (1 / numerical_change)) / (1 / numerical_change)
    if nand(old_mus_vol == mus_vol, old_snd_vol == snd_vol, old_deadzone == deadzone):
        sound_player.play_sound(beep_sound)
    old_mus_vol = mus_vol
    old_snd_vol = snd_vol
    old_deadzone = deadzone

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
                binding_key = False
                current_bind = False
            elif game_ready:
                menu = False
                game = True
                game_ready = False
                fade_out = True
                intro_players = None
                logo = None
                players = []
                power_meters = []
                fireballs = []
                fireballs2 = []
                fireballs3 = []
                fireballs4 = []
                tiles = [Brick(25 + i, 21 + j) for i in range(32) for j in range(3)]
                enemies = [Goomba(56, 20)]
                items = [FireFlower(25, 20)]
                dt = 0
                bgm_player.play_music("overworld")
                for i in range(player_count):
                    lives.append(3)
                    characters_table = ["mario", "luigi", "yellowtoad", "bluetoad"]
                    players.append(Player(x=48 + i * 8, y=SCREEN_HEIGHT, character=characters_table[i], player_number=i + 1))
                    power_meters.append(PowerMeter(players[i]))

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
            for player in intro_players:
                player.speedx = 2
                player.walk_cutscene = True

    elif game:
        dt += 1

        background_manager.load_background("ground", 4)
        background_manager.update()
        background_manager.draw()
        title_ground.draw()
        camera.update(players, False, 15)

        for power_meter in power_meters:
            power_meter.draw()
            if not any(player.grow_animation for player in players):
                power_meter.update()

        for tile in tiles:
            tile.draw()
            tile.update()

        for fireball in fireballs:
            fireball.draw()
            if fireball.is_visible() and not any(player.grow_animation for player in players):
                fireball.update()
            elif not fireball.is_visible():
                fireballs.remove(fireball)

        for fireball in fireballs2:
            fireball.draw()
            if fireball.is_visible() and not any(player.grow_animation for player in players):
                fireball.update()
            elif not fireball.is_visible():
                fireballs2.remove(fireball)

        for fireball in fireballs3:
            fireball.draw()
            if fireball.is_visible() and not any(player.grow_animation for player in players):
                fireball.update()
            elif not fireball.is_visible():
                fireballs3.remove(fireball)

        for fireball in fireballs4:
            fireball.draw()
            if fireball.is_visible() and not any(player.grow_animation for player in players):
                fireball.update()
            elif not fireball.is_visible():
                fireballs4.remove(fireball)

        for player in players:
            player.draw()
            player.update()

        for item in items:
            item.draw()
            if item.is_visible() and not any(player.grow_animation for player in players):
                item.update()

        for enemy in enemies:
            enemy.draw()
            if enemy.is_visible() and not any(player.grow_animation for player in players):
                enemy.update()

        if debris:
            for debris_part in debris:
                debris_part.draw()
                if not any(player.grow_animation for player in players):
                    debris_part.update()
                if debris_part.y >= SCREEN_HEIGHT + 16:
                    debris.remove(debris_part)

        (sound_player.loop_sound if any(player.pspeed for player in players) else sound_player.stop_sound)(pspeed_sound)
        (sound_player.loop_sound if any(player.skidding for player in players) else sound_player.stop_sound)(skid_sound)

        pspeed_sound.set_volume(0 if is_playing(jump_sound) or is_playing(jumpbig_sound) else 1)
    
    fade_surface.fill((0, 0, 0, a))
    screen.blit(fade_surface, (0, 0))

    if nor(game_ready, game, exit_ready):
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
                        elif selected_menu_index == 6:
                            deadzone -= numerical_change
                elif event.key == controls["right"]:
                    if menu_options == title_screen[1]:
                        if selected_menu_index == 4:
                            mus_vol += numerical_change
                        elif selected_menu_index == 5:
                            snd_vol += numerical_change
                        elif selected_menu_index == 6:
                            deadzone += numerical_change
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

    if nitpicks["inverted_colors"]:
        pygame.surfarray.blit_array(screen, 255 - pygame.surfarray.array3d(screen))

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
