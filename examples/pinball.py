"""
pinball.py - Minimal pinball game in MicroPython based on code from Ten Minute Physics Tutorial
"How to write a pinball simulation."

Tutorial Links:
https://matthias-research.github.io/pages/tenMinutePhysics/
https://youtu.be/NhVUCsXp-Uo

Gameplay Video:
https://youtu.be/y0B3i_UmEU8

Requires:
    tft_config.py for display configuration. See examples/configs
    tft_buttons.py for button configuration. See examples/configs
    OR modify the code for your own display and buttons.

This file incorporates work covered by the following copyright and permission notice.
Modifications and additions Copyright (c) 2022 Russ Hughes and released under the same
terms as the original code.


Copyright 2021 Matthias Müller - Ten Minute Physics

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# pylint: disable=missing-function-docstring, missing-class-docstring, invalid-name

from array import array
import time
import random
import math

import sdl2
import display


# ------------ set constants  ------------

#  Adjust these constants to match your display

WIDTH = 160
HEIGHT = 320
X_SCALE = 2
Y_SCALE = 2

FNT_WIDTH = 8
FNT_HEIGHT = 8

#
#   Adjust these constants to change the game play
#

FLIPPER_SPEED = const(12)  # flipper speed
GRAVITY = -0.8  # gravity (negative y direction)

# If the ball passes thru your flippers you may need to chage
# the FPS value. You can uncomment the print statement in the
# start_game() method to see how many frames per second your
# device is running.

FPS = 60  # frames per second

BALL_SLOW = const(2)  # launch speed for slow ball
BALL_FAST = const(3)  # launch speed for fast ball

BACKGROUND = display.BLUE  # My favorite color
MULTIBALL_SCORE = const(30)  # points to start multiball
PRESSED = 0  # value when button is pressed

# ------------ end constants ------------


def color565(r, g, b):
    """convert 8-bit red, green and blue values to a 16-bit 565 encoding"""
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def color_wheel(WheelPos):
    """returns a 565 color from the given position of the color wheel"""
    WheelPos = (255 - WheelPos) % 255

    if WheelPos < 85:
        return color565(255 - WheelPos * 3, 0, WheelPos * 3)

    if WheelPos < 170:
        WheelPos -= 85
        return color565(0, WheelPos * 3, 255 - WheelPos * 3)

    WheelPos -= 170
    return color565(WheelPos * 3, 255 - WheelPos * 3, 0)


def text_color():
    """return the next color from the color wheel"""
    color = 0
    while True:
        yield color_wheel(color)
        color = (color + 1) % 255


def scale_x(pos):
    """scale position to screen x coordinate"""
    return int(pos.x * SCALE_X)


def scale_y(pos):
    """scale position to screen y coordinate"""
    return int(HEIGHT - pos.y * SCALE_Y)


def pos_to_tuple(pos):
    """convert pos to screen (x,y) coordinate tuple"""
    return (scale_x(pos), scale_y(pos))


# vector math ---------------------------------------


class Vector2:
    def __init__(self, x=0.0, y=0.0, c=display.WHITE):
        """create a new vector"""
        self.x = x
        self.y = y
        self.color = c

    def __str__(self):
        """return a string representation of this vector"""
        return f"({self.x}, {self.y})"

    def set(self, v):
        """set this vector to the values of another vector"""
        self.x = v.x
        self.y = v.y
        self.color = v.color

    def clone(self):
        """return a copy of this vector"""
        return Vector2(self.x, self.y, self.color)

    def add(self, v, s=1.0):
        """add a vector scaled by s to this vector"""
        self.x += v.x * s
        self.y += v.y * s
        return self

    def add_vectors(self, a, b):
        """add two vectors"""
        self.x = a.x + b.x
        self.y = a.y + b.y
        return self

    def subtract(self, v, s=1.0):
        """subtract a vector scaled by s from this vector"""
        self.x -= v.x * s
        self.y -= v.y * s
        return self

    def subtract_vectors(self, a, b):
        """subtract two vectors"""
        self.x = a.x - b.x
        self.y = a.y - b.y
        return self

    def length(self):
        """return the length of this vector"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def scale(self, s):
        """scale this vector by s"""
        self.x *= s
        self.y *= s
        return self

    def dot(self, v):
        """return the dot product of this vector and another vector"""
        return self.x * v.x + self.y * v.y

    def perp(self):
        """return a perpendicular vector"""
        return Vector2(-self.y, self.x, self.color)


