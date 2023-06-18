// Include MicroPython API.
#include "py/runtime.h"
#include "py/mphal.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include <SDL2/SDL.h>

typedef struct _sdl2_obj_t
{
	mp_obj_base_t base;

	int x;                  // x position of the window in virtual pixels
	int y;                  // y position of the window in virtual pixels
	int width;              // width of the window in virtual pixels
	int height;             // height of the window in virtual pixels
	const char *title;      // title of the window
	int window_flags;       // window flags
    int render_flags;       // render flags
    int x_scale;            // x scale of the window
    int y_scale;            // y scale of the window

	SDL_Window *win;
	SDL_Renderer *renderer;

} sdl2_obj_t;

/// ### SDL2
///
/// ```python
/// sdl2.SDL2(
///     width=320,
///     height=240,
///     x=SDL_WINDOWPOS_CENTERED,
///     y=SDL_WINDOWPOS_CENTERED,
///     title="MicroPython",
///     window_flags=SDL_WINDOW_SHOWN,
///     render_flags=SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
/// ```
///
/// #### Description
/// Creates a window and renderer with the specified position, dimensions,
/// title, flags and returns a SDL2 object.
///
/// #### Parameters
/// - `width` The width of the window. Default: 320
/// - `height` The height of the window. Default: 240
/// - `x` The x position of the window. Default: SDL_WINDOWPOS_CENTERED
///    - SDL_WINDOWPOS_UNDEFINED - used to indicate that you don't care what the x position is
///    - SDL_WINDOWPOS_CENTERED - used to indicate that the window position should be centered
///
/// - `y` The y position of the window. Default: SDL_WINDOWPOS_CENTERED
///    - SDL_WINDOWPOS_UNDEFINED - used to indicate that you don't care what the y position is
///    - SDL_WINDOWPOS_CENTERED - used to indicate that the window position should be centered
///
/// - `x_scale` The x scale of the window. Default: 1
/// - `y_scale` The y scale of the window. Default: 1
/// - `title` The title of the window. Default: "MicroPython"
/// - `window_flags` The window flags. Default: SDL_WINDOW_SHOWN
///    - SDL_WINDOW_SHOWN - the window is visible
///    - SDL_WINDOW_BORDERLESS - no window decoration
///
/// - `render_flags` The render flags. Default: SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
///    - SDL_RENDERER_ACCELERATED - the renderer uses hardware acceleration
///    - SDL_RENDERER_PRESENTVSYNC - present is synchronized with the refresh rate
///
/// #### Returns
/// - A new SDL2 object.
///
/// #### Raises
/// - RuntimeError for any SDL2 errors.

STATIC mp_obj_t sdl2_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args)
{
	enum
	{
		ARG_width,              // The width of the window in virtual pixels
		ARG_height,             // The height of the window in virtual pixels
		ARG_x,                  // The x position of the window in virtual pixels
		ARG_y,                  // The y position of the window in virtual pixels
        ARG_x_scale,            // The x scale of the window
        ARG_y_scale,            // The y scale of the window
		ARG_title,              // The title of the window
		ARG_window_flags,       // The window flags
        ARG_render_flags,       // The render flags
	};

	STATIC const mp_arg_t allowed_args[] = {
		{MP_QSTR_width, MP_ARG_INT, {.u_int = 320}},
		{MP_QSTR_height, MP_ARG_INT, {.u_int = 240}},
		{MP_QSTR_x, MP_ARG_OBJ, {.u_int = SDL_WINDOWPOS_CENTERED}},
		{MP_QSTR_y, MP_ARG_OBJ, {.u_int = SDL_WINDOWPOS_CENTERED}},
        {MP_QSTR_x_scale, MP_ARG_INT, {.u_int = 1}},
        {MP_QSTR_y_scale, MP_ARG_INT, {.u_int = 1}},
		{MP_QSTR_title, MP_ARG_OBJ, {.u_rom_obj = MP_ROM_QSTR(MP_QSTR_MicroPython)}},
		{MP_QSTR_window_flags, MP_ARG_INT, {.u_int = SDL_WINDOW_SHOWN}},
        {MP_QSTR_render_flags, MP_ARG_INT, {.u_int = SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC}},
	};

	mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
	mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

	// Allocates the new object and sets the type.
	sdl2_obj_t *self = mp_obj_malloc(sdl2_obj_t, type);

	// store the argument values in the object
	self->x = args[ARG_x].u_int;
	self->y = args[ARG_y].u_int;
	self->width = args[ARG_width].u_int;
	self->height = args[ARG_height].u_int;
    self->x_scale = args[ARG_x_scale].u_int;
    self->y_scale = args[ARG_y_scale].u_int;
	self->title = mp_obj_str_get_str(args[ARG_title].u_obj);
	self->window_flags = args[ARG_window_flags].u_int;
    self->render_flags = args[ARG_render_flags].u_int;

	if (SDL_Init(SDL_INIT_EVERYTHING) != 0) {
		mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_Init error: %s\n"), SDL_GetError());
	}

	self->win = SDL_CreateWindow(
                    self->title,
                    self->x,
                    self->y,
                    self->width * self->x_scale,
                    self->height * self->y_scale,
                    self->window_flags);

	if (self->win == NULL) {
		mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_CreateWindow error: %s\n"), SDL_GetError());
	}

	self->renderer = SDL_CreateRenderer(self->win, -1, self->render_flags);
	if (self->renderer == NULL) {
		mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_CreateRenderer error: %s\n"), SDL_GetError());
	}

	return MP_OBJ_FROM_PTR(self);
}

