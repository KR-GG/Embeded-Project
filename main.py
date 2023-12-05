import time
import random
from colorsys import hsv_to_rgb
import board
from digitalio import DigitalInOut, Direction
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
import numpy as np

class Joystick:
    def __init__(self):
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.BAUDRATE = 24000000

        self.spi = board.SPI()
        self.disp = st7789.ST7789(
                    self.spi,
                    height=240,
                    y_offset=80,
                    rotation=180,
                    cs=self.cs_pin,
                    dc=self.dc_pin,
                    rst=self.reset_pin,
                    baudrate=self.BAUDRATE,
                    )

        # Input pins:
        self.button_A = DigitalInOut(board.D5)
        self.button_A.direction = Direction.INPUT

        self.button_B = DigitalInOut(board.D6)
        self.button_B.direction = Direction.INPUT

        self.button_L = DigitalInOut(board.D27)
        self.button_L.direction = Direction.INPUT

        self.button_R = DigitalInOut(board.D23)
        self.button_R.direction = Direction.INPUT

        self.button_U = DigitalInOut(board.D17)
        self.button_U.direction = Direction.INPUT

        self.button_D = DigitalInOut(board.D22)
        self.button_D.direction = Direction.INPUT

        self.button_C = DigitalInOut(board.D4)
        self.button_C.direction = Direction.INPUT

        # Turn on the Backlight
        self.backlight = DigitalInOut(board.D26)
        self.backlight.switch_to_output()
        self.backlight.value = True

        # Create blank image for drawing.
        # Make sure to create image with mode 'RGB' for color.
        self.width = self.disp.width
        self.height = self.disp.height

joystick = Joystick()

font = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/HedvigLettersSans-Regular.ttf", 15)
font_small = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/HedvigLettersSans-Regular.ttf", 12)
font_title_60 = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/BlakaInk-Regular.ttf", 60)
font_title_45 = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/BlakaInk-Regular.ttf", 45)
font_title_40 = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/BlakaInk-Regular.ttf", 40)
font_title_25 = ImageFont.truetype("/home/kau-esw/Desktop/Embeded-Project/font/BlakaInk-Regular.ttf", 25)

bg_image = Image.new("RGB", (joystick.width, joystick.height))
my_character = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/pink_ch.png')
my_character_opp = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/pink_ch_opp.png')
base_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/ground_240_20.png')
block_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/ground_120_20.png')
icy_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/ground_120_20_icy.png')
enemy_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/enemy_img.png')
enemy_opp_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/enemy_opp_img.png')
cloud_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/cloud_img.png')
fire_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/fire.png')
fire_opp_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/fire_opp.png')
heart_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/heart.png')
rule_image = Image.open('/home/kau-esw/Desktop/Embeded-Project/res/rule.png')

bg_draw = ImageDraw.Draw(bg_image)

