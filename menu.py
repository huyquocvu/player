import curses

def main(screen):
    h, w = screen.getmaxyx()
    win1 = curses.newwin(3, 10, 0, 0)
    win2 = curses.newwin(3, 10, 0, w//2)
    for count in ['3', '2', '1', 'GO!']:
        win1.addstr(1, 1, 'Win1: '+ count)
        win2.addstr(1, 1, 'Win2: '+ count)
        win1.border(1)

        screen.refresh()
        win1.refresh()
        win2.refresh()
        screen.getch()

curses.wrapper(main)