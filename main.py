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
        self.position = np.array([width/2 - 10, 3*height/4 - 60, width/2 + 10, 3*height/4 - 40])
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
        on_ground = self.overlap(self.position, ground.position)
        
        if on_ground:
            self.state = 'ground'
            self.vertical_speed = 0
        
        else:
            if self.state == 'fly':
                self.vertical_speed += 2.5
            else: self.state = 'fly'
    
    def overlap(self, ch_position, gr_position):
        return ch_position[3] >= gr_position[1] and gr_position[0] < (ch_position[0]+ch_position[2])/2 < gr_position[2]
    
class Base:
    def __init__(self, width, height):
        self.state = 0
        self.position = np.array([0, height-20, width, height])
        self.outline = "#FFFFFF"

class Block:
    def __init__(self, width, height):
        self.state = random.choice(['moving', 'fixed'])
        self.v = 3.5
        self.length = random.randrange(60, 90)
        start_position=random.randrange(0, width-self.length)
        self.position = np.array([start_position, height+20, start_position+self.length, height])

    def moving(self, width):
        if self.state == 'moving':
            if self.position[2] >= width:
                self.v = -3.5
            elif self.position[0] <= 0:
                self.v = 3.5
            self.position[0] += self.v
            self.position[2] += self.v


# 잔상이 남지 않는 코드 & 대각선 이동 가능
my_circle = Character(joystick.width, joystick.height)
my_base = Base(joystick.width, joystick.height)
blocks = [Block(joystick.width, 150)]
my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))

while True:
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

    blocks[0].moving(joystick.width)
    my_circle.ground_check(my_base)
    my_circle.move(command)
    my_circle.re_positioning(my_base)

    #그리는 순서가 중요합니다. 배경을 먼저 깔고 위에 그림을 그리고 싶었는데 그림을 그려놓고 배경으로 덮는 결과로 될 수 있습니다.
    my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
    my_draw.rectangle(tuple(my_base.position), fill = (0, 255, 0, 100))
    my_draw.rectangle(tuple(blocks[0].position), fill = (0, 255, 0, 100))
    my_draw.ellipse(tuple(my_circle.position), outline = my_circle.outline, fill = (0, 0, 0, 100))
    #좌표는 동그라미의 왼쪽 위, 오른쪽 아래 점 (x1, y1, x2, y2)
    joystick.disp.image(my_image)

