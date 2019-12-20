import numpy as np
import pydub


def speedx(segment, factor):
    """ Multiplies the sound's speed by some `factor` """
    channels = segment.split_to_mono()
    res = []
    for ch in channels:
        sound_array = list(ch.raw_data)
        indices = np.round(np.arange(0, len(sound_array), factor))
        indices = indices[indices < len(sound_array)].astype(int)
        res.append(pydub.AudioSegment(bytes(np.array(sound_array)[indices.astype(int)].tolist()), sample_width=segment.sample_width, frame_rate=segment.frame_rate, channels=1))
    return res[0].raw_data
