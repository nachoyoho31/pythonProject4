import pygame
from os import path
import sqlite3 as sl
import time
from tkinter.simpledialog import askstring

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

# define font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)
font_record = pygame.font.SysFont('Bauhaus 93', 50)

# define game variables
tile_size = 50
game_over = 0
death_count = 0
main_menu = True
shop = False
level = 0
max_levels = 7
indexa = 0
score = 0
count = 0
save = 1
pred_teleport_time = 0
score_onlvlstart = 0

# define colours
white = (255, 255, 255)
blue = (0, 0, 255)

# load images

restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')
home_img = pygame.image.load('img/home_button.png')
shop_img = pygame.image.load('img/shop_btn.png')
arrowR_img = pygame.image.load('img/arrowsR.png')
arrowL_img = pygame.image.load('img/arrowsL.png')
setting = ['sun', 'moon', 'pirate']
sun_img = pygame.image.load(f'img/{setting[count]}/{setting[count]}.png')
bg_img = pygame.image.load(f'img/{setting[count]}/sky({setting[count]}).png')

# load sounds
pygame.mixer.music.load('music/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('music/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('music/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('music/game_over.wav')
game_over_fx.set_volume(0.5)


def change_setting():
    global count, sun_img, bg_img, world, world_data
    count += 1
    if count > len(setting) - 1:
        count = 0
    sun_img = pygame.image.load(f'img/{setting[count]}/{setting[count]}.png')
    bg_img = pygame.image.load(f'img/{setting[count]}/sky({setting[count]}).png')
    world_data = []
    change_button.image = pygame.image.load(f'img/{setting[count]}/change_btn({setting[count]}).png')
    world = reset_level(level)


def result_save(name, level, score, deaths, time, money):
    con = sl.connect('statistic.db')
    sql = 'INSERT INTO player_statistic (name,level, score, deaths, time, money) values(?, ?, ?, ?, ?, ?)'
    con.execute(sql, (name, level, score, deaths, time, money))
    con.commit()
    con.close()


def tablica():
    try:
        con = sl.connect('statistic.db')
        sql1 = """SELECT score FROM player_statistic"""
        d = con.execute(sql1).fetchall()
        print(max(d)[0])
        sql = f"""SELECT * FROM player_statistic WHERE score == {max(d)[0]}"""
        a = con.execute(sql).fetchall()
        a = list(a[0])
        sql1 = """SELECT money FROM player_statistic"""
        m = list(con.execute(sql1).fetchall())
        sql1 = """SELECT * FROM skins"""
        s = list(con.execute(sql1).fetchall())
        con.commit()
        con.close()
    except ValueError:
        a = ['', '', '', '', '', 0]
    return (f"name: {a[0]}", f"level: {a[1]}", f"score: {str(a[2]).upper()}",
            f"death: {a[3]}", f"time in game: {a[4]} секунд", m[-1][0], s)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# function to reset level
def reset_level(level):
    global save
    player.reset(100, screen_height - 130)
    print(level)
    blob_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()
    lamp_group.empty()
    flag_group.empty()
    palm_group.empty()
    chest_group.empty()
    tree_group.empty()
    button_group.empty()
    invis_group.empty()
    portalFrom_group.empty()
    portalTo_group.empty()

    # load in level data and create world
    if path.exists(f'levels/level{level}'):
        f = open(f'levels/level{level}', 'r')
        world_data = []
        for el in f.readlines():
            world_data.append(map(int, el.split(', ')[:len(el.split(', ')) - 1]))
    world = World(world_data)
    # create dummy coin for showing the score
    score_coin = Coin(tile_size // 2, tile_size // 2)
    coin_group.add(score_coin)
    return world


class Button:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button
        screen.blit(self.image, self.rect)

        return action


class Player:
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if game_over == 0:
            # get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and not self.jumped and not self.in_air:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if not key[pygame.K_SPACE]:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if not key[pygame.K_LEFT] and not key[pygame.K_RIGHT]:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # handle animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                elif self.direction == -1:
                    self.image = self.images_left[self.index]

            # add gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # check for collision
            self.in_air = True
            for tile in world.tile_list:
                # check for collision in x direction
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # check for collision in y direction
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if below the ground i.e. jumping
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # check if above the ground i.e. falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # check for collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over = -1
                game_over_fx.play()

            # check for collision with lava
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()

            # check for collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

                # check for collision with platforms
            for platform in platform_group:
                # collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # check if above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # move sideways with the platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            for blok in invis_group:
                # collision in the x direction
                if blok.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # collision in the y direction
                if blok.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if below platform
                    if abs((self.rect.top + dy) - blok.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = blok.rect.bottom - self.rect.top
                    # check if above platform
                    elif abs((self.rect.bottom + dy) - blok.rect.top) < col_thresh:
                        self.rect.bottom = blok.rect.top - 1
                        self.in_air = False
                        dy = 0
            # update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
            draw_text(f'YOUR SCORE {score}', font, blue, (screen_width // 2) - 200, screen_height // 2 + 50)
            if self.rect.y > 200:
                self.rect.y -= 5

        # draw player onto screen
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, skin[-1]):
            img_right = pygame.image.load(f'img/player/{skin[0]}/{skin[0]} ({num}).png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True


class World:
    def __init__(self, data):
        self.tile_list = []

        # load images
        dirt_img = pygame.image.load(f'img/{setting[count]}/dirt({setting[count]}).png')
        grass_img = pygame.image.load(f'img/{setting[count]}/grass({setting[count]}).png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                elif tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                elif tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                # x move
                elif tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                # y move
                elif tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                elif tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                elif tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                elif tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                elif tile == 9 and count == 0:
                    tree = Tree(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    tree_group.add(tree)
                elif tile == 9 and count == 1:
                    lamp = Lamp(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    lamp_group.add(lamp)
                elif tile == 9 and count == 2:
                    flag = Flag(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    flag_group.add(flag)
                elif tile == 10 and count == 2:
                    palml = PalmL(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    palm_group.add(palml)
                elif tile == 11 and count == 2:
                    palm = Palm(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    palm_group.add(palm)
                elif tile == 12 and count == 2:
                    palmr = PalmR(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    palm_group.add(palmr)
                elif tile == 13:
                    chest = Chest(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    chest_group.add(chest)
                elif tile == 14:
                    button = Buttons(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    button_group.add(button)
                elif tile == 15:
                    invis = InvisibaleBlocks(col_count * tile_size + (tile_size // 2),
                                             row_count * tile_size + (tile_size // 2))
                    invis_group.add(invis)
                elif tile == 16:
                    pf = PortalFrom(col_count * tile_size + (tile_size // 2),
                                    row_count * tile_size + (tile_size // 2))
                    portalFrom_group.add(pf)
                elif tile == 17:
                    pt = PortalTo(col_count * tile_size + (tile_size // 2),
                                  row_count * tile_size + (tile_size // 2))
                    portalTo_group.add(pt)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


class Vitrina(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(f'img/player/{skin[0]}/{skin[0]} (1).png')
        self.image = pygame.transform.scale(img, (tile_size * 2, tile_size * 2.5))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(f'img/{setting[count]}/platform({setting[count]}).png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Buttons(pygame.sprite.Sprite):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(f'img/{setting[count]}/button({setting[count]}).png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x - 25
        self.rect.y = y - 25


class InvisibaleBlocks(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(f'img/invisibaleBlock.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.image.set_alpha(0)


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/Chest.png')
        self.image = pygame.transform.scale(img, (tile_size + 30, tile_size))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Lamp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/moon/lamp.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 2.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - 50


class PortalFrom(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/portalfrom.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size + 50))
        self.rect = self.image.get_rect()
        self.rect.x = x - 25
        self.rect.y = y - 75


class PortalTo(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/portalto.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size + 50))
        self.rect = self.image.get_rect()
        self.rect.x = x - 25
        self.rect.y = y - 75


class Tree(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/sun/tree.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 2.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - 50


class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images_right = []
        self.index = 0
        self.counter = 0
        for num in range(1, 10):
            img_right = pygame.image.load(f'img/pirate/flag/Flag 0{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 100))
            self.images_right.append(img_right)
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y - 25

    def update(self):
        self.index += 1
        if self.index >= len(self.images_right):
            self.index = 0
        self.image = self.images_right[self.index]


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(f'img/{setting[count]}/door({setting[count]}).png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class PalmL(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/pirate/PalmL.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Palm(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/pirate/Palm.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class PalmR(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/pirate/PalmR.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


name, levels, scores, death, timer, money, skins = tablica()
skin = skins[indexa]
player = Player(100, screen_height - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
lamp_group = pygame.sprite.Group()
flag_group = pygame.sprite.Group()
palm_group = pygame.sprite.Group()
vitrina_group = pygame.sprite.Group()
chest_group = pygame.sprite.Group()
tree_group = pygame.sprite.Group()
button_group = pygame.sprite.Group()
invis_group = pygame.sprite.Group()
portalFrom_group = pygame.sprite.Group()
portalTo_group = pygame.sprite.Group()

# create dummy coin for showing the score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

# load in level data and create world
if path.exists(f'levels/level{level}'):
    f = open(f'levels/level{level}', 'r')
    world_data = []
    for el in f.readlines():
        world_data.append(map(int, el.split(', ')[:len(el.split(', ')) - 1]))

world = World(world_data)
# create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 125, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)
change_button = Button(screen_width - 350, screen_height - 150,
                       pygame.image.load(f'img/{setting[count]}/change_btn({setting[count]}).png'))
home_button = Button(screen_width - 50, 0, home_img)
shop_button = Button(screen_width - 200, 0, shop_img)
arrowR_button = Button(screen_width - 50, screen_height // 2, arrowR_img)
arrowL_button = Button(0, screen_height // 2, arrowL_img)
run = True
while run:

    clock.tick(fps)

    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    if main_menu:
        draw_text(f'YOU HAVE {money} COINS', font_score, blue, screen_width // 2 - 140, 0)
        draw_text('YOUR RECORD:', font_record, blue, 0, screen_height - 320)
        draw_text(name, font_record, blue, 0, screen_height - 290)
        draw_text(levels, font_record, blue, 0, screen_height - 230)
        draw_text(scores, font_record, blue, 0, screen_height - 170)
        draw_text(death, font_record, blue, 0, screen_height - 110)
        draw_text(timer, font_record, blue, 0, screen_height - 50)
        if exit_button.draw():
            run = False
        if start_button.draw():
            start_time = time.time()
            main_menu = False
        if change_button.draw():
            change_setting()
        if shop_button.draw():
            vt = Vitrina(screen_width // 2 - 140, screen_height // 2)
            vitrina_group.add(vt)
            shop = True
            main_menu = False
    elif shop:
        vitrina_group.draw(screen)
        if arrowR_button.draw():
            indexa += 1
            if indexa >= len(skins):
                indexa = 0
            skin = skins[indexa]
            player.reset(100, screen_height - 130)
            vitrina_group.sprites()[0].image = pygame.image.load(f'img/player/{skin[0]}/{skin[0]} (1).png')
        if arrowL_button.draw():
            indexa -= 1
            if indexa < 0:
                indexa = len(skins) - 1
            skin = skins[indexa]
            player.reset(100, screen_height - 130)
            vitrina_group.sprites()[0].image = pygame.image.load(f'img/player/{skin[0]}/{skin[0]} (1).png')
        if home_button.draw():
            money += score
            level = 0
            score = 0
            shop = False
            main_menu = True
    else:
        world.draw()
        if home_button.draw():
            money += score
            level = 0
            score = 0
            world_data = []
            world = reset_level(level)
            if save:
                name = askstring('Name', 'What is your name?')
                print(name, score, death_count, (time.time() - start_time) // 1)
                result_save(name, level, score, death_count, (time.time() - start_time) // 1, money)
            main_menu = True
        if game_over == 0:
            blob_group.update()
            flag_group.update()
            platform_group.update()
            # update score
            # check if a coin has been collected
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            if pygame.sprite.spritecollide(player, chest_group, True):
                score += 10
                coin_fx.play()
            if pygame.sprite.spritecollide(player, portalFrom_group, False) and time.time() - pred_teleport_time >= 5:
                player.reset(portalTo_group.sprites()[0].rect.x, portalTo_group.sprites()[0].rect.y)
                pred_teleport_time = time.time()
            if pygame.sprite.spritecollide(player, portalTo_group, False) and time.time() - pred_teleport_time >= 5:
                player.reset(portalFrom_group.sprites()[0].rect.x, portalFrom_group.sprites()[0].rect.y)
                pred_teleport_time = time.time()

            if pygame.sprite.spritecollide(player, button_group, False):
                for el in button_group:
                    el.image = pygame.transform.scale(
                        pygame.image.load(f'img/{setting[count]}/button({setting[count]})_pressed.png'),
                        (tile_size, tile_size))
                    el.rect = el.image.get_rect()
                    el.rect.x = el.x - 25
                    el.rect.y = el.y - 13
                for el in invis_group:
                    el.image.set_alpha(100)
            draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)

        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)
        lamp_group.draw(screen)
        flag_group.draw(screen)
        palm_group.draw(screen)
        chest_group.draw(screen)
        tree_group.draw(screen)
        button_group.draw(screen)
        invis_group.draw(screen)
        portalFrom_group.draw(screen)
        portalTo_group.draw(screen)

        game_over = player.update(game_over)

        # if player has died
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                death_count += 1
                world = reset_level(level)
                game_over = 0
                score = score_onlvlstart

        # if player has completed the level
        if game_over == 1:
            # reset game and go to next level
            level += 1
            money += score
            score_onlvlstart = score
            if level <= max_levels:
                # reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font, blue, (screen_width // 2) - 140, screen_height // 2)
                draw_text(F'YOUR SCORE {score}', font, blue, (screen_width // 2) - 140, screen_height // 2 + 50)
                if save:
                    name = askstring('Name', 'What is your name?')
                    print(name, score, death_count, (time.time() - start_time) // 1)
                    result_save(name, level, score, death_count, (time.time() - start_time) // 1, money)
                    save = 0
                if restart_button.draw():
                    level = 1
                    save = 1
                    # reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            money += score
            if save:
                name = askstring('Name', 'What is your name?')
                try:
                    result_save(name, level, score, death_count, (time.time() - start_time) // 1, money)
                except NameError:
                    result_save(name, level, score, death_count, 0, money)
            run = False

    pygame.display.update()

pygame.quit()
