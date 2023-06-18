"""
feathers.py: A demo of the SDL2 display driver for MicroPython
"""
# pylint: disable=import-error
import random
import math
import time
import sdl2
import display

WIDTH = 240
HEIGHT = 320


def between(left, right, along):
    """returns a point along the curve from left to right"""
    dist = (1 - math.cos(along * math.pi)) / 2
    return left * (1 - dist) + right * dist


def color565(red, green, blue):
    """Return RGB565 color value.
    Args:
        r (int): Red value.
        g (int): Green value.
        b (int): Blue value.
    """
    return (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3


def color_wheel(position):
    """returns a 565 color from the given position of the color wheel"""
    position = (255 - position) % 255

    if position < 85:
        return color565(255 - position * 3, 0, position * 3)

    if position < 170:
        position -= 85
        return color565(0, position * 3, 255 - position * 3)

    position -= 170
    return color565(position * 3, 255 - position * 3, 0)


def main():
    """main program"""
    # create a display instance
    tft = display.Display(WIDTH, HEIGHT, x_scale=3, y_scale=2, title="Feathers")

    scroll = 0  # scroll position
    wheel = 0  # color wheel position

    tft.fill(0)  # clear screen

    half = (HEIGHT >> 1) - 1  # half the HEIGHT of the display
    interval = 0  # steps between new points
    increment = 0  # increment per step
    counter = 1  # step counter, overflow to start
    current_y = 0  # current_y value (right point)
    last_y = 0  # last_y value (left point)

    # segment offsets
    x_offsets = [x * (WIDTH // 8) - 1 for x in range(2, 9)]

    while True:

        # when the counter exceeds the interval, save current_y to last_y,
        # choose a new random value for current_y between 0 and 1/2 the
        # HEIGHT of the display, choose a new random interval then reset
        # the counter to 0

        if counter > interval:
            last_y = current_y
            current_y = random.randint(0, half)
            counter = 0
            interval = random.randint(10, 100)
            increment = 1 / interval

        # clear the first column of the display and scroll it
        tft.vline(WIDTH - 1, 0, HEIGHT, 0)
        tft.scroll(-1, 0)
        # get the next point between last_y and current_y
        tween = int(between(last_y, current_y, counter * increment))

        # draw mirrored pixels across the display at the offsets using the color_wheel effect
        for i, x_offset in enumerate(x_offsets):
            tft.pixel(
                (scroll + x_offset) % WIDTH, half + tween, color_wheel(wheel + (i << 2))
            )
            tft.pixel(
                (scroll + x_offset) % WIDTH, half - tween, color_wheel(wheel + (i << 2))
            )

        # increment scroll, counter, and wheel
        scroll = (scroll + 1) % WIDTH
        wheel = (wheel + 1) % 256
        counter += 1

        # pause to slow down scrolling
        tft.show()
        time.sleep(0.005)

        # poll for SDL2 events
        event = tft.poll_event()
        if event and event[0] == sdl2.SDL_QUIT:
            break

    tft.deinit()


main()
