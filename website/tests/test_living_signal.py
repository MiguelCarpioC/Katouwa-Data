import io
import unittest
import wave
from living_signal import normalize_index, frequency_hz, create_sonification_wav

class TestLivingSignal(unittest.TestCase):
    def test_normalize(self):
        self.assertAlmostEqual(normalize_index(-1),0)
        self.assertAlmostEqual(normalize_index(0),.5)
        self.assertAlmostEqual(normalize_index(1),1)
        self.assertAlmostEqual(normalize_index(3),1)
    def test_frequency(self):
        self.assertAlmostEqual(frequency_hz(-1),220)
        self.assertAlmostEqual(frequency_hz(1),660)
    def test_wav(self):
        out=create_sonification_wav([.2,.3,.4])
        with wave.open(io.BytesIO(out),'rb') as wav:
            self.assertEqual(wav.getframerate(),16000)
            self.assertEqual(wav.getnchannels(),1)
            self.assertGreater(wav.getnframes(),8000)
    def test_invalid(self):
        with self.assertRaises(ValueError):create_sonification_wav([])
        with self.assertRaises(ValueError):normalize_index(float('nan'))

if __name__=='__main__':unittest.main()
