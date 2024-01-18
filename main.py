import subprocess
import time
from time import sleep
import os
import sys
from RPi import GPIO
from natsort import natsorted

import curses
import textwrap

# tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM)

# set up the pins we have been using
clk = 27
dt = 17
sw = 22

# set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# get the initial states
counter = 0

swLastState = GPIO.input(sw)
current_row = 0
step = 1

last_debounce_time = 0
debounce_time = 5

# State definitions
STATE_00 = 0b00
STATE_01 = 0b01
STATE_11 = 0b11
STATE_10 = 0b10

# State transition matrix
state_transition_matrix = {
    STATE_00: {STATE_01: 1, STATE_10: -1},
    STATE_01: {STATE_00: -1, STATE_11: 1},
    STATE_11: {STATE_01: -1, STATE_10: 1},
    STATE_10: {STATE_00: 1, STATE_11: -1},
}

# Variables to keep track of the position and state
position = 0
last_state = STATE_00
last_valid_state = STATE_00
current_state = 0

# Initialize the encoder state
last_state = (GPIO.input(clk) << 1) | GPIO.input(dt)
last_valid_state = last_state


# Track states
lastCounter = 0
playing = False
event = 0
progress = 0
last_state = None

# define filelist
files = os.listdir("/home/dewdrop/player/audio")
cwd = os.getcwd()

filelist = menu = natsorted([file for file in files])

def playback(current_row):
    global playing
    global filelist
    if playing:
        os.chdir("/home/dewdrop/player/audio")

        filepath = os.path.abspath(filelist[current_row])
        out = open(os.devnull, "w")
        subprocess.run(
            ["ffplay", "-nodisp", filepath, "-autoexit"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        playing = False


def print_menu(stdscr, selected_row_idx):
    description_table = natsorted(os.listdir("/home/dewdrop/player/descriptions"))

    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Title
    titleBar = curses.newwin(4, w - 1, 0, 0)
    title = "DEW DROP MEMORIES"
    titleBar.addstr(1, 2, title)
    titleBar.addstr(2, 2, "SELECT A TRACK TO HEAR MORE ABOUT OUR HISTORY")
    titleBar.border(0)

    # Track List
    trackWindow = curses.newwin(h - 4, w // 3, 4, 0)
    trackWindow.addstr(1, 2, "Tracklist")
    trackWindow.border(0)

    # Description Window
    descriptionWindow = curses.newwin(h - 4, (w * 2 // 3) - 1, 4, (w // 3))
    descriptionWindow.addstr(1, 2, "Description")
    descriptionWindow.box()

    x = 3
    for idx, row in enumerate(menu):
        # y = h // 2 - len(menu) // 2 + idx
        y = 3 + idx
        name = str(row).split(".")[0]
        if idx == selected_row_idx:
            trackWindow.attron(curses.color_pair(2))
            trackWindow.addstr(y, x - 2, " >  " + name)
            trackWindow.attroff(curses.color_pair(2))

            os.chdir("/home/dewdrop/player/descriptions")
            with open(os.path.abspath(description_table[idx])) as f:
                # for j, text in enumerate(textwrap.wrap(f.read(), w * 2 // 3 - 5)):
                #    descriptionWindow.addstr(j + 3, 2, text)
                text = f.readlines()
                for j, line in enumerate(text):
                    descriptionWindow.addstr(j + 3, 2, textwrap.fill(line, w * 2 // 3 - 5))
        else:
            trackWindow.addstr(y, x, name)

    stdscr.refresh()
    titleBar.refresh()
    trackWindow.refresh()
    descriptionWindow.refresh()


def print_center(stdscr, text):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    x = w // 2 - len(text) // 2
    y = h // 2
    stdscr.addstr(y, x, text)
    stdscr.refresh()


def print_description(stdscr, text):
    return


def main(stdscr):
    global current_row
    global event
    global lastCounter
    global playing
    global counter

    stdscr.clear()
    stdscr.refresh()

    # turn off cursor blinking
    curses.curs_set(0)

    # color scheme for selected row
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    stdscr.nodelay(True)

    # define functions which will be triggered on pin state changes
    def rotary_interrupt(channel):
        global counter
        global lastCounter
        global current_row
        global playing
        global last_state
        global last_valid_state
        global last_debounce_time

        if playing:
            return
        # Read the current state
        state = (GPIO.input(clk) << 1) | GPIO.input(dt)

        # Debounce by ensuring that the state is stable
        time.sleep(0.002)

        stable_state = (GPIO.input(clk) << 1) | GPIO.input(dt)
        if state != stable_state:
            return

        # Check the transition is valid (one bit has changed)
        if stable_state in state_transition_matrix[last_valid_state]:
            direction = state_transition_matrix[last_valid_state][stable_state]
            # Check if we returned to the initial state
            if stable_state == STATE_00:
                lastCounter = counter
                counter += direction
            # Update the last valid state
            last_valid_state = stable_state

        # Always update the last state to the stable state
        last_state = stable_state
        current_row = counter % len(filelist)

    def swClicked(channel):
        global event
        global playing
        global lastCounter
        global counter

        # Check playback status
        if not playing:
            playing = True
            lastCounter = counter

    GPIO.add_event_detect(clk, GPIO.BOTH, callback=rotary_interrupt)
    GPIO.add_event_detect(dt, GPIO.BOTH, callback=rotary_interrupt)
    GPIO.add_event_detect(sw, GPIO.FALLING, callback=swClicked, bouncetime=100)

    # trigger a playback to clear message
    print_center(stdscr, "INITIALIZING...\n")
    sleep(0.5)
    print_menu(stdscr, current_row)
    playing = False
    while True:
        if playing:
            trackName = menu[current_row]
            print_center(stdscr, f"Playing: {trackName.split('.')[0]}")
            playback(current_row)
            print_menu(stdscr, current_row)
        while not playing:
            if lastCounter != counter:
                lastCounter = counter
                print_menu(stdscr, current_row)
            k = stdscr.getch()
            if k == curses.KEY_UP:
                lastCounter = counter
                counter = counter - step
                current_row = counter % len(filelist)
            elif k == curses.KEY_DOWN:
                lastCounter = counter
                counter = counter + step
                current_row = counter % len(filelist)
            elif k == 10:
                # Check playback status
                if not playing:
                    lastCounter = counter
                    playing = True


if __name__ == "__main__":
    curses.wrapper(main)
    GPIO.cleanup()