# ----------------------------------------------


def closest_point_on_segment(p, a, b):
    """return the closest point on the segment ab to point p"""
    ab = Vector2()
    ab.subtract_vectors(b, a)
    t = ab.dot(ab)
    if t == 0.0:
        return a.clone()
    t = max(0.0, min(1.0, (p.dot(ab) - a.dot(ab)) / t))
    closest = a.clone()
    return closest.add(ab, t)


# object classes ---------------------------------------


class Ball:
    """Class to track a ball"""

    def __init__(self, radius, mass, pos, vel, restitution):
        """create a new ball"""
        self.radius = radius
        self.mass = mass
        self.restitution = restitution
        self.pos = pos.clone()
        self.last = pos.clone()
        self.vel = vel.clone()
        self.size = int(radius * SCALE_RADIUS)
        self.wheel = 0

    def simulate(self, dt, gravity):
        """update the ball position in dt seconds"""
        self.last.set(self.pos)
        self.vel.add(gravity, dt)
        self.pos.add(self.vel, dt)


class Obstacle:
    """Class to contain an obstacle"""

    def __init__(self, radius, pos, pushVel):
        """create a new obstacle"""
        self.radius = radius
        self.size = int(radius * SCALE_RADIUS)
        self.pos = pos.clone()
        self.pushVel = pushVel


class Flipper:
    """Class to contain a flipper"""

    def __init__(self, radius, pos, length, restAngle, maxRotation, angularVelocity):
        """create a new flipper"""

        # fixed
        self.radius = radius
        self.size = int(radius * SCALE_RADIUS)
        self.pos = pos.clone()
        self.length = length
        self.restAngle = restAngle
        self.maxRotation = abs(maxRotation)
        self.sign = math.copysign(1, maxRotation)
        self.angularVelocity = angularVelocity

        # variable
        self.rotation = 0.0
        self.prevRotation = 0.0
        self.currentAngularVelocity = 0.0
        self.pressed = False

    def simulate(self, dt):
        """update the flipper position in dt seconds"""
        self.prevRotation = self.rotation
        if self.pressed:
            self.rotation = min(
                self.rotation + dt * self.angularVelocity, self.maxRotation
            )
        else:
            self.rotation = max(self.rotation - dt * self.angularVelocity, 0.0)
        self.currentAngularVelocity = (
            self.sign * (self.rotation - self.prevRotation) / dt
        )

    def select(self, pos):
        """return True if pos is within the flipper"""
        d = Vector2()
        d.subtract_vectors(self.pos, pos)
        return d.length() < self.length

    def getTip(self, rotation=None):
        """return the tip position of the flipper"""
        if rotation is None:
            rotation = self.rotation
        angle = self.restAngle + self.sign * rotation
        direction = Vector2(math.cos(angle), math.sin(angle))
        tip = self.pos.clone()
        return tip.add(direction, self.length)

    def rot_pos_in_dir(self, pos, direction):
        """rotate pos in direction"""
        pos.add(direction, self.length)
        result = self.pos.clone()
        result.add(Vector2(0.0, self.radius))
        return result

    def direction_from_rot(self, rotation):
        """return the direction of the flipper at rotation"""
        if rotation is None:
            rotation = self.rotation
        angle = self.restAngle + self.sign * rotation
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        return Vector2(cos_angle, sin_angle)

    def draw(self, rotation=None, color=display.WHITE):
        """draw the flipper"""
        if rotation is None:
            rotation = self.rotation
        angle = self.restAngle + self.sign * rotation
        direction = Vector2(math.cos(angle), math.sin(angle))
        tip = self.pos.clone()
        tip.add(direction, self.length)

        direction = self.direction_from_rot(rotation)
        tip = self.pos.clone()
        tip_top = self.rot_pos_in_dir(tip, direction)
        tip_top.add(direction, self.length)

        tip_bot = self.pos.clone()
        tip_bot.add(Vector2(0.0, -self.radius))
        base_top = self.rot_pos_in_dir(tip_bot, direction)
        base_top.add(direction, 0)

        base_bot = self.pos.clone()
        base_bot.add(Vector2(0.0, -self.radius))
        base_bot.add(direction, 0)

        tft.ellipse(
            scale_x(self.pos), scale_y(self.pos), self.size, self.size, color, True
        )

        tft.line(
            scale_x(base_top),
            scale_y(base_top),
            scale_x(tip_top),
            scale_y(tip_top),
            color,
        )

        tft.line(
            scale_x(self.pos), scale_y(self.pos), scale_x(tip), scale_y(tip), color
        )

        tft.line(
            scale_x(base_bot),
            scale_y(base_bot),
            scale_x(tip_bot),
            scale_y(tip_bot),
            color,
        )

        tft.ellipse(scale_x(tip), scale_y(tip), self.size, self.size, color, True)


