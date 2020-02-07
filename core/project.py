import os
from core.track import Track
from core.fragment import Fragment
import shlex

import pydub


class FileException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Project:
    def __init__(self):
        self.tracks = []
        self.fragments = []
        self.formats = ['.mp3', '.wav']

    def add_track(self, path):
        if not path:
            raise FileException("Excepted file path")

        track = Track(path)
        if not track.path:
            raise FileException("Unsupported file")

        if track not in self.tracks:
            self.tracks.append(track)

    def add_dir(self, path):
        if len(path) > 0 and os.path.exists(path) and os.path.isdir(path):
            for i in os.listdir(path):
                if os.path.splitext(i)[-1] in self.formats:
                    try:
                        self.add_track(f'{path}/{i}')
                    except FileException:
                        pass

    def add_fragment_to_end(self, fragment):
        self.fragments.append(fragment)
        fragment.project_begin = self.end

    def add_fragment(self, fragment):
        if isinstance(fragment, int):
            fragment = Fragment(self.tracks[fragment])
        if isinstance(fragment, str):
            track = self.track_by_name(fragment)
            fragment = Fragment(track)
        if isinstance(fragment, Track):
            fragment = Fragment(fragment)
        self.fragments.append(fragment)
        self.sort_fragments()

    def export(self):
        res = pydub.AudioSegment.silent(self.end * 1000, frame_rate=44100)
        for frag in self.fragments:
            res = res.overlay(frag.get_segment(), frag.project_begin * 1000)

        return res

    def del_fragment(self, index: (str, int)):
        if isinstance(index, str):
            self.fragments.remove(self.fragment_by_name(index))
        elif index < len(self.fragments):
            del self.fragments[index]

    def stick(self):
        """Свдигает все фрагметы к началу так чтобы не было пустых ячеек"""
        temp = 0
        for f in self.fragments:
            if f.project_begin > temp:
                f.project_begin = temp
            temp = max(temp, f.project_end)

    @property
    def end(self):
        if not self.fragments:
            return 0
        return max(map(lambda f: f.project_begin + f.project_length,
                       self.fragments))

    def track_by_name(self, name):
        for e in self.tracks:
            if e.filename == name:
                return e

        return None

    def fragment_by_name(self, name):
        for e in self.fragments:
            if e.name == name:
                return e

        return None

    def save_project(self, filename):
        out = "tracks\n"
        for i in self.tracks:
            out += f'"{i.path}"\n'
        out += "fragments\n"
        for i in self.fragments:
            out += (f'"{i.track.path}" {i.track_begin} {i.project_begin} '
                    f'{i.project_length} "{i.name}" {i.volume} {i.speed}\n')
        path = os.path.split(filename)[0]
        if path and not os.path.exists(path):
            os.makedirs(path)
        with open(filename, 'wb') as f:
            f.write(out.encode('utf-8'))

    def load_project(self, fname):
        self.clear()
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                commands = {
                    'tracks': self.add_track,
                    'fragments': self.import_fragment,
                }
                current = None
                for line in f:
                    line = line[:-1]
                    if line in commands:
                        current = commands[line]
                        continue
                    args = shlex.split(line)
                    current(*args)

    def import_fragment(self, *args):
        track = self.track_by_path(args[0])
        frag = Fragment(track, args[4])
        frag.track_begin = float(args[1])
        frag.project_begin = float(args[2])
        frag.project_length = float(args[3])
        frag.volume = float(args[5])
        frag.speed = float(args[6])
        self.fragments.append(frag)

    def clear(self):
        self.tracks = []
        self.fragments = []

    def track_by_path(self, path):
        for e in self.tracks:
            if e.path == path:
                return e
        return None

    def sort_fragments(self):
        self.fragments = sorted(self.fragments, key=lambda f: f.project_begin)
