import curses
import math
import os
import threading
import time
import datetime

from core import player as pl
from core import fragment as fr
import pydub

# Color pairs for windows #
WINDOW = 1
ACTIVE_WINDOW = 2
ACTIVE_LINE = 2
MENU = 1


# ----------------------- #


def del_last_digit(num: float):
    str_num = str(num)
    if str_num[-2:] == '.0' or str_num[-2:] == ',0':
        return int(num)

    if len(str_num) == 1:
        return 0

    if '.' in str_num or ',' in str_num:
        return float(str_num[:-1])

    return int(str_num[:-1])


def format_time(time_: float):
    """time in seconds"""
    time_ = round(time_, 1)
    ms = int((time_ - int(time_)) * 10)
    time_ = int(time_)
    s = time_ % 60
    m = time_ // 60 % 60
    h = time_ // 3600

    return f"{h}:{m:02}:{s:02}.{ms}"


class Window:
    def __init__(self, y, x, height, width, name=None, key=None, parent=None):
        self.win = curses.newwin(height, width, y, x)
        self.win.attron(curses.color_pair(WINDOW))
        self.parent = parent
        self.name = name
        self.width = width
        self.height = height
        self.key = key

    def redraw(self):
        for y in range(self.height):
            for x in range(self.width):
                try:
                    self.win.addch(y, x, ' ')
                except curses.error:
                    pass

    def close(self):
        pass

    def check_key(self, key):
        pass