class Table:
    """Class to contain the table"""

    def __init__(self):
        """create a new table"""
        self.gravity = Vector2(0.0, GRAVITY)
        self.dt = 1.0 / FPS
        self.ticks = int(self.dt * 1000)
        self.game_over = False
        self.score = 0
        self.multiball = 0
        self.ball = 3
        self.gutter = 0
        self.balls = []

        self.border = [Vector2(0.74, 0.25), Vector2(0.995, 0.4), Vector2(0.995, 1.4)]

        # draw arc from left wall to right wall using line segments
        arcRadius = 0.5
        arcCenter = Vector2(0.5, 1.375)
        arcStartAngle = 0
        arcEndAngle = math.pi
        arcSegments = 11
        arcAngleStep = (arcEndAngle - arcStartAngle) / arcSegments
        for i in range(arcSegments + 1):
            angle = arcStartAngle + i * arcAngleStep
            x = arcCenter.x + arcRadius * math.cos(angle)
            y = arcCenter.y + arcRadius * math.sin(angle)
            self.border.append(Vector2(x, y))

        self.border.append(Vector2(0, 0.4))
        self.border.append(Vector2(0.26, 0.25))
        self.gutter = len(self.border)
        self.border.append(Vector2(0.26, 0.0))  # gutter floor
        self.border.append(Vector2(0.74, 0.0))  # gutter floor

        # convert border to scaled polygon
        wall = list(map(pos_to_tuple, self.border))
        self.wall = array("h", [item for sublist in wall for item in sublist])

        # obstacles
        self.obstacles = [
            Obstacle(0.04, Vector2(0.10, 1.68), 0.8),
            Obstacle(0.08, Vector2(0.5, 1.45, display.RED), 1.5),
            Obstacle(0.08, Vector2(0.74, 1.2, display.RED), 1.5),
            Obstacle(0.08, Vector2(0.26, 1.2, display.RED), 1.5),
            Obstacle(0.08, Vector2(0.5, 0.95, display.RED), 1.5),
            Obstacle(0.04, Vector2(0.13, 0.8, display.YELLOW), 1.3),
            Obstacle(0.04, Vector2(0.87, 0.8, display.YELLOW), 1.3),
            Obstacle(0.04, Vector2(0.15, 0.6, display.GREEN), 1.2),
            Obstacle(0.04, Vector2(0.85, 0.6, display.GREEN), 1.2),
        ]

        # flippers
        radius = 0.035
        length = 0.185
        maxRotation = 1.0
        restAngle = 0.5
        angularVelocity = FLIPPER_SPEED

        left_pos = Vector2(0.26, 0.22)
        right_pos = Vector2(0.74, 0.22)

        self.flippers = [
            Flipper(radius, left_pos, length, -restAngle, maxRotation, angularVelocity),
            Flipper(
                radius,
                right_pos,
                length,
                math.pi + restAngle,
                -maxRotation,
                angularVelocity,
            ),
        ]

    def reset(self):
        """reset the table"""
        self.game_over = False
        self.ball = 3
        self.score = 0

        print_right("M  ", 0.25)

        update_score()
        update_ball()

    def add_ball(self):
        """add a ball to the table"""
        radius = 0.03
        mass = math.pi * radius * radius
        pos = Vector2(0.95, 0.5, display.WHITE)
        vel = Vector2(0, random.uniform(BALL_SLOW, BALL_FAST))
        self.balls.append(Ball(radius, mass, pos, vel, 0.2))

    def ball_reset(self):
        """reset the ball"""
        table.multiball = 0
        self.draw_border()
        self.draw_obstacles()
        self.draw_flippers()

        update_ball()
        update_score()
        ball_countdown()
        self.add_ball()

    def draw_border(self):
        """draw the walls of the table"""
        tft.poly(0, 0, self.wall, display.WHITE)

    def draw_balls(self):
        """draw the balls on the table"""
        for ball in self.balls:
            x = scale_x(ball.pos)
            y = scale_y(ball.pos)

            tft.ellipse(
                scale_x(ball.last),
                scale_y(ball.last),
                ball.size,
                ball.size,
                BACKGROUND,
                True,
            )

            tft.ellipse(x, y, ball.size, ball.size, ball.pos.color, True)

    def draw_obstacles(self):
        """draw the obstacles on the table"""
        for obstacle in self.obstacles:
            tft.ellipse(
                scale_x(obstacle.pos),
                scale_y(obstacle.pos),
                obstacle.size,
                obstacle.size,
                obstacle.pos.color,
                True,
            )

    def draw_flippers(self):
        """draw the flippers on the table"""
        for flipper in self.flippers:
            if flipper.currentAngularVelocity != 0:
                flipper.draw(flipper.prevRotation, BACKGROUND)
            flipper.draw()

    def simulate(self):
        """simulate the table"""
        for flipper in self.flippers:
            flipper.simulate(self.dt)

        for i, ball in enumerate(self.balls):
            ball.simulate(self.dt, self.gravity)

            for j in range(i + 1, len(self.balls)):
                ball2 = self.balls[j]
                handle_ball_ball_collision(ball, ball2)

            for obstacle in self.obstacles:
                handle_ball_obstacle_collision(ball, obstacle)

            for flipper in self.flippers:
                handle_ball_flipper_collision(ball, flipper)

            if handle_ball_border_collision(ball, self.border) == self.gutter:
                tft.ellipse(
                    scale_x(ball.last),
                    scale_y(ball.last),
                    ball.size,
                    ball.size,
                    BACKGROUND,
                    True,
                )

                balls = len(self.balls)
                if balls == 1:
                    self.ball -= 1
                    update_ball()

                if self.ball > 0:
                    self.balls.remove(ball)
                    if balls == 1:
                        self.ball_reset()
                else:
                    self.game_over = True


