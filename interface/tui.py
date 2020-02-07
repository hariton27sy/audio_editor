import curses
import math
import os

from interface import preferences as pf
import interface.windows as ws
import core
from core import project


def get_readme():
    par_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           os.path.pardir)
    with open(os.path.join(par_dir, 'README.md')) as f:
        data = f.readlines()
    return data


class TerminalInterface:
    # Color pairs for windows #
    WINDOW = 1
    ACTIVE_WINDOW = 2
    ACTIVE_LINE = 3
    MENU = 1

    # ----------------------- #

    def __init__(self, *args, **kwargs):
        self.starting = True

        self.project = project.Project()
        self.player = core.player.Player()

        self.main_win = curses.initscr()
        self._init_curses()

        self.height, self.width = self.main_win.getmaxyx()

        self.menuWin = ws.Menu(self)
        self.tracksWin = ws.Tracks(self.height // 2, int(self.width * 0.7),
                                   math.ceil(self.height / 2),
                                   math.ceil(self.width * 0.3),
                                   self)
        self.player_win = ws.Player(
            self.player, self.height // 2,
            0, 8, int(self.width * 0.7), self)
        self.fragments_win = ws.Fragments(1, int(self.width * 0.7),
                                          self.height // 2 - 1,
                                          math.ceil(self.width * 0.3), self)
        self.editor_win = ws.FragmentEditor(1, 0,
                                            self.height // 2 - 1,
                                            int(self.width * 0.7), self)

        self.help_win = ws.HelpWindow(self.height // 4, self.width // 4,
                                      self.height // 2, self.width // 2,
                                      get_readme(), self)

        self.active_win = self.menuWin

        self.loop()

    def _init_curses(self):
        self.main_win = curses.initscr()

        # Check resolution
        if not self.check_resolution():
            self.main_win.getch()
            self.starting = False
            return

        # Check colorful_display
        if not self.check_colorful_term():
            self.main_win.getch()
            self.starting = False
            return

        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.main_win.keypad(True)

        # Color Initializing
        curses.start_color()
        for i in pf.colors:
            curses.init_color(i, *pf.colors[i])
        for i in pf.color_pairs:
            curses.init_pair(i, *pf.color_pairs[i])

        # Load Test data
        # self.project.add_dir("music")

    def check_resolution(self):
        (height, width) = self.main_win.getmaxyx()
        info = (f"Please, set minimum resolution "
                f"{pf.HEIGHT} lines and {pf.WIDTH} rows and "
                "restart app:)\n\nPress any key...")
        if height < pf.HEIGHT or width < pf.WIDTH:
            self.main_win.addstr(0, 0, info)
            self.main_win.refresh()
            return False
        return True

    def check_colorful_term(self):
        info = ("We support only colorful terminals, We are sorry, "
                "but you can't use this program"
                "/nPress any key...")
        if not curses.can_change_color():
            self.main_win.addstr(0, 0, info)
            self.main_win.refresh()
            return False
        return True

    def loop(self):
        self.redraw()

        while self.starting:
            try:
                key = self.main_win.getch()
                self.check_key(key)
            except Warning:
                pass
            except KeyboardInterrupt:
                self.stop()
                print("Exit")
                break
            except Exception as e:
                self.stop()
                raise e
                break

        self.stop()

    def stop(self):
        self.starting = False

        self.player_win.close()
        self.player.stop()

        curses.use_default_colors()
        curses.endwin()

    def check_key(self, key):
        changed = False
        if key == self.tracksWin.win_key:
            self.active_win = self.tracksWin
            changed = True
        if key == self.menuWin.win_key:
            self.active_win = self.menuWin
            changed = True
        if key == self.player_win.win_key:
            self.active_win = self.player_win
            changed = True
        if key == self.fragments_win.win_key:
            self.active_win = self.fragments_win
            changed = True
        if key == self.editor_win.win_key:
            self.active_win = self.editor_win
            changed = True
        if key == self.help_win.win_key:
            self.active_win = self.help_win
        # self.redraw_main_win()
        # self.main_win.addstr(0, 0, str(type(key)))
        # self.main_win.refresh()

        if changed:
            self.redraw()

        self.active_win.check_key(key)

    def redraw(self):
        self.redraw_main_win()
        self.main_win.refresh()
        self.menuWin.redraw()
        self.tracksWin.redraw()
        self.player_win.redraw()
        self.fragments_win.redraw()
        self.editor_win.redraw()
        if self.active_win == self.help_win:
            self.help_win.redraw()

    def redraw_main_win(self):
        for y in range(self.height):
            for x in range(self.width):
                try:
                    self.main_win.addch(y, x, ' ')
                except Exception:
                    pass
        self.main_win.refresh()