/// ### show
///
/// ```python
/// SDL2.show(buffer)
/// ```
/// #### Description
///
/// Show the buffer on the SDL2 window.
///
/// #### Parameters
///
/// - `buffer` bytearray of 16-bit RGB565 values
///
/// #### Raises
///
/// - ValueError if the buffer is the wrong size.
/// - RuntimeError for any SDL2 errors.

STATIC mp_obj_t sdl2_show(size_t n_args, const mp_obj_t *args) {
	sdl2_obj_t *self = MP_OBJ_TO_PTR(args[0]);
	mp_buffer_info_t bufinfo;
	mp_get_buffer(args[1], &bufinfo, MP_BUFFER_READ);

    // Check that there is a buffer.
    if (bufinfo.buf == NULL) {
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("no buffer"));
    }

    // Check the buffer size.
    if (bufinfo.len != (unsigned) self->width * self->height * 2) {
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("buffer size mismatch"));
    }

	uint16_t *buffer = bufinfo.buf;
    SDL_Rect fillRect;

	int i = 0;
	for (int y = 0; y < self->height; y++) {
		for (int x = 0; x < self->width; x++) {
			uint16_t color = buffer[i++];
			unsigned int r = (color >> 11) * 255 / 31;
			unsigned int g = ((color >> 5) & 0x3F) * 255 / 63;
			unsigned int b = (color & 0x1F) * 255 / 31;

            if (SDL_SetRenderDrawColor(self->renderer, r, g, b, 255) != 0) {
                mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_SetRenderDrawColor error: %s\n"), SDL_GetError());
            }

            if (self->x_scale == 1 && self->y_scale == 1) {
                if (SDL_RenderDrawPoint(self->renderer, x, y) != 0) {
                    mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_RenderDrawPoint error: %s\n"), SDL_GetError());
                }
                continue;
            }

            fillRect.x = x * self->x_scale;
            fillRect.y = y * self->y_scale;
            fillRect.w = self->x_scale;
            fillRect.h = self->y_scale;
            if (SDL_RenderFillRect(self->renderer, &fillRect) != 0) {
                mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SDL_RenderFillRect error: %s\n"), SDL_GetError());
            }
		}
	}

	SDL_RenderPresent(self->renderer);
	return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(sdl2_show_obj, 1, 2, sdl2_show);

/// ### event
///
/// ```python
/// SDL2.event()
/// ```
///
/// #### Description
///
/// Checks for events and returns a tuple describing the event if there is one,
/// otherwise returns None.
///
/// #### Returns:
///
/// - None or a tuple describing the event
///
/// #### Event Types:

STATIC mp_obj_t sdl2_poll_event(size_t n_args, const mp_obj_t *args) {
    sdl2_obj_t *self = MP_OBJ_TO_PTR(args[0]);
  	SDL_Event event;
    const char *keyname = "";

	if (SDL_PollEvent(&event)) {

		switch(event.type) {
			case SDL_KEYDOWN:
			case SDL_KEYUP:

                ///   - SDL_KEYDOWN or SDL_KEYUP
                ///
                ///     (event_type, keyname, mod)
                ///
                ///     Index       | Item       | Description
                ///     ------------|------------|------------
                ///     sdl.EVENT   | event_type | SDL_KEYDOWN or SDL_KEYUP
                ///     sdl.KEYNAME | keyname    | name of the key pressed or released if any
                ///     sdl.MOD     | mod        | status of modifier keys (shift, ctrl, alt, etc.)

				keyname = SDL_GetKeyName(event.key.keysym.sym);
				mp_obj_t result[3] = {
					mp_obj_new_int(event.type),
					mp_obj_new_str(keyname, strlen(keyname)),
					mp_obj_new_int(event.key.keysym.mod)
				};
				return mp_obj_new_tuple(3, result);

			case SDL_MOUSEMOTION:

                ///   - SDL_MOUSEMOTION
                ///
                ///     (event_type, x, y, xrel, yrel, state)
                ///
                ///      Index       | Item       | Description
                ///     -------------|------------|------------
                ///      sdl.EVENT   | event_type | SDL_MOUSEMOTION
                ///      sdl.X       | x          | coordinates of the mouse
                ///      sdl.Y       | y          | coordinates of the mouse
                ///      sdl.XREL    | xrel       | relative motion in the X direction
                ///      sdl.YREL    | yrel       | relative motion in the Y direction
                ///      sdl.STATE   | state      | state of the mouse buttons
				{
					mp_obj_t mouse_motion[6] = {
						mp_obj_new_int(event.type),
						mp_obj_new_int(event.motion.x / self->x_scale),
						mp_obj_new_int(event.motion.y / self->y_scale),
						mp_obj_new_int(event.motion.xrel / self->x_scale),
						mp_obj_new_int(event.motion.yrel / self->y_scale),
						mp_obj_new_int(event.motion.state)
					};
					return mp_obj_new_tuple(6, mouse_motion);
				}

			case SDL_MOUSEBUTTONDOWN:
			case SDL_MOUSEBUTTONUP:

                ///   - SDL_MOUSEBUTTONDOWN or SDL_MOUSEBUTTONUP
                ///
                ///     (event_type, x, y, button)
                ///
                ///     | Index       | Item       | Description
                ///     |-------------|------------|------------
                ///     | sdl.EVENT   | event_type | SDL_MOUSEBUTTONDOWN or SDL_MOUSEBUTTONUP
                ///     | sdl.X       | x          | coordinates of the mouse
                ///     | sdl.Y       | y          | coordinates of the mouse
                ///     | sdl.BUTTON  | button     | button pressed or released
				{
					mp_obj_t mouse_button[4] = {
						mp_obj_new_int(event.type),
						mp_obj_new_int(event.button.x / self->x_scale),
						mp_obj_new_int(event.button.y / self->y_scale),
						mp_obj_new_int(event.button.button)
					};
					return mp_obj_new_tuple(4, mouse_button);
				}

			case SDL_MOUSEWHEEL:

                ///   - SDL_MOUSEWHEEL
                ///
                ///     (event_type, x, y, direction, preciseX, preciseY, mouseX, mouseY)
                ///
                ///     | Index         | Item       | Description
                ///     |---------------|------------|------------
                ///     | sdl.EVENT     | event_type | SDL_MOUSEWHEEL
                ///     | sdl.X         | x          | amount scrolled horizontally
                ///     | sdl.Y         | y          | amount scrolled vertically
                ///     | sdl.DIRECTION | direction  | direction of the scroll

				{
					mp_obj_t mouse_wheel[8] = {
						mp_obj_new_int(event.type),
						mp_obj_new_int(event.wheel.x / self->x_scale),
						mp_obj_new_int(event.wheel.y / self->x_scale),
						mp_obj_new_int(event.wheel.direction),
					};
					return mp_obj_new_tuple(8, mouse_wheel);
				}
		}

        ///   - SDL_QUIT
        ///
        ///     | Index         | Item       | Description
        ///     |---------------|------------|------------
        ///     | sdl.EVENT     | event_type | SDL_QUIT
        ///
        ///   - all others return a tuple containing the integer (event_type) id of the event
        ///
        ///     | Index         | Item       | Description
        ///     |---------------|------------|------------
        ///     | sdl.EVENT     | event_type | integer event_type id

		mp_obj_t event_type[1] = {
			mp_obj_new_int(event.type)
		};

		return mp_obj_new_tuple(1, event_type);
	}
	else {
		return mp_const_none;
	}
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(sdl2_poll_event_obj, 1, 1, sdl2_poll_event);

/// ### deinit()
///
/// ```python
/// SDL2.deinit()
/// ```
/// #### Description
///
/// Deinitialize SDL2, removes all SDL2 windows.
///

STATIC mp_obj_t sdl2_deinit(size_t n_args, const mp_obj_t *args) {
    SDL_Quit();
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(sdl2_deinit_obj, 1, 1, sdl2_deinit);

STATIC const mp_rom_map_elem_t sdl2_locals_dict_table[] = {
	{MP_ROM_QSTR(MP_QSTR_show), MP_ROM_PTR(&sdl2_show_obj)},
	{MP_ROM_QSTR(MP_QSTR_poll_event), MP_ROM_PTR(&sdl2_poll_event_obj)},
    {MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&sdl2_deinit_obj)},
};

STATIC MP_DEFINE_CONST_DICT(sdl2_locals_dict, sdl2_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
	sdl2_type_t,
	MP_QSTR_SDL2,
	MP_TYPE_FLAG_NONE,
	make_new, sdl2_make_new,
	locals_dict, &sdl2_locals_dict);

// Define all properties of the module.
STATIC const mp_rom_map_elem_t sdl2_module_globals_table[] = {
	{MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sdl2)},
	{MP_ROM_QSTR(MP_QSTR_SDL2), MP_ROM_PTR(&sdl2_type_t)},

    {MP_ROM_QSTR(MP_QSTR_SDL_WINDOWPOS_UNDEFINED), MP_ROM_INT(SDL_WINDOWPOS_UNDEFINED)},
	{MP_ROM_QSTR(MP_QSTR_SDL_WINDOWPOS_CENTERED), MP_ROM_INT(SDL_WINDOWPOS_CENTERED)},
    {MP_ROM_QSTR(MP_QSTR_SDL_WINDOW_SHOWN), MP_ROM_INT(SDL_WINDOW_SHOWN)},
    {MP_ROM_QSTR(MP_QSTR_SDL_WINDOW_BORDERLESS), MP_ROM_INT(SDL_WINDOW_BORDERLESS)},

    {MP_ROM_QSTR(MP_QSTR_SDL_RENDERER_ACCELERATED), MP_ROM_INT(SDL_RENDERER_ACCELERATED)},
    {MP_ROM_QSTR(MP_QSTR_SDL_RENDERER_PRESENTVSYNC), MP_ROM_INT(SDL_RENDERER_PRESENTVSYNC)},

	// SDL_MOUSEMOTION: (TYPE, X, Y, XREL, YREL, STATE)
    {MP_ROM_QSTR(MP_QSTR_SDL_MOUSEMOTION), MP_ROM_INT(SDL_MOUSEMOTION)},
	{MP_ROM_QSTR(MP_QSTR_X), MP_ROM_INT(1)},
	{MP_ROM_QSTR(MP_QSTR_Y), MP_ROM_INT(2)},
	{MP_ROM_QSTR(MP_QSTR_XREL), MP_ROM_INT(3)},
	{MP_ROM_QSTR(MP_QSTR_YREL), MP_ROM_INT(4)},
	{MP_ROM_QSTR(MP_QSTR_STATE), MP_ROM_INT(5)},

	// SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP: (TYPE, X, Y, BUTTON)
    {MP_ROM_QSTR(MP_QSTR_SDL_MOUSEBUTTONDOWN), MP_ROM_INT(SDL_MOUSEBUTTONDOWN)},
    {MP_ROM_QSTR(MP_QSTR_SDL_MOUSEBUTTONUP), MP_ROM_INT(SDL_MOUSEBUTTONUP)},
	{MP_ROM_QSTR(MP_QSTR_BUTTON), MP_ROM_INT(3)},
	{MP_ROM_QSTR(MP_QSTR_SDL_BUTTON_LEFT), MP_ROM_INT(SDL_BUTTON_LEFT)},
	{MP_ROM_QSTR(MP_QSTR_SDL_BUTTON_MIDDLE), MP_ROM_INT(SDL_BUTTON_MIDDLE)},
	{MP_ROM_QSTR(MP_QSTR_SDL_BUTTON_RIGHT), MP_ROM_INT(SDL_BUTTON_RIGHT)},

	// SDL_MOUSEWHEEL: (TYPE, X, Y, DIRECTION, PRECISEX, PRECISEY, MOUSEX, MOUSEY)
	{MP_ROM_QSTR(MP_QSTR_SDL_MOUSEWHEEL), MP_ROM_INT(SDL_MOUSEWHEEL)},
	{MP_ROM_QSTR(MP_QSTR_SDL_MOUSEWHEEL_NORMAL), MP_ROM_INT(SDL_MOUSEWHEEL_NORMAL)},
	{MP_ROM_QSTR(MP_QSTR_SDL_MOUSEWHEEL_FLIPPED), MP_ROM_INT(SDL_MOUSEWHEEL_FLIPPED)},
	{MP_ROM_QSTR(MP_QSTR_DIRECTION), MP_ROM_INT(3)},
	{MP_ROM_QSTR(MP_QSTR_PRECISEX), MP_ROM_INT(4)},
	{MP_ROM_QSTR(MP_QSTR_PRECISEY), MP_ROM_INT(5)},
	{MP_ROM_QSTR(MP_QSTR_MOUSEX), MP_ROM_INT(6)},
	{MP_ROM_QSTR(MP_QSTR_MOUSEY), MP_ROM_INT(7)},

	// SDL_KEYDOWN, SDL_KEYUP: (TYPE, KEYNAME, MOD)
    {MP_ROM_QSTR(MP_QSTR_SDL_KEYDOWN), MP_ROM_INT(SDL_KEYDOWN)},
    {MP_ROM_QSTR(MP_QSTR_SDL_KEYUP), MP_ROM_INT(SDL_KEYUP)},
	{MP_ROM_QSTR(MP_QSTR_TYPE), MP_ROM_INT(0)},
	{MP_ROM_QSTR(MP_QSTR_KEYNAME), MP_ROM_INT(1)},
	{MP_ROM_QSTR(MP_QSTR_MOD), MP_ROM_INT(2)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_NONE), MP_ROM_INT(KMOD_NONE)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LSHIFT), MP_ROM_INT(KMOD_LSHIFT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RSHIFT), MP_ROM_INT(KMOD_RSHIFT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LCTRL), MP_ROM_INT(KMOD_LCTRL)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RCTRL), MP_ROM_INT(KMOD_RCTRL)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LALT), MP_ROM_INT(KMOD_LALT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RALT), MP_ROM_INT(KMOD_RALT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LGUI), MP_ROM_INT(KMOD_LGUI)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RGUI), MP_ROM_INT(KMOD_RGUI)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_NUM), MP_ROM_INT(KMOD_NUM)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_CAPS), MP_ROM_INT(KMOD_CAPS)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_MODE), MP_ROM_INT(KMOD_MODE)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_CTRL), MP_ROM_INT(KMOD_CTRL)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LCTRL), MP_ROM_INT(KMOD_LCTRL)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RCTRL), MP_ROM_INT(KMOD_RCTRL)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_SHIFT), MP_ROM_INT(KMOD_SHIFT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LSHIFT), MP_ROM_INT(KMOD_LSHIFT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RSHIFT), MP_ROM_INT(KMOD_RSHIFT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_ALT), MP_ROM_INT(KMOD_ALT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_LALT), MP_ROM_INT(KMOD_LALT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_RALT), MP_ROM_INT(KMOD_RALT)},
	{MP_ROM_QSTR(MP_QSTR_KMOD_GUI), MP_ROM_INT(KMOD_GUI)},

	// SDL_QUIT: (TYPE)
	{MP_ROM_QSTR(MP_QSTR_SDL_QUIT), MP_ROM_INT(SDL_QUIT)},
};

STATIC MP_DEFINE_CONST_DICT(sdl2_module_globals, sdl2_module_globals_table);

// Define module object.
const mp_obj_module_t sdl2_user_cmodule = {
	.base = {&mp_type_module},
	.globals = (mp_obj_dict_t *)&sdl2_module_globals,
};

// Register the module to make it available in Python.
MP_REGISTER_MODULE(MP_QSTR_sdl2, sdl2_user_cmodule);