# ------------ collision handling ------------


def handle_ball_ball_collision(ball1, ball2):
    """handle a collision between two balls"""
    restitution = min(ball1.restitution, ball2.restitution)
    direction = Vector2()
    direction.subtract_vectors(ball2.pos, ball1.pos)
    d = direction.length()
    if d == 0.0 or d >= ball1.radius + ball2.radius:
        return

    tft.ellipse(
        scale_x(ball1.pos), scale_y(ball1.pos), ball1.size, ball1.size, BACKGROUND, True
    )
    tft.ellipse(
        scale_x(ball2.pos), scale_y(ball2.pos), ball2.size, ball1.size, BACKGROUND, True
    )

    direction.scale(1.0 / d)

    corr = (ball1.radius + ball2.radius - d) / 2.0
    ball1.pos.add(direction, -corr)
    ball2.pos.add(direction, corr)

    v1 = ball1.vel.dot(direction)
    v2 = ball2.vel.dot(direction)

    m1 = ball1.mass
    m2 = ball2.mass

    newV1 = (m1 * v1 + m2 * v2 - m2 * (v1 - v2) * restitution) / (m1 + m2)
    newV2 = (m1 * v1 + m2 * v2 - m1 * (v2 - v1) * restitution) / (m1 + m2)

    ball1.vel.add(direction, newV1 - v1)
    ball2.vel.add(direction, newV2 - v2)