class Character:
    def __init__(self):
        self.state = 'ground'
        self.vertical_speed = 0
        self.horizontal_speed = 0
        self.position = np.array([110, 200])

    def move(self, ground, command = None):
        if command['jump'] and self.vertical_speed == 0:
            self.vertical_speed = -16
            self.horizontal_speed = 0

        self.position[1] += self.vertical_speed

        if ground.icy == 'true':
            if self.horizontal_speed:
                self.horizontal_speed += 1 if self.horizontal_speed<0 else -1
            if ground.state == 'moving' and self.state == 'ground':
                    self.horizontal_speed += ground.v
            if command['left_pressed']:
                self.horizontal_speed -= 7
            if command['right_pressed']:
                self.horizontal_speed += 7
            self.position[0] += self.horizontal_speed
            if command['left_pressed']:
                self.horizontal_speed += 5
            if command['right_pressed']:
                self.horizontal_speed -= 5
            if ground.state == 'moving' and self.state == 'ground':
                self.horizontal_speed -= ground.v
        
        else:
            self.horizontal_speed = 0
            if ground.state == 'moving' and self.state == 'ground':
                self.horizontal_speed += ground.v
            if command['left_pressed']:
                self.horizontal_speed -= 5
            if command['right_pressed']:
                self.horizontal_speed += 5
            self.position[0] += self.horizontal_speed
        
    def re_positioning(self, ground):
        if (self.position[1]+20 > ground.position[1]): 
            self.position[1] = ground.position[1] - 20

    def ground_check(self, ground):
        on_ground = self.on_ground(ground)
        
        if on_ground:
            self.state = 'ground'
            self.re_positioning(ground)
            self.vertical_speed = 0
        
        else:
            if self.state == 'fly':
                self.vertical_speed += 2.5
            else: self.state = 'fly'
    
    def next_block_check(self, next_block):
        on_next = self.on_ground(next_block) and self.vertical_speed >= 0

        if on_next:
            self.re_positioning(next_block)
            self.state = 'ground'
            self.vertical_speed = 0
            return 1
        return 0
        
    def falling_check(self, ground):
        falling = self.position[1]+20 >= ground.position[1] + 20

        return falling

    def on_ground(self, ground):
        return ground.position[1] <= self.position[1]+20 <= ground.position[1]+20 and ground.position[0] <= self.position[0]+10 <= ground.position[0] + ground.length
    
    def move_up(self, t_up, bg_start):
        if t_up:
            self.position[1] += 10
            return bg_start + 10
        return bg_start

    def move_down(self, t_down, bg_start):
        if t_down:
            self.position[1] -= 14
            return bg_start -14
        return bg_start

    def enemy_check(self, enemies):
        for index, enemy in enumerate(enemies):
            if enemy:
                if (enemy.position[0]-10 <= self.position[0] <= enemy.position[0]+10 and enemy.position[1]-20 <= self.position[1] <= enemy.position[1]+20) or (enemy.position[0]-20 <= self.position[0] <= enemy.position[0]+20 and enemy.position[1]-10 <= self.position[1] <= enemy.position[1]+10):
                    return index
        return -1
    
    def heart_check(self, hearts):
        for index, heart in enumerate(hearts):
            if heart:
                if (heart.position[0]-20 <= self.position[0] <= heart.position[0] + 15 and heart.position[1] - 20 <= self.position[1] <= heart.position[1] + 15):
                    return index
        return -1
    
class Fire:
    def __init__(self, character):
        if my_ch_img == my_character:
            self.state = 'left'
            self.position = np.array([character.position[0]-15, character.position[1] + 2])
            self.v = -6
        else:
            self.state = 'right'
            self.position = np.array([character.position[0]+20, character.position[1] + 2])
            self.v = 6
    
    def move(self):
        self.position[0] += self.v

    def enemy_check(self, enemies):
        for index, enemy in enumerate(enemies):
            if enemy:
                head = self.position[0] if self.state == 'left' else self.position[0] + 15
                if(enemy.position[0] <= head <= enemy.position[0]+20 and enemy.position[1]-20 < self.position[1] < enemy.position[1]+20):
                    return index
        return -1
    
    def move_up(self, t_up):
        if t_up:
            self.position[1] += 10

    def move_down(self, t_down):
        if t_down:
            self.position[1] -= 14

class Enemy:
    def __init__(self, block):
        self.position = np.array([block.position[0] + random.randint(0, block.length - 10), block.position[1] - 25])
        self.v = 2

    def re_positioning(self, block):
        self.position[1] = block.position[1] -25
        if self.position[0] >= block.position[0] + block.length - 10:
            self.v = -2
        elif self.position[0] <= block.position[0] + 10:
            self.v = 2
        self.position[0] += self.v

class Heart:
    def __init__(self, block):
        self.position = np.array([block.position[0] + random.randint(0, block.length - 10), block.position[1] - 20])
        self.offset = block.position[0] - self.position[0]

    def re_positioning(self, block):
        self.position[1] = block.position[1] -20
        self.position[0] = block.position[0] - self.offset

class Base:
    def __init__(self):
        self.state = 'fixed'
        self.enemy = 'false'
        self.icy = 'false'
        self.v = 0
        self.length = 240
        self.position = np.array([0, 220])

    def moving(self, width):
        pass

    def move_up(self, t_up):
        if t_up:
            self.position[1] += 10

    def move_down(self, t_down):
        if t_down:
            self.position[1] -= 14

