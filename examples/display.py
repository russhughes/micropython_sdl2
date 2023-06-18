"""
display.py: Display is a subclass of framebuf.FrameBuffer. It can be used to
create a display object to emulate a graphical display on the screen with
minimal changes to the code. It also support polling for SDL events,
like mouse clicks and key presses.
"""
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

import framebuf
import sdl2

# pylint: disable=too-many-arguments
class Display(framebuf.FrameBuffer):
    """A framebuf based display driver for SDL2"""

    def __init__(
        self,
        width=320,
        height=240,
        x=sdl2.SDL_WINDOWPOS_CENTERED,
        y=sdl2.SDL_WINDOWPOS_CENTERED,
        x_scale=1,
        y_scale=1,
        title="MicroPython",
        window_flags=sdl2.SDL_WINDOW_SHOWN,
        render_flags=sdl2.SDL_RENDERER_ACCELERATED,
    ):
        self.buffer = bytearray(width * height * 2)

        self.width = width
        self.height = height
        self.display = sdl2.SDL2(
            width,
            height,
            x=x,
            y=y,
            x_scale=x_scale,
            y_scale=y_scale,
            title=title,
            window_flags=window_flags,
            render_flags=render_flags,
        )

        super().__init__(self.buffer, width, height, framebuf.RGB565)

    def show(self):
        """show the buffer on the display"""
        self.display.show(self.buffer)

    def save(self, file_name):
        """save the buffer to a BMP """
        self.display.save(self.buffer, file_name)

    def poll_event(self):
        """poll for a SDL_Event and return it"""
        return self.display.poll_event()

    def deinit(self):
        """deinitialize the display"""
        self.display.deinit()
