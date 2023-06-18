# Add all C files to SRC_USERMOD.
SRC_USERMOD += $(USERMOD_DIR)/sdl2.c

# We can add our module folder to include paths if needed
# This is not actually needed in this example.
CFLAGS_USERMOD += -I$(USERMOD_DIR) -I/usr/include/SDL2 -D_REENTRANT
CEXAMPLE_MOD_DIR := $(USERMOD_DIR)
LDFLAGS_USERMOD += -lSDL2