class Block:
    def __init__(self, width, height):
        self.state = random.choice(['moving', 'fixed'])
        self.enemy = random.choice(['true', 'true', 'true','false', 'false'])
        self.heart = random.choice(['true', 'false', 'false', 'false', 'false'])
        self.icy = random.choice(['true', 'false'])
        self.v = 3.5
        self.length = random.randint(80, 120)
        start_position=random.randint(0, width-self.length)
        self.position = np.array([start_position, height-20])

    def moving(self, width):
        if self.state == 'moving':
            if self.position[0] + self.length >= width:
                self.v = -3.5
            elif self.position[0] <= 0:
                self.v = 3.5
            self.position[0] += self.v

    def move_up(self, t_up):
        if t_up:
            self.position[1] += 10

    def move_down(self, t_down):
        if t_down:
            self.position[1] -= 14

def create_gauge_bar(cooltime):
    if cooltime == 0: return 0
    image = Image.new("RGB", (25, 4), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0,0,25,4), outline="white")

    fill = int((50-cooltime) / 2)
    draw.rectangle((0,0,fill,4), fill=(255,102,0))
    return image

records = []
record = 0
last_score = 0
start_page = 3
end_page = 0
delay = 0
my_ch = Character()
my_base = Base()
blocks = [] # height: 380 / 310 / 240 / 170 / 100 / 30
enemies = [0, 0, 0, 0, 0, 0]
hearts = [0, 0, 0, 0, 0, 0]
fireball = 0
cooltime = 0
bg_start = 0
health = 3
stair = 0
score = 0
current_index = 2
next_index = 3
t_up = 0
t_down = 0
fall_stack = 0
spawn_h = 380
while spawn_h >= 30:
    blocks.append(Block(joystick.width, spawn_h))
    spawn_h -= 70
blocks[2] = my_base
for index, block in enumerate(blocks):
    if block.state == 'fixed' and block.enemy =='true':
        enemies[index] = Enemy(block)
    if block.state == 'moving' and block.enemy =='false' and block.heart == 'true':
        hearts[index] = Heart(block)

