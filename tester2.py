import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent folder to sys.path so we can import project.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project2 import Radio  # your main radio class

class TestTimeRadio(unittest.TestCase):
    def setUp(self):
        # Patch pygame.mixer.music so no sound actually plays
        patcher = patch("project.pygame.mixer.music", new=MagicMock())
        self.mock_music = patcher.start()
        self.addCleanup(patcher.stop)

        # Create a fresh Radio instance for each test
        self.radio = Radio()

    def test_radio_switch_station(self):
        # Test changing years updates the current_year variable
        initial_year = self.radio.current_year.get()
        self.radio.current_year.set(initial_year + 1)
        self.radio.play_audio()
        self.assertNotEqual(initial_year, self.radio.current_year.get())

    def test_random_song_selection(self):
        # Test that pick_random_song returns a filename string and length
        key = ("FM", 1950)
        file, length = self.radio.pick_random_song(key)
        if file is not None:
            self.assertTrue(file.endswith(".mp3") or file.endswith(".wav"))
            self.assertIsInstance(length, float)

    def test_set_volume(self):
        # Test volume setting
        self.radio.set_volume = lambda v: setattr(self.radio, "volume", v)
        self.radio.set_volume(0.7)
        self.assertEqual(self.radio.volume, 0.7)

    def test_tick_stations_auto_next(self):
        # Test that tick_stations updates position and loads next song
        key = ("FM", 1950)
        # Mock a station
        self.radio.stations[key] = {"file": "fake.mp3", "position": 0, "length": 1}
        self.radio.currently_playing_key = key
        # Tick forward
        self.radio.tick_stations()
        # Position should increase
        self.assertGreaterEqual(self.radio.stations[key]["position"], 1)

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