# ------------------------


def handle_ball_obstacle_collision(ball, obstacle):
    """handle a collision between a ball and an obstacle"""
    direction = Vector2()
    direction.subtract_vectors(ball.pos, obstacle.pos)
    d = direction.length()
    if d == 0.0 or d >= ball.radius + obstacle.radius:
        return

    direction.scale(1.0 / d)

    corr = ball.radius + obstacle.radius - d
    ball.pos.add(direction, corr)

    v = ball.vel.dot(direction)
    ball.vel.add(direction, obstacle.pushVel - v)

    table.score += 1

    ball_count = len(table.balls)
    if ball_count == 1:
        table.multiball += 1
        if table.multiball == MULTIBALL_SCORE:
            table.multiball = 0
            table.add_ball()


# ------------------------


def handle_ball_flipper_collision(ball, flipper):
    """handle a collision between a ball and a flipper"""
    closest = closest_point_on_segment(ball.pos, flipper.pos, flipper.getTip())
    direction = Vector2()
    direction.subtract_vectors(ball.pos, closest)
    d = direction.length()
    if d == 0.0 or d >= ball.radius + flipper.radius:
        return

    direction.scale(1.0 / d)

    corr = ball.radius + flipper.radius - d
    ball.pos.add(direction, corr)

    # update velocitiy
    radius = closest.clone()
    radius.add(direction, flipper.radius)
    radius.subtract(flipper.pos)
    surfaceVel = radius.perp()
    surfaceVel.scale(flipper.currentAngularVelocity)
    v = ball.vel.dot(direction)
    vnew = surfaceVel.dot(direction)
    ball.vel.add(direction, vnew - v)


# ------------------------


def handle_ball_border_collision(ball, border):
    """handle a collision between a ball and a border"""
    # find closest segment
    d = Vector2()
    closest = Vector2()
    ab = Vector2()
    normal = Vector2()
    wall = 0
    minDist = 0.0

    for i, a in enumerate(border):
        b = border[(i + 1) % len(border)]
        c = closest_point_on_segment(ball.pos, a, b)
        d.subtract_vectors(ball.pos, c)
        dist = d.length()
        if i == 0 or dist < minDist:
            wall = i
            minDist = dist
            closest.set(c)
            ab.subtract_vectors(b, a)
            normal = ab.perp()

    # push out
    d.subtract_vectors(ball.pos, closest)
    dist = d.length()
    if dist == 0.0:
        d.set(normal)
        dist = normal.length()

    d.scale(1.0 / dist)

    if d.dot(normal) >= 0.0:
        if dist > ball.radius:
            return 0
        ball.pos.add(d, ball.radius - dist)

    else:
        ball.pos.add(d, -(dist + ball.radius))

    # update velocity
    v = ball.vel.dot(d)
    vnew = abs(v) * ball.restitution

    ball.vel.add(d, vnew - v)
    return wall


# ------------ Text routines ------------


def center_on(text, y, color=display.WHITE):
    """center text on y"""
    width = FNT_WIDTH * len(text)
    x = (WIDTH >> 1) - (width >> 1)
    y_s = int(HEIGHT - y * SCALE_Y) - FNT_HEIGHT // 2
    tft.rect(x, y_s, width, FNT_HEIGHT, BACKGROUND, True)
    tft.text(text, x, y_s, color)


