import subprocess
import time
from time import sleep
import os
import sys
from RPi import GPIO
 
import asyncio
import threading
 
from pydub import AudioSegment
from pydub.playback import play
 
import curses

#tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM)
 
#set up the pins we have been using
clk = 27
dt = 17
sw = 22
 
#set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#get the initial states
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
    STATE_10: {STATE_00: 1, STATE_11: -1}
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
files = os.listdir("./audio")
os.chdir("./audio")
cwd = os.getcwd()
print(cwd)
filelist = menu = sorted([file for file in files])
print(menu)
 
def load_audio_file(file):
    filename = os.path.abspath(file)
    sound = None
 
    try:
        if filename.endswith('.mp3') or filename.endswith('.MP3'):
            sound = AudioSegment.from_mp3(filename)
        elif filename.endswith('.wav') or filename.endswith('.WAV'):
            sound = AudioSegment.from_wav(filename)
        elif filename.endswith('.ogg') or filename.endswith('.OGG'):
            sound = AudioSegment.from_ogg(filename)
        elif filename.endswith('.flac'):
            sound = AudioSegment.from_file(filename, "flac")
        elif filename.endswith('.3gp'):
            sound = AudioSegment.from_file(filename, "3gp")
        elif filename.endswith('.3g'):
            sound = AudioSegment.from_file(filename, "3g")
    except:
           print("Could not load file")
           return None
    return sound
 
 
def load_to_track(files):
    # Preloads audio files for playback
    # Stores in dictionary for faster retrieval
    playback = map(load_audio_file, files)
    tracks = list(playback)
    return tracks
 
def playback(tracks, current_row):
    global playing
    global filelist
 
    # os.system('clear')
    def _play():
        sys.stdout = open(os.devnull, "w")
        play(tracks[current_row])
 
    def ffplay():
        global playing
        filepath = os.path.abspath(filelist[current_row])
        out = open(os.devnull, 'w')
        subprocess.run(["ffplay", "-nodisp", filepath, "-autoexit"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        playing = False
    ffplay()
    event = 0
 
def print_menu(stdscr, selected_row_idx):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    # stdscr.attron(curses.color_pair(1))
    title = "WELCOME TO THE DEW DROP INN"
    stdscr.addstr(0,0,title)
    stdscr.addstr(1,0, "SELECT A FILE TO HEAR MORE ABOUT OUR HISTORY")
    # stdscr.attroff(curses.color_pair(1))
    for idx, row in enumerate(menu):
        x = w // 2 - 10
        y = h // 2 - len(menu) // 2 + idx
        name = str(row)
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, name)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, name)
    stdscr.refresh()
 
 
def print_center(stdscr, text):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    x = w // 2 - len(text) // 2
    y = h // 2
    stdscr.addstr(y, x, text)
    stdscr.refresh()
 
 
def main(stdscr):
    global current_row
    global event
    global lastCounter
    global playing
    global counter

    # print("INITIALIZING....")
    # tracks = load_to_track(filelist)
    tracks = []

    # turn off cursor blinking
    curses.curs_set(0)
 
    # color scheme for selected row
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    stdscr.nodelay(True)
    # print the menu
    # print_menu(stdscr, current_row)
 
    #define functions which will be triggered on pin state changes
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
                event = 1
 
    GPIO.add_event_detect(clk, GPIO.BOTH, callback=rotary_interrupt)
    GPIO.add_event_detect(dt, GPIO.BOTH, callback=rotary_interrupt)
    GPIO.add_event_detect(sw, GPIO.RISING, callback=swClicked, bouncetime=2000)
 
    event = 0
    # trigger a playback to clear message
    print_center(stdscr, "INITIALIZING...\n")
    sleep(0.5)
    # playback(tracks, current_row)
    print_menu(stdscr, current_row)
    while True:
        if playing:
            # print_center(stdscr, "Paying'{}, {}'".format(menu[current_row], ["."*p for p in progress]))
            # print_center(stdscr, "Playing: {}".format(menu[current_row]))
 
            print_center(stdscr, "Playing: {}".format(menu[current_row]))
            f = playback(tracks, current_row)
            # play_track(current_row)
            event = 0
            print_menu(stdscr, current_row)
            # playing = False
        while not playing:
            if lastCounter != counter and not event:
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
                    playing = True
                    lastCounter = counter
                    event = 1
               
                 
if __name__ == "__main__":
    curses.wrapper(main)
    GPIO.cleanup()
