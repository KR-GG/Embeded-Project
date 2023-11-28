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

my_image = Image.new("RGB", (joystick.width, joystick.height))

my_draw = ImageDraw.Draw(my_image)

class Character:
    def __init__(self, width, height):
        self.appearance = 'circle'
        self.state = None
        self.vertical_speed = 0
        self.position = np.array([width/2 - 10, height-40, width/2 + 10, height-20])
        self.outline = "#FFFFFF"

    def move(self, command = None):
        if command['jump'] and self.vertical_speed == 0:
            self.vertical_speed = -10 * np.sqrt(3)

        self.position[1] += self.vertical_speed
        self.position[3] += self.vertical_speed

        if command['left_pressed']:
            self.position[0] -= 5
            self.position[2] -= 5
        
        if command['right_pressed']:
            self.position[0] += 5
            self.position[2] += 5

    def re_positioning(self, ground):
        if (self.position[3] > ground.position[1]): 
            self.position[1] = ground.position[1] - 20
            self.position[3] = ground.position[1]

    def ground_check(self, ground):
        on_ground = self.on_ground(ground)
        
        if on_ground:
            self.state = 'ground'
            self.vertical_speed = 0
        
        else:
            if self.state == 'fly':
                self.vertical_speed += 2.5
            else: self.state = 'fly'
    
    def next_block_check(self, next_block):
        on_next = self.on_ground(next_block)

        if on_next:
            self.re_positioning(next_block)
            self.state = 'ground'
            self.vertical_speed = 0
            return 1
        
    def falling_check(self, ground):
        falling = self.position[1] >= ground.position[3]

        if falling:
            return 1

    def on_ground(self, ground):
        return ground.position[1] <= self.position[3] <= ground.position[1]+10 and ground.position[0] < (self.position[0]+self.position[2])/2 < ground.position[2]
    
    def move_up(self, t_up):
        if t_up:
            self.position[1] += 10
            self.position[3] += 10

    def move_down(self, t_down):
        if t_down:
            self.position[1] -= 14
            self.position[3] -= 14

class Base:
    def __init__(self, width, height):
        self.state = 0
        self.position = np.array([0, height-20, width, height])
        self.outline = "#FFFFFF"

class Block:
    def __init__(self, width, height):
        self.state = random.choice(['moving', 'fixed'])
        self.v = 3.5
        self.length = random.randrange(80, 100)
        start_position=random.randrange(0, width-self.length)
        self.position = np.array([start_position, height-20, start_position+self.length, height])

    def moving(self, width):
        if self.state == 'moving':
            if self.position[2] >= width:
                self.v = -3.5
            elif self.position[0] <= 0:
                self.v = 3.5
            self.position[0] += self.v
            self.position[2] += self.v

    def move_up(self, t_up):
        if t_up:
            self.position[1] += 10
            self.position[3] += 10

    def move_down(self, t_down):
        if t_down:
            self.position[1] -= 14
            self.position[3] -= 14


# 잔상이 남지 않는 코드 & 대각선 이동 가능
my_circle = Character(joystick.width, joystick.height)
my_base = Base(joystick.width, joystick.height)
blocks = [] # height: 380 / 310 / 240 / 170 / 100 / 30
my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
stair = 0
current_index = 2
next_index = 3
t_up = 0
t_down = 0
fall_stack = 0

while True:
    spawn_h = 380 - 70 * len(blocks)
    while spawn_h >= 30:
        blocks.append(Block(joystick.width, spawn_h))
        spawn_h -= 70

    command = {'move': False, 'jump': False, 'up_pressed': False , 'down_pressed': False, 'left_pressed': False, 'right_pressed': False}
    
    if not joystick.button_A.value: # A pressed
        command['jump'] = True

    if not joystick.button_U.value:  # up pressed
        command['up_pressed'] = True
        command['move'] = True

    if not joystick.button_D.value:  # down pressed
        command['down_pressed'] = True
        command['move'] = True

    if not joystick.button_L.value:  # left pressed
        command['left_pressed'] = True
        command['move'] = True

    if not joystick.button_R.value:  # right pressed
        command['right_pressed'] = True
        command['move'] = True

    for block in blocks:
        block.moving(joystick.width)

    up = my_circle.next_block_check(blocks[next_index])
    if up == 1:
        if fall_stack:
            current_index += 1
            next_index += 1
            fall_stack -= 1
        else:
            blocks = blocks[1:]
            blocks.append(Block(joystick.width, blocks[-1].position[3]-70))
        stair += 1
        if stair == 1: t_up += 5
        else: t_up += 7
    
    my_circle.move_up(t_up)
    for block in blocks:
        block.move_up(t_up)
    t_up -= 1 if t_up else 0

    fall = my_circle.falling_check(blocks[current_index])
    if fall:
        fall_stack += 1
        stair -= 1
        current_index -= 1
        next_index -= 1
        t_down += 7
    if fall_stack == 2:
        print("Game Over")
        my_circle = Character(joystick.width, joystick.height)
        my_base = Base(joystick.width, joystick.height)
        blocks = [] # height: 380 / 310 / 240 / 170 / 100 / 30
        my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
        stair = 0
        current_index = 2
        next_index = 3
        t_up = 0
        t_down = 0
        fall_stack = 0
        continue
    my_circle.move_down(t_down)
    for block in blocks:
        block.move_down(t_down)
    t_down -= 1 if t_down else 0

    if stair == 0:
        my_circle.ground_check(my_base)
        my_circle.move(command)
        if my_circle.state == 'ground': my_circle.re_positioning(my_base)
    else:
        my_circle.ground_check(blocks[current_index])
        my_circle.move(command)
        if my_circle.state == 'ground': my_circle.re_positioning(blocks[current_index])

    #그리는 순서가 중요합니다. 배경을 먼저 깔고 위에 그림을 그리고 싶었는데 그림을 그려놓고 배경으로 덮는 결과로 될 수 있습니다.
    my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
    if stair == 0: my_draw.rectangle(tuple(my_base.position), fill = (0, 255, 0, 100))
    for block in blocks:
        my_draw.rectangle(tuple(block.position), fill = (0, 255, 0, 100))
    my_draw.ellipse(tuple(my_circle.position), outline = my_circle.outline, fill = (0, 0, 0, 100))
    #좌표는 동그라미의 왼쪽 위, 오른쪽 아래 점 (x1, y1, x2, y2)
    joystick.disp.image(my_image)

