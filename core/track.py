import pydub
import os
from interface.noalsaerror import noalsaerr


class Track:
    def __init__(self, path):
        self.filename = os.path.basename(path)
        self.path = path
        self.format = os.path.splitext(path)[-1][1:]
        try:
            with noalsaerr():
                temp = pydub.AudioSegment.from_file(self.path, self.format)
            self.length = len(temp) / 1000
            self.rate = temp.frame_rate
            self.channels = temp.channels
        except Exception:
            self.path = None

    def get_frames(self, begin=0, length=None):
        """Возвращает начиная с begin длины length

        Parameters:
        begin -- начало фрагмента в секундах
        length -- длина фрагмента в секундах"""

        if length is None or length >= self.length:
            length = self.length
        with noalsaerr():
            return pydub.AudioSegment.from_file(
                self.path, self.format)[begin * 1000:(begin + length) * 1000]

    def __repr__(self):
        return f"Track({self.path})"

    def __eq__(self, other):
        return isinstance(other, Track) and self.path == other.path

    def __hash__(self):
        return hash(self.path)
