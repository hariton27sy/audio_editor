import math
import pydub

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
        """Returns raw data"""
        frag = self.track.get_frames(self.track_begin, self.track_length)

        db = 10 * math.log10(self.volume)
        frag = frag + db
        if self.fade_out:
            frag = frag.fade_out(int(self.fade_out * 1000))
        if self.fade_in:
            frag = frag.fade_in(int(self.fade_in * 1000))
        if abs(self.speed - 1) < 1e-2:
            return frag.raw_data

        return frag.set_frame_rate(int(frag.frame_rate / self.speed)).raw_data

    def get_segment(self):
        """Returns pydub AudioSegment"""
        return pydub.AudioSegment(self.get_fragment(),
                                  frame_rate=self.track.rate,
                                  channels=self.track.channels,
                                  sample_width=2)

    @property
    def track_length(self):
        return self.project_length * self.speed

    @track_length.setter
    def track_length(self, val):
        self.project_length = val / self.speed

    @property
    def project_end(self):
        return self.project_begin + self.project_length

    def set_track_begin(self, t):
        if t < 0:
            self.track_begin = 0
        elif t > self.track.length:
            self.track_begin = self.track.length
            self.track_length = 0
        elif t + self.track_length > self.track.length:
            self.track_begin = t
            self.track_length = self.track.length - t
        else:
            self.track_begin = t

    def set_project_length(self, t):
        if t < 0:
            self.project_length = 0
        elif t * self.speed > self.track.length:
            self.project_length = self.track.length / self.speed
            self.track_begin = 0
        elif self.track_begin + t * self.speed > self.track.length:
            self.track_begin = self.track.length - t * self.speed
            self.project_length = t
        else:
            self.project_length = t