while True:
    delay -= 1 if delay else 0
    cooltime -= 1 if cooltime else 0
    command = {'move': False, 'jump': False, 'attack': False, 'left_pressed': False, 'right_pressed': False}
    
    if not joystick.button_A.value: # A pressed
        command['jump'] = True

    if not joystick.button_L.value:  # left pressed
        command['left_pressed'] = True
        command['move'] = True

    if not joystick.button_R.value:  # right pressed
        command['right_pressed'] = True
        command['move'] = True

    if not joystick.button_B.value and cooltime == 0: # B pressed
        command['attack'] = True
        try:
            fireball = Fire(my_ch)
            cooltime += 50
        except NameError:
            pass

    if (start_page == 0 and end_page == 0):
        for block in blocks:
            block.moving(joystick.width)

        up = my_ch.next_block_check(blocks[next_index])
        if up:
            if fall_stack:
                current_index += 1
                next_index += 1
                fall_stack -= 1
            else:
                score += 10
                blocks = blocks[1:]
                blocks.append(Block(joystick.width, blocks[-1].position[1]-50))
                enemies = enemies[1:]
                if blocks[-1].enemy == 'true' and blocks[-1].state == 'fixed':
                    enemies.append(Enemy(blocks[-1]))
                else:
                    enemies.append(0)
                hearts = hearts[1:]
                if blocks[-1].state == 'moving' and blocks[-1].enemy == 'false' and blocks[-1].heart == 'true':
                    hearts.append(Heart(blocks[-1]))
                else:
                    hearts.append(0)
            t_up += 7 if stair else 5
            stair += 1
        
        bg_start = my_ch.move_up(t_up, bg_start)
        for block in blocks:
            block.move_up(t_up)
        if fireball: fireball.move_up(t_up)
        t_up -= 1 if t_up else 0

        fall = my_ch.falling_check(blocks[current_index])
        if fall:
            if stair == 0: fall_stack = 3
            elif stair == 1:
                fall_stack += 1
                stair = 0
                current_index -= 1
                next_index -= 1
                my_ch.position[1] -= 8
                for block in blocks:
                    block.position[1] -= 8
                t_down += 3
            else:
                fall_stack += 1
                stair -= 1
                current_index -= 1
                next_index -= 1
                t_down += 5

        if fall_stack > 2:
            delay = 10
            record = score
            last_score = record
            start_page = 1
            end_page = 1
            my_ch = Character()
            my_base = Base()
            blocks = [] # height: 380 / 310 / 240 / 170 / 100 / 30
            enemies = [0, 0, 0, 0, 0, 0]
            hearts = [0, 0, 0, 0, 0, 0]
            fireball = 0
            bg_start = 0
            health = 3
            stair = 0
            score = 0
            current_index = 2
            next_index = 3
            t_up = 0
            t_down = 0
            fall_stack = 0
            spawn_h = 380
            while spawn_h >= 30:
                blocks.append(Block(joystick.width, spawn_h))
                spawn_h -= 70
            blocks[2] = my_base
            for index, block in enumerate(blocks):
                if block.state == 'fixed' and block.enemy =='true':
                    enemies[index] = Enemy(block)
                if block.state == 'moving' and block.enemy =='false' and block.heart == 'true':
                    hearts[index] = Heart(block)
            continue

        bg_start = my_ch.move_down(t_down, bg_start)
        for block in blocks:
            block.move_down(t_down)
        if fireball: fireball.move_down(t_down)
        t_down -= 1 if t_down else 0
    
        my_ch.ground_check(blocks[current_index])
        my_ch.move(blocks[current_index], command)

        if fireball:
            fireball.move()
            hit = fireball.enemy_check(enemies)
            if hit != -1:
                score += 10
                enemies[hit] = 0
            head = fireball.position[0] if fireball.state == 'left' else fireball.position[0] + 15
            if -15 > head or joystick.width < head:
                fireball = 0

        for index, enemy in enumerate(enemies):
            if enemy:
                enemy.re_positioning(blocks[index])
        for index, heart in enumerate(hearts):
            if heart:
                heart.re_positioning(blocks[index])

        hit = my_ch.enemy_check(enemies)
        if hit != -1:
            health -= 1
            enemies[hit] = 0

        if health == 0:
            delay = 10
            record = score
            last_score = record
            start_page = 1
            end_page = 1
            my_ch = Character()
            my_base = Base()
            blocks = [] # height: 380 / 310 / 240 / 170 / 100 / 30
            enemies = [0, 0, 0, 0, 0, 0]
            hearts = [0, 0, 0, 0, 0, 0]
            fireball = 0
            bg_start = 0
            health = 3
            stair = 0
            score = 0
            current_index = 2
            next_index = 3
            t_up = 0
            t_down = 0
            fall_stack = 0
            spawn_h = 380
            while spawn_h >= 30:
                blocks.append(Block(joystick.width, spawn_h))
                spawn_h -= 70
            blocks[2] = my_base
            for index, block in enumerate(blocks):
                if block.state == 'fixed' and block.enemy =='true':
                    enemies[index] = Enemy(block)
                if block.state == 'moving' and block.enemy =='false' and block.heart == 'true':
                    hearts[index] = Heart(block)
            continue

        hit = my_ch.heart_check(hearts)
        if hit != -1:
            health += 1
            hearts[hit] = 0

        #그리는 순서가 중요합니다. 배경을 먼저 깔고 위에 그림을 그리고 싶었는데 그림을 그려놓고 배경으로 덮는 결과로 될 수 있습니다.
        bg_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
        temp = bg_start
        while temp > -240:
            bg_image.paste(cloud_image, (0, temp), cloud_image)
            temp -= 240
        for block in blocks:
            if block == my_base: pass
            if block.icy == 'true':
                bg_image.paste(icy_image.resize(tuple(map(int, (block.length, 20)))), tuple(block.position))
            else:
                bg_image.paste(block_image.resize(tuple(map(int,(block.length, 20)))), tuple(block.position))
        if stair == 0: bg_image.paste(base_image, tuple(my_base.position))
        for enemy in enemies:
            if enemy:
                enemy_img = enemy_image if enemy.v > 0 else enemy_opp_image
                bg_image.paste(enemy_img, tuple(enemy.position), enemy_img)
        for heart in hearts:
            if heart:
                bg_image.paste(heart_image, tuple(heart.position), heart_image)
        bg_draw.text((3, 2), f"SCORE {score}", font = font, fill = (0,0,0,100))
        bg_draw.text((3, 18), f"LIFE", font = font, fill = (0,0,0,100))
        temp = health
        while temp > 0:
            heart_position = 18 + temp*20
            bg_image.paste(heart_image, (heart_position, 20), heart_image)
            temp -= 1
        try:
            my_ch_img
        except NameError: 
            my_ch_img = my_character
        if command['left_pressed'] == True: my_ch_img = my_character
        if command['right_pressed'] == True: my_ch_img = my_character_opp
        bg_image.paste(my_ch_img, tuple(my_ch.position), my_ch_img)
        if fireball:
            if fireball.state == 'left':
                bg_image.paste(fire_opp_image, tuple(fireball.position), fire_opp_image)
            else:
                bg_image.paste(fire_image, tuple(fireball.position), fire_image)
        if cooltime:
            bar = create_gauge_bar(cooltime)
            if bar:
                bg_image.paste(bar, (my_ch.position[0]-2, my_ch.position[1]-8))

    if record:
        try:
            records[4]
        except IndexError:
            records.append(record)
        else:
            if record > records[4]:
                records[4] = record
        record = 0
        records.sort(reverse=True)

    if command['right_pressed'] == True and delay == 0:
        if end_page:
            end_page = 0
            delay += 5
        elif start_page:
            start_page -= 1
            delay += 5

    if start_page == 1:
        bg_image.paste(cloud_image, (0, 0), cloud_image)
        bg_image.paste(base_image, tuple(my_base.position))
        bg_draw.text((55, 50), "PONG!", font = font_title_60, fill=(203,153,000))
        bg_draw.text((45, 150), "Press -> to start GAME", font = font, fill=(0,0,0))

    if start_page == 2:
        bg_image.paste(rule_image, (0,0), rule_image)
        bg_draw.text((28,22), "HOW TO PLAY", font = font_title_40, fill = (204,102,0))
        bg_draw.text((33,69), "Jump to the next block!", font = font_small, fill = (0,0,0))
        bg_draw.text((40,82), "jump:#5     attack:#6", font = font_small, fill = (0,0,0))
        bg_draw.text((33,98), "Stay away               Take hearts", font = font_small, fill = (0,0,0))
        bg_draw.text((33,111), "from enemies!      and keep alive", font = font_small, fill = (0,0,0))

    if start_page == 3:
        bg_image.paste(cloud_image, (0, 0), cloud_image)
        bg_image.paste(base_image, tuple(my_base.position))
        bg_draw.text((55, 50), "PONG!", font = font_title_60, fill=(203,153,000))
        bg_draw.text((45, 150), "Press -> to start GAME", font = font, fill=(0,0,0))

    if end_page == 1:
        bg_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (10,10,10, 30))
        bg_draw.text((20,5), "GAME OVER", font = font_title_45, fill=(153,000,51))
        bg_draw.text((20,210), "My SCORE", font = font_title_25, fill=(255,204,000))
        bg_draw.text((140,210), f"{last_score}", font = font_title_25, fill=(255,204,000))
        bg_draw.text((20,60), "1st SCORE", font = font_title_25)
        bg_draw.text((20,90), "2nd SCORE", font = font_title_25)
        bg_draw.text((20,120), "3rd SCORE", font = font_title_25)
        bg_draw.text((20,150), "4th SCORE", font = font_title_25)
        bg_draw.text((20,180), "5th SCORE", font = font_title_25)

        try:
            bg_draw.text((140,60), f"{records[0]}", font = font_title_25)
        except IndexError:
            pass
        try:
            bg_draw.text((140,90), f"{records[1]}", font = font_title_25)
        except IndexError:
            pass
        try:
            bg_draw.text((140,120), f"{records[2]}", font = font_title_25)
        except IndexError:
            pass
        try:
            bg_draw.text((140,150), f"{records[3]}", font = font_title_25)
        except IndexError:
            pass
        try:
            bg_draw.text((140,180), f"{records[4]}", font = font_title_25)
        except IndexError:
            pass

    joystick.disp.image(bg_image)
    print(start_page, end_page)