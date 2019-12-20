import curses
import math
import os
import threading
import time

from core import player as pl
from core import fragment as fr

# Color pairs for windows #
WINDOW = 1
ACTIVE_WINDOW = 2
ACTIVE_LINE = 2
MENU = 1
# ----------------------- #


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
        super().__init__(0, 0, 1, parent.width, "menu", "Sh+M", parent)
        self.win.attron(curses.color_pair(MENU))
        self.walker = None

        self.win_key = ord("M")

        self.options = [
            "open",
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
        elif key == 10 and self.current == 0:
            self.walker = FileWalker(self.parent.height // 4,
                                     self.parent.width // 4,
                                     self.parent.height // 2,
                                     self.parent.width // 2, self.parent)

        if self.walker and self.walker.result:
            try:
                self.parent.project.add_track(self.walker.result)
            except Exception:
                pass
            self.walker = None
            self.parent.active_win = self.parent.tracksWin
            self.parent.redraw()

        self.redraw()


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
        super().__init__(y, x, height, width, "Tracks", "Sh+4", parent)
        self.win_key = ord("$")

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
        self.padding = 2

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
        self.win.attron(curses.color_pair(WINDOW))
        self.draw_list(self._elems)
        self.win.refresh()

    def check_key(self, key):
        path = os.path.join(self._path, self._elems[self.current])

        if key == curses.KEY_DOWN and self.current + 1 < len(self._elems):
            self.scroll(1)
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == 10:
            if os.path.isdir(path):
                self._path = os.path.abspath(path)
                self._elems = [".."]
                temp = next(os.walk(self._path))
                self._elems.extend(temp[1])
                self._elems.extend(temp[2])
            else:
                self.result = path
                return
        self.redraw()


class Player(ScrollableWindow):
    full_cell = "█"
    semi_cell = "▌"

    def __init__(self, player: pl.Player, y, x, height, width, parent=None):
        super().__init__(y, x, height, width, name="Player",
                         key="Sh+3", parent=parent)

        self.player = player
        self.isWorking = True

        self.win_key = ord("#")

        self._thread = threading.Thread(target=self._redraw_timeline)
        self._thread.start()

    def redraw(self):
        super(Player, self).redraw()
        self.win.addstr(self.padding, self.padding, self.get_timeline())
        self.win.addstr(self.padding + 1, self.padding,
                        f"{round(self.player.current_time)}/"
                        f"{round(self.player.full_time)}")

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
                                        "Fragments", "Sh+2", parent)

        self.win_key = ord("@")

    def check_key(self, key):
        if key == curses.KEY_DOWN and self.current + 1 < len(
                self.parent.project.fragments):
            self.scroll(1)
        if key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        if key == 10:
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

        self.redraw()

    def redraw(self):
        super(Fragments, self).redraw()

        items = list(map(lambda f: f"{f.name} (length: {f.project_length})",
                         self.parent.project.fragments))

        self.draw_list(items)
        self.win.refresh()


class FragmentEditor(ScrollableWindow):
    def __init__(self, y, x, height, width, parent):
        super().__init__(y, x, height, width,
                         "Fragment Editor", "Sh+1", parent)

        self.win_key = ord("!")
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
            lambda k: None,
            lambda k: None,
            lambda k: None,
            lambda k: self.check_key_volume(k),
            lambda k: self.check_key_speed(k),
            lambda k: None,
            lambda k: None,
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
        elif key == curses.KEY_UP and self.current > 0:
            self.scroll(-1)
        else:
            self._handlers[self.current](key)

        self.redraw()

    def check_key_name(self, key):
        if key == 8:
            if len(self.fragment.name) > 1:
                self.fragment.name = self.fragment.name[:-1]
            return
        key = chr(key)
        if key.isprintable():
            self.fragment.name += key

    def check_key_volume(self, key):
        if key == curses.KEY_LEFT and self.fragment.volume > 0:
            self.fragment.volume = max(self.fragment.volume - 0.01, 0)
        if key == curses.KEY_RIGHT:
            self.fragment.volume += 0.01

    def check_key_speed(self, key):
        if key == curses.KEY_LEFT and self.fragment.speed > 0.5:
            self.fragment.speed = max(self.fragment.speed - 0.05, 0)
        if key == curses.KEY_RIGHT:
            self.fragment.speed += 0.05

    def check_common_key(self, field, key):
        if key == 8:
            return float(str(field)[:-1])
        if chr(key).isdigit() or chr(key) == '.' and '.' not in str(field):
            return float(str(field) + chr(key))

        return field
