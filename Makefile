ARCHS = arm64
TARGET = iphone:clang:latest:15.0
include $(THEOS)/makefiles/common.mk
TOOL_NAME = taildaemon-probe
taildaemon-probe_FILES = main.c
taildaemon-probe_CFLAGS = -Wall -Wextra
taildaemon-probe_INSTALL_PATH = /usr/bin
include $(THEOS_MAKE_PATH)/tool.mk
