import os
from core.track import Track


class FileException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Project:
    def __init__(self):
        self.tracks = []
        self.fragments = []
        self.formats = ['.mp3', '.wav']
        self.project_end = 0

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
        fragment.project_begin = self.project_end
        self.fragments = sorted(self.fragments, key=lambda x: x.project_begin)
        self.project_end += fragment.project_length

    def add_fragment(self, fragment):
        self.fragments.append(fragment)
        # self.fragments =
        # sorted(self.fragments, key=lambda f: f.project_begin)