class Menu(Window):
    def __init__(self, parent):
        super().__init__(0, 0, 1, parent.width, "menu", "F2", parent)
        self.win.attron(curses.color_pair(MENU))
        self.walker = None

        self.win_key = curses.KEY_F2

        self.options = [
            "open",
            "load project",
            "save project",
            "export track"
        ]
        self.current = 0
        self.splitter = " | "

    def redraw(self):
        for x in range(self.win.getmaxyx()[1]):
            try:
                self.win.addch(0, x, ' ')
            except curses.error:
                pass

        x = 1
        for i, elem in enumerate(self.options):
            if i == self.current:
                self.win.attron(curses.color_pair(ACTIVE_LINE))

            self.win.addstr(0, x, elem)
            x += len(elem) + len(self.splitter)

            self.win.attron(curses.color_pair(MENU))
            if i + 1 < len(self.options):
                self.win.addstr(0, x - len(self.splitter), self.splitter)

        self.win.addstr(0, self.win.getmaxyx()[1] - 3 - len(self.key),
                        f"[{self.key}]")

        self.win.refresh()

        if self.walker:
            self.walker.redraw()

    def check_key(self, key):
        if self.walker:
            self.walker.check_key(key)
        elif key == curses.KEY_LEFT:
            self.current = max(0, self.current - 1)
        elif key == curses.KEY_RIGHT:
            self.current = min(len(self.options) - 1, self.current + 1)
        elif key == 10:
            if self.current == 0:
                self.walker = FileWalker(self.parent.height // 4,
                                         self.parent.width // 4,
                                         self.parent.height // 2,
                                         self.parent.width // 2, self.parent)

            if self.current == self.options.index("export track"):
                self.walker = FileSaver(self.parent.height // 4,
                                        self.parent.width // 4,
                                        self.parent.height // 2,
                                        self.parent.width // 2, self.parent)

            if self.current == self.options.index('save project'):
                self.walker = FileSaver(self.parent.height // 4,
                                        self.parent.width // 4,
                                        self.parent.height // 2,
                                        self.parent.width // 2, self.parent,
                                        ['.proj'])

            if self.current == self.options.index('load project'):
                self.walker = FileWalker(self.parent.height // 4,
                                         self.parent.width // 4,
                                         self.parent.height // 2,
                                         self.parent.width // 2, self.parent)

        if self.walker and self.walker.result and self.current == 0:
            if self.walker.result != "<ESC>":
                try:
                    if os.path.isdir(self.walker.result):
                        self.parent.project.add_dir(self.walker.result)
                    else:
                        self.parent.project.add_track(self.walker.result)
                except Exception:
                    pass
            self.walker = None
            self.parent.active_win = self.parent.tracksWin
            self.parent.redraw()

        if (self.walker and self.walker.result and
                self.current == self.options.index('export track') and
                self.walker.end is True):
            if self.walker.result != "<ESC>":
                self.save_file(self.walker.result)

            self.walker = None
            self.parent.active_win = self.parent.tracksWin
            self.parent.redraw()

        if (self.walker and self.walker.result and
                self.current == self.options.index('save project') and
                self.walker.end is True):
            if self.walker.result != "<ESC>":
                self.parent.project.save_project(self.walker.result)

            self.walker = None
            self.parent.active_win = self.parent.tracksWin
            self.parent.redraw()

        if (self.walker and self.walker.result and
                self.current == self.options.index('load project')):
            if self.walker.result != "<ESC>":
                try:
                    if not os.path.isdir(self.walker.result):
                        self.parent.project.load_project(self.walker.result)
                except Exception:
                    pass
            self.walker = None
            self.parent.active_win = self.parent.tracksWin
            self.parent.redraw()

        self.redraw()

    def save_file(self, filename):
        segment = self.parent.project.export()
        ext = os.path.splitext(filename)[-1]
        pydub.AudioSegment.export(segment, filename, ext[1:])


class ScrollableWindow(Window):
    def __init__(self, y, x, height, width, name=None, key=None, parent=None):
        super().__init__(y, x, height, width, name, key, parent)
        self.win.border()

        self.padding = 2

        self.current = 0
        self.top_position = 0

    def scroll(self, delta):
        if (self.current + delta >=
                self.top_position + self.height - 2 * self.padding):
            self.top_position = (self.current + delta -
                                 self.height + self.padding * 2 + 1)
        if self.current + delta < self.top_position:
            self.top_position += delta

        self.current += delta

    def redraw(self):
        super().redraw()
        if self.parent.active_win == self:
            self.win.attron(curses.color_pair(ACTIVE_WINDOW))
        self.win.border()
        line = ""
        if self.name:
            line = self.name
        if self.key:
            line += f" [{self.key}]" if line else f"[{self.key}]"

        x = (self.width - len(line)) // 2
        x = 0 if x < 0 else x
        self.win.addstr(0, x, line)

        self.win.attron(curses.color_pair(WINDOW))

    def draw_list(self, elements, print_pos=True):
        for i in range(self.top_position, self.top_position +
                       self.height - self.padding * 2):
            if i < len(elements):
                line = f"{i + 1}. " if print_pos else ""
                line += elements[i]
                if len(line) > self.width - self.padding * 2:
                    line = line[:self.width - self.padding * 2 - 3] + "..."
                if i == self.current:
                    self.win.attron(curses.color_pair(ACTIVE_LINE))
                self.win.addstr(self.padding + i - self.top_position,
                                self.padding, line)
                self.win.attron(curses.color_pair(WINDOW))
            else:
                break


class Tracks(ScrollableWindow):
    def __init__(self, y, x, height, width, parent):
        super().__init__(y, x, height, width, "Tracks", "SHIFT+T", parent)
        self.win_key = ord("T")

    def redraw(self):
        super().redraw()
        self.draw_list([e.filename for e in self.parent.project.tracks])
        self.win.refresh()

    def check_key(self, key):
        if key == curses.KEY_DOWN and self.current + 1 < len(
                self.parent.project.tracks):
            self.scroll(1)
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == ord(" ") and self.current < len(self.parent.project.tracks):
            self.parent.active_win = self.parent.player_win
            track = self.parent.project.tracks[self.current]
            data = track.get_frames().raw_data
            self.parent.player.play(data)
            self.parent.redraw()
        if key == 10 and self.current < len(
                self.parent.project.tracks):
            fragment = fr.Fragment(self.parent.project.tracks[self.current])
            self.parent.project.add_fragment(fragment)
            self.parent.redraw()

        self.redraw()


class FileWalker(ScrollableWindow):
    def __init__(self, y, x, height, width, parent):
        super().__init__(y, x, height, width, "Open File", parent=parent)
        self.padding = 4

        self._path = os.path.abspath(".")
        self._elems = ['..']
        temp = next(os.walk(self._path))
        self._elems.extend(temp[1])
        self._elems.extend(temp[2])

        self.result = None

        self.redraw()

    def redraw(self):
        super(FileWalker, self).redraw()
        self.win.attron(curses.color_pair(ACTIVE_WINDOW))
        self.win.border()
        self.win.addstr(0, (self.width - len(self.name)) // 2, self.name)
        self.win.addstr(2, 2, "Press 's' for selecting current directory")
        self.win.attron(curses.color_pair(WINDOW))
        self.draw_list(self._elems)
        self.win.refresh()

    def check_key(self, key):
        if key == ord('s'):
            self.result = self._path
        if key == curses.KEY_DOWN and self.current + 1 < len(self._elems):
            self.scroll(1)
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == 10:
            path = os.path.join(self._path, self._elems[self.current])
            if os.path.isdir(path):
                self._path = os.path.abspath(path)
                self._elems = [".."]
                temp = next(os.walk(self._path))
                self._elems.extend(temp[1])
                self._elems.extend(temp[2])
                self.current = 0
                self.top_position = 0
            else:
                self.result = path
                return
        if key == 27:
            self.result = "<ESC>"
        self.redraw()


class Player(ScrollableWindow):
    full_cell = "█"
    semi_cell = "▌"

    def __init__(self, player: pl.Player, y, x, height, width, parent=None):
        super().__init__(y, x, height, width, name="Player",
                         key="SHIFT+P", parent=parent)

        self.player = player
        self.isWorking = True

        self.win_key = ord("P")

        self._thread = threading.Thread(target=self._redraw_timeline)
        self._thread.start()

    def redraw(self):
        super(Player, self).redraw()
        self.win.addstr(self.padding, self.padding, self.get_timeline())
        self.win.addstr(self.padding + 1, self.padding,
                        f"{format_time(self.player.current_time)}/"
                        f"{format_time(self.player.full_time)}")

        self.win.addstr(self.height - self.padding, self.padding,
                        "Space - play/pause, LEFT/RIGHT - back/forward, "
                        "Sh+S - stop")

        self.win.refresh()

    def check_key(self, key):
        if key == curses.KEY_LEFT:
            self.player.translate_pos(-1)
        if key == curses.KEY_RIGHT:
            self.player.translate_pos()
        if key == ord(" "):
            if self.player.is_working:
                self.player.pause()
            else:
                self.player.play1()
        if key == ord("S"):
            self.player.stop()

        self.redraw()

    def get_timeline(self):
        length = self.width - 2 * self.padding
        if self.player.full_time != 0:
            count = (self.player.current_time /
                     self.player.full_time * (length - 2))
        else:
            count = 0

        timeline = "[" + self.full_cell * math.floor(count)
        if count - math.floor(count) > 0.5:
            timeline += self.semi_cell

        timeline = timeline.ljust(length - 1)
        timeline += "]"

        return timeline

    def _redraw_timeline(self):
        while self.isWorking:
            if self.player.is_working:
                self.redraw()

            time.sleep(.1)

    def close(self):
        self.isWorking = False
        self._thread.join()


class Fragments(ScrollableWindow):
    def __init__(self, y, x, height, width, parent):
        super(Fragments, self).__init__(y, x, height, width,
                                        "Fragments", "SHIFT+F", parent)

        self.win_key = ord("F")
        self.padding = 4

        funcs = {
            'Сдвинуть, убрать промежутки': lambda: self.parent.project.stick()
        }
        self.active_win = None
        self.tools = Tools(y + 2, x + 2, height - 4, width - 4, funcs,
                           self)

    def check_key(self, key):
        if self.active_win:
            self.tools.check_key(key)
            self.redraw()
            return

        if key == curses.KEY_DOWN and self.current + 1 < len(
                self.parent.project.fragments):
            self.scroll(1)
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == 10 and self.current < len(self.parent.project.fragments):
            self.parent.active_win = self.parent.editor_win
            self.parent.active_win.fragment = (
                self.parent.project.fragments[self.current])
            self.parent.redraw()
        if key == ord(" ") and self.current < len(
                self.parent.project.fragments):
            self.parent.active_win = self.parent.player_win
            frag = self.parent.project.fragments[self.current]
            data = frag.get_fragment()
            self.parent.player.play(data)
            self.parent.redraw()
        if key == ord("S"):
            frag = self.parent.project.export()
            self.parent.player.play(frag.raw_data)
            self.parent.redraw()
        if key == ord('t'):
            self.active_win = self.tools
        if key == ord('d'):
            self.parent.project.del_fragment(self.current)

        self.redraw()

    def redraw(self):
        super(Fragments, self).redraw()

        self.win.addstr(self.height - 3, 2, 'd - delete frag, t - tools,')
        self.win.addstr(self.height - 2, 2, 'Shift+S - compile and play all')
        items = list(map(lambda f: f"{f.name} (length: {f.project_length})",
                         self.parent.project.fragments))

        self.draw_list(items)
        self.win.refresh()
        if self.active_win:
            self.tools.redraw()


class FragmentEditor(ScrollableWindow):
    def __init__(self, y, x, height, width, parent):
        super().__init__(y, x, height, width,
                         "Fragment Editor", "SHIFT+E", parent)

        self.win_key = "E"
        self.fragment = None

        self._items = {
            "name": lambda: self.fragment.name,
            "begin in the project": lambda: self.fragment.project_begin,
            "begin in the  track": lambda: self.fragment.track_begin,
            "project length": lambda: self.fragment.project_length,
            "volume": lambda: lambda: self.fragment.volume,
            "speed": lambda: self.fragment.speed,
            "fade in": lambda: self.fragment.fade_in,
            "fade out": lambda: self.fragment.fade_out
        }

        self._handlers = [
            lambda k: self.check_key_name(k),
            lambda k: self.check_key_project_begin(k),
            lambda k: self.check_key_track_begin(k),
            lambda k: self.check_key_project_length(k),
            lambda k: self.check_key_volume(k),
            lambda k: self.check_key_speed(k),
            lambda k: self.check_key_fade_in(k),
            lambda k: self.check_key_fade_out(k)
        ]

    def redraw(self):
        super(FragmentEditor, self).redraw()
        items = []
        if self.fragment is not None:
            items.append(f"name: {self.fragment.name}")
            items.append("begin in the project: "
                         f"{self.fragment.project_begin}")
            items.append(f"begin in the track: {self.fragment.track_begin}")
            items.append(f"project length: {self.fragment.project_length}")
            items.append(f"volume: {round(self.fragment.volume * 100, 2)}%")
            items.append(f"speed: {round(self.fragment.speed * 100, 2)}%")
            items.append(f"fade in: {self.fragment.fade_in}")
            items.append(f"fade out: {self.fragment.fade_out}")

        self.draw_list(items)
        self.win.refresh()

    def check_key(self, key):
        if self.fragment is None:
            return
        if key == curses.KEY_DOWN and self.current + 1 < len(self._items):
            self.scroll(1)
        elif key == curses.KEY_UP:
            if self.current > 0:
                self.scroll(-1)
        else:
            self._handlers[self.current](key)

        self.parent.project.sort_fragments()
        self.parent.fragments_win.redraw()

        self.redraw()

    def check_key_name(self, key):
        if key == curses.KEY_BACKSPACE:
            if len(self.fragment.name) > 1:
                self.fragment.name = self.fragment.name[:-1]
            return

        if chr(key).isprintable():
            self.fragment.name += chr(key)

    def check_key_volume(self, key):
        if key == curses.KEY_LEFT and self.fragment.volume > 0.01:
            self.fragment.volume = max(self.fragment.volume - 0.01, 0)
        if key == curses.KEY_RIGHT:
            self.fragment.volume += 0.01

    def check_key_speed(self, key):
        if key == curses.KEY_LEFT and self.fragment.speed > 0.5:
            self.fragment.speed = max(self.fragment.speed - 0.05, 0)
        if key == curses.KEY_RIGHT:
            self.fragment.speed += 0.05

    def check_key_track_begin(self, key):
        if key == curses.KEY_LEFT:
            self.fragment.set_track_begin(self.fragment.track_begin - .5)
        if key == curses.KEY_RIGHT:
            self.fragment.set_track_begin(self.fragment.track_begin + .5)
        if key == curses.KEY_BACKSPACE:
            self.fragment.set_track_begin(del_last_digit(
                self.fragment.track_begin))
        if chr(key).isdigit():
            num = float(str(self.fragment.track_begin) + chr(key))
            if num - int(num) < 1e-10:
                num = int(num)
            self.fragment.set_track_begin(num)

    def check_key_project_begin(self, key):
        if key == curses.KEY_LEFT and self.fragment.project_begin > 0.5:
            self.fragment.project_begin -= .5
        if key == curses.KEY_RIGHT:
            self.fragment.project_begin += .5
        if key == curses.KEY_BACKSPACE:
            self.fragment.project_begin = del_last_digit(
                self.fragment.project_begin)
        if chr(key).isdigit():
            num = float(str(self.fragment.project_begin) + chr(key))
            if num - int(num) < 1e-10:
                num = int(num)
            self.fragment.project_begin = num

    def check_key_project_length(self, key):
        if key == curses.KEY_LEFT:
            self.fragment.set_project_length(self.fragment.project_length - .5)
        if key == curses.KEY_RIGHT:
            self.fragment.set_project_length(self.fragment.project_length + .5)
        if key == curses.KEY_BACKSPACE:
            self.fragment.set_project_length(del_last_digit(
                self.fragment.project_length))
        if chr(key).isdigit():
            num = float(str(self.fragment.project_length) + chr(key))
            if num - int(num) < 1e-10:
                num = int(num)
            self.fragment.set_project_length(num)

    def check_key_fade_in(self, key):
        if key == curses.KEY_LEFT and self.fragment.fade_in >= 0.5:
            self.fragment.fade_in -= 0.5
        if (key == curses.KEY_RIGHT and
                self.fragment.fade_in < self.fragment.project_length):
            self.fragment.fade_in += 0.5

        if key == curses.KEY_BACKSPACE:
            self.fragment.fade_in = del_last_digit(
                self.fragment.fade_in)
        if chr(key).isdigit():
            num = float(str(self.fragment.fade_in) + chr(key))
            if num - int(num) < 1e-10:
                num = int(num)
            self.fragment.fade_in = num

    def check_key_fade_out(self, key):
        if key == curses.KEY_LEFT and self.fragment.fade_out >= 0.5:
            self.fragment.fade_out -= 0.5
        if (key == curses.KEY_RIGHT and
                self.fragment.fade_out < self.fragment.project_length):
            self.fragment.fade_out += 0.5

        if key == curses.KEY_BACKSPACE:
            self.fragment.fade_out = del_last_digit(
                self.fragment.fade_out)
        if chr(key).isdigit():
            num = float(str(self.fragment.fade_out) + chr(key))
            if num - int(num) < 1e-10:
                num = int(num)
            self.fragment.fade_out = num


class HelpWindow(ScrollableWindow):
    def __init__(self, y, x, height, width, data, parent):
        super().__init__(y, x, height, width, 'Help',
                         'F1 (ESC for close this window)', parent)
        self.win_key = curses.KEY_F1
        self.data = list(map(lambda x_: x_[:-1], data))

    def redraw(self):
        super().redraw()
        self.draw_list(self.data, False)
        self.win.refresh()

    def check_key(self, key):
        if key == curses.KEY_DOWN and self.current < len(self.data) - 1:
            self.scroll(1)

        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)

        if key == 27:
            self.parent.active_win = self.parent.player_win
            self.parent.redraw()
            return

        self.redraw()


class Tools(ScrollableWindow):
    def __init__(self, y, x, height, width, funcs: dict, parent):
        super().__init__(y, x, height, width, "Tools", parent=parent)
        self.funcs = funcs

    def redraw(self):
        super().redraw()
        self.draw_list(list(self.funcs.keys()))

        self.win.refresh()

    def check_key(self, key):
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == curses.KEY_DOWN and self.current + 1 < len(self.funcs):
            self.scroll(1)
        if key == 27:
            self.parent.active_win = None
        if key == 10:
            k = list(self.funcs.keys())[self.current]
            self.funcs[k]()
            self.parent.active_win = None

        self.parent.redraw()


class FileSaver(FileWalker):
    def __init__(self, y, x, height, width, parent, exts=None):
        super().__init__(y, x, height, width, parent)
        self.end = False
        self.filename = ''
        self.exts = exts
        if not exts:
            self.exts = ['.wav', '.mp3']
        self.ext = 0

    def redraw(self):
        if not self.result:
            super().redraw()
        else:
            self.draw_filename_input()

    def check_key(self, key):
        if not self.result:
            super().check_key(key)
        else:
            if key == curses.KEY_DOWN or key == curses.KEY_UP:
                self.ext = (self.ext + 1) % len(self.exts)
            elif key == 27:
                self.result = "<ESC>"
                self.end = True
            elif key == curses.KEY_BACKSPACE:
                self.filename = self.filename[:-1]
            elif key == 10:
                self.end = True
                self.result = (os.path.join(self.result, self.filename) +
                               self.exts[self.ext])
            elif chr(key).isprintable():
                self.filename += chr(key)

    def draw_filename_input(self):
        ScrollableWindow.redraw(self)
        self.win.addstr(2, 2, "Enter filename:")
        self.win.addstr(3, 2, self.filename)
        self.win.addstr(4, 2, 'extension: ' + self.exts[self.ext])
        self.win.addstr(5, 2, 'for changing extension press UP or DOWN')
        self.win.refresh()
