"""Documented *artistic* encoding of environmental index values.

The output is not an environmental classification, a physical acoustic
measurement, or a validated mangrove-health index. Its sole purpose is to
translate the numbers in an input series to a repeatable multimodal metaphor.
"""
from __future__ import annotations
import io
import wave
import numpy as np


def normalize_index(value: float) -> float:
    """Normalize NDVI/EVI in the physical range [-1, 1] to [0, 1]."""
    if not np.isfinite(float(value)):
        raise ValueError('Cannot map a nonfinite value to a signal')
    return float(np.clip((float(value) + 1.0) / 2.0, 0.0, 1.0))


def frequency_hz(value: float) -> float:
    """Simple deterministic illustration: value −1→220 Hz, +1→660 Hz."""
    return 220.0 + 440.0 * normalize_index(value)


def create_sonification_wav(values, sample_rate: int = 16000,
                            seconds_per_note: float = 0.17,
                            max_notes: int = 48) -> bytes:
    """Turn a supplied sequence of index values into a short WAV file.

    Each valid number maps to exactly one sine tone. This is an arbitrary,
    transparent artistic encoding, not recorded environmental sound.
    """
    if not 8000 <= sample_rate <= 48000:
        raise ValueError('sample rate outside supported range')
    arr=np.asarray(values,dtype=float).reshape(-1)
    arr=arr[np.isfinite(arr)][:max_notes]
    if not len(arr):
        raise ValueError('No finite values to sonify')
    n=max(32,int(sample_rate*seconds_per_note))
    t=np.arange(n)/sample_rate
    rise=min(int(.016*sample_rate),max(8,n//10))
    envelope=np.ones(n,dtype=float)
    envelope[:rise]=np.linspace(0,1,rise)
    envelope[-rise:]=np.linspace(1,0,rise)
    pcm=[]
    for v in arr:
        tone=.24*np.sin(2*np.pi*frequency_hz(v)*t)*envelope
        pcm.append((tone*32767).astype('<i2'))
    with io.BytesIO() as b:
        with wave.open(b,'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(sample_rate)
            w.writeframes(np.concatenate(pcm).tobytes())
        return b.getvalue()