def print_at(text, x, y, color=display.WHITE):
    """print text at x,y"""
    width = FNT_WIDTH * len(text)
    x_s = int(x * SCALE_X)
    y_s = int(HEIGHT - y * SCALE_Y) - FNT_HEIGHT // 2
    tft.rect(x_s, y_s, width, FNT_HEIGHT, BACKGROUND, True)
    tft.text(text, x_s, y_s, color)


def print_right(text, y, color=display.WHITE):
    """print text right aligned at y"""
    width = FNT_WIDTH * len(text)
    x_s = WIDTH - (FNT_WIDTH * len(text))
    y_s = int(HEIGHT - y * SCALE_Y) - FNT_HEIGHT // 2

    tft.rect(x_s, y_s, width, FNT_HEIGHT, BACKGROUND, True)
    tft.text(text, x_s, y_s, color)


def update_score():
    """update the score"""
    print_right(f"{MULTIBALL_SCORE-table.multiball:2}", 0.25)
    print_right(f"{table.score:04}", 0.08)


def update_ball():
    """update the ball count"""
    print_at(f"B {table.ball}", 0.0, 0.08)


def ball_countdown():
    """countdown before the ball is released"""
    for i in range(3, 0, -1):
        center_on(f"{i}", 1.2, display.WHITE)
        tft.show()
        time.sleep(1)

    center_on(" ", 1.2, display.WHITE)
    table.draw_border()
    table.draw_obstacles()


def print_game_over(color=display.RED):
    """print game over"""
    center_on("GAME", 1.25, color)
    center_on("OVER", 1.15, color)
    tft.show()


def game_over():
    """game over, man, game over"""
    print_game_over()
    time.sleep(1)

    color = text_color()

    for _ in range(300):
        print_game_over(next(color))
        time.sleep(0.01)

    tft.fill(BACKGROUND)


# ------------ the big show ------------


def start_game():
    """start the game and loop"""
    try:

        event = None
        while True:
            table.reset()
            table.ball_reset()

            while table.game_over is False:
                last = time.ticks_ms()

                # check the event queue for mouse button events or quit.
                while event := tft.poll_event():
                    if event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONDOWN:
                        if event[sdl2.BUTTON] == sdl2.SDL_BUTTON_LEFT:
                            table.flippers[0].pressed = True

                        if event[sdl2.BUTTON] == sdl2.SDL_BUTTON_RIGHT:
                            table.flippers[1].pressed = True

                    elif event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONUP:
                        if event[sdl2.BUTTON] == sdl2.SDL_BUTTON_LEFT:
                            table.flippers[0].pressed = False

                        if event[sdl2.BUTTON] == sdl2.SDL_BUTTON_RIGHT:
                            table.flippers[1].pressed = False

                    elif event[sdl2.TYPE] == sdl2.SDL_QUIT:
                        return

                table.simulate()

                table.draw_border()
                table.draw_obstacles()

                table.draw_flippers()
                table.draw_balls()
                update_score()

                tft.show()
                # print("FPS: ", 1000 / (time.ticks_ms() - last))
                if time.ticks_ms() - last < table.ticks:
                    time.sleep_ms(table.ticks - (time.ticks_ms() - last))

            game_over()

    finally:
        if hasattr(tft, "deinit") and callable(tft.deinit):
            tft.deinit()


# ------------ set up the display ------------

tft = display.Display(WIDTH, HEIGHT, x_scale=X_SCALE, y_scale=Y_SCALE, title="Pinball")
tft.fill(BACKGROUND)

MAX_HEIGHT = 1.88

SCALE_X = WIDTH
SCALE_Y = HEIGHT / MAX_HEIGHT
SCALE_RADIUS = min(SCALE_X, SCALE_Y)


# ------- set up the table and start game ---------

table = Table()
start_game()
