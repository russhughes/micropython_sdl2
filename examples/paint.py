"""
paint.py: A very simple paint program to demonstrate the SDL2 mouse events.
"""
# pylint: disable=import-error
import sdl2
import display

# pylint: disable=undefined-variable
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

# color swatches
COLORS = [BLACK, BLUE, RED, GREEN, CYAN, MAGENTA, YELLOW, WHITE]

WIDTH = 240
HEIGHT = 240


def main():
    """
    Draw on screen using mouse events.
    """

    # configure display
    tft = display.Display(WIDTH, HEIGHT, x_scale=3, y_scale=2, title="Paint")

    color_index = 0
    color = 0
    # draw color swatches used to select color to draw
    for color_index, color in enumerate(COLORS):
        tft.rect(color_index * 30, 210, 30, 30, color, True)

    add_highlight(tft, color_index)

    drawing = False
    p_x = 0
    p_y = 0

    while True:
        # check for an event
        event = tft.poll_event()

        # if no events, continue
        if not event:
            continue

        # if the event is SDL_QUIT, exit
        if event[sdl2.TYPE] == sdl2.SDL_QUIT:
            break

        # if the event is SDL_MOUSEBUTTONDOWN, get the mouse position
        if event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONDOWN:
            p_x = event[sdl2.X]
            p_y = event[sdl2.Y]

            # If point is in the lowest 30 rows of the screen
            # change color to swatch pressed.
            if p_y > 209:
                # remove highlight from around previous color swatch
                remove_highlight(tft, color_index, color)

                # update new color, and add highlight around new color swatch
                color_index = p_x // 30
                color = COLORS[color_index]
                add_highlight(tft, color_index)

            else:
                # otherwise enable drawing
                drawing = True

        # if the event is SDL_MOUSEBUTTONUP, stop drawing
        elif event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONUP:
            drawing = False

        # if the event is SDL_MOUSEMOTION, and we are drawing, draw the pixel
        elif event[sdl2.TYPE] == sdl2.SDL_MOUSEMOTION:
            if drawing:
                # draw the pixel - would be better with lines
                p_x = event[sdl2.X]
                p_y = event[sdl2.Y]
                tft.pixel(p_x, p_y, color)

        # update the display
        tft.show()

    tft.deinit()


def remove_highlight(tft_display, color_index, color):
    """remove highlight around previously selected color swatch"""
    tft_display.rect(color_index * 30, 210, 30, 30, color)
    tft_display.rect(color_index * 30 + 1, 211, 28, 28, color)
    tft_display.rect(color_index * 30 + 2, 212, 26, 26, color)


def add_highlight(tft_display, color_index):
    """draw highlight around newly selected color swatch"""
    tft_display.rect(color_index * 30, 210, 30, 30, WHITE)
    tft_display.rect(color_index * 30 + 1, 211, 28, 28, BLACK)
    tft_display.rect(color_index * 30 + 2, 212, 26, 26, BLACK)


main()
