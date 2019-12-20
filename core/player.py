import pyaudio
import threading
import time


class Player:
    def __init__(self, sampwidth=2, channels=2, rate=44100):
        self.pyAudio = pyaudio.PyAudio()
        self.player = self.pyAudio.open(format=self
                                        .pyAudio
                                        .get_format_from_width(sampwidth),
                                        channels=channels,
                                        rate=rate,
                                        output=True)

        self._sampwidth = sampwidth
        self._channels = channels
        self._rate = rate

        self._isPlaying = False
        self._data=None
        self._thread = None
        self._dt = 10
        self._nframes = 0
        self._pos = 0

    def close(self):
        self.stop()
        time.sleep(0.1)

        self.player.close()
        self.pyAudio.terminate()

    def stop(self):
        self.pause()
        self._pos = 0

    def pause(self):
        self._isPlaying = False
        if self._thread:
            self._thread.join()

    def play(self, data=None):
        """Play given data"""
        if data is None:
            self.play1()
            return
        self.stop()

        self._data = data
        self._nframes = len(data) // self.frame_size

        self.play1()

    def play1(self):
        """Renew playing of selected data. If not data, it does nothing"""
        if not self._data:
            return

        if not self._isPlaying:
            self._isPlaying = True
            self._thread = threading.Thread(target=self._play)
            self._thread.start()

    def _play(self):
        while self._isPlaying:
            if self._pos >= self._nframes:
                self._pos = self._nframes
                self._isPlaying = False
                break

            self.player.write(self._data[self._pos * self.frame_size:
                                         (self._pos + self._dt)
                                         * self.frame_size])

            self._pos += self._dt

    def translate_pos(self, delta=1):
        """Moves player position by delta. Delta in seconds, positive number
        moves forward, negative back.
        By default translate forward by 1 second"""
        was_playing = self._isPlaying
        self.pause()
        self._pos += int(delta * self._rate)
        if self._pos < 0:
            self._pos = 0
        if self._pos > self._nframes:
            self._pos = self._nframes
        if was_playing:
            self.play1()

    @property
    def frame_size(self):
        return self._sampwidth * self._channels

    @property
    def full_time(self):
        """Returns data duration in seconds as real number"""
        return self._nframes / self._rate

    @property
    def current_time(self):
        """Returns current position of the data in seconds as real number"""
        return self._pos / self._rate

    @property
    def is_working(self):
        return self._isPlaying
