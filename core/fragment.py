import math

from core.track import Track


class Fragment:
    counter = 0

    def __init__(self, track: Track,
                 name=None):
        """project_begin, track_begin, project_length in seconds"""
        self.track = track
        self.project_begin = 0
        self.project_length = self.track.length
        self.track_begin = 0
        self.fade_in = 0
        self.fade_out = 0

        if name is None:
            self.name = '*unnamed%d' % self.counter
            Fragment.counter += 1
        else:
            self.name = name

        self.volume = 1
        self.speed = 1.5

    def get_fragment(self):
        frag = self.track.get_frames()

        db = 10 * math.log10(self.volume)
        frag = frag + db
        return frag.raw_data

    @property
    def track_length(self):
        return self.project_length * self.speed

    @property
    def project_end(self):
        return self.project_begin + self.project_length
