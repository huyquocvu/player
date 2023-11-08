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
 
# from playsound import playsound
# import pygame
 
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
last_state = (GPIO.input(clk) << 1) | GPIO.input(dt)

clkLastState = GPIO.input(clk)
dtLastState = GPIO.input(dt)
swLastState = GPIO.input(sw)
current_row = 0
step = 1

last_debounce_time = 0
debounce_time = 5
state_table = [
    [0, -1, 1, 0],
    [1, 0, 0, -1],
    [-1, 0, 0, 1],
    [0, 1, -1, 0]
]

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
 
def play_track(current_row):
    global playing
 
    filename = os.path.abspath(filelist[current_row])
    # sound = pygame.mixer.Sound(filename)
    # pygame.mixer.Sound(filename).play()
    # sound.play()
    playing = False
 
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

    print("INITIALIZING....")
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
    def get_encoder_state():
        return (GPIO.input(clk) << 1) | GPIO.input(dt)

    def rotary_interrupt(channel):
        global counter
        global lastCounter
        global step
        global current_row
        global event
        global playing
        global clkLastState
        global dtLastState
        global last_state
        global last_debounce_time

        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)

        current_time = time.time() * 1000 # current time in milliseconds
        current_state = get_encoder_state()
        
        move = state_table[last_state][current_state]
        
        if move != 0:
            lastCounter = counter
            counter += move
            current_row = counter % len(filelist)

        # Update last states
        last_state = current_state
        clkLastState = clkState
        dtLastState = dtState

    def clkClicked(channel):
            global counter
            global lastCounter
            global step
            global current_row
            global event
            global playing
 
            clkState = GPIO.input(clk)
            dtState = GPIO.input(dt)
   
            if clkState == 0 and dtState == 1 and not playing:
                    lastCounter = counter
                    counter = counter - step
                    current_row = counter % len(filelist)
                   
   
    def dtClicked(channel):
            global counter
            global lastCounter
            global step
            global current_row
            global event
            global playing
 
            clkState = GPIO.input(clk)
            dtState = GPIO.input(dt)
           
            if clkState == 1 and dtState == 0 and not playing:
                    lastCounter = counter
                    counter = counter + step
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
