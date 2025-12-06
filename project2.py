import tkinter as tk
from tkinter import ttk
import os
import random
import pygame
import threading

# Initialize mixer
pygame.mixer.quit()                              
pygame.mixer.init(buffer=4096)                   

# ---------- Station class ----------
class Station:
    def __init__(self, mode, year, folder_root="audio"): 
        self.mode = mode                          # "FM" or "AM"
        self.year = year                          # int year
        self.folder_root = folder_root            # base audio folder
        self.files = self._scan_files()           # list of file paths
        self.current_file = None                  # currently selected file path
        self.length = 0.0                         # length in seconds
        self.position = 0.0                       # simulated playback position in seconds
        self.last_file = None                     # last played file
    
    def _year_folder(self):
        base = "music" if self.mode == "FM" else "news"
        return os.path.join(self.folder_root, base, str(self.year))
    
    def _scan_files(self):
        year_folder = self._year_folder()
        if not os.path.exists(year_folder):
            return []                              # no files available
        files = [os.path.join(year_folder, f) for f in os.listdir(year_folder)
                 if f.lower().endswith((".mp3", ".wav"))]
        return sorted(files)                       # deterministic order
    
    def refresh(self):
        self.files = self._scan_files()            # re-scan folder
    
    def pick_random(self):
        """Pick a random file, avoiding immediate repeat if possible. Returns (file, length)."""
        self.refresh()                             # ensure we see new files if any
        if not self.files:
            return None, 0
        choices = list(self.files)
        # Prefer not to pick last_file if possible
        if self.last_file and len(choices) > 1:
            try:
                choices.remove(self.last_file)
            except ValueError:
                pass
        chosen = random.choice(choices)
        length = self._safe_get_length(chosen)
        return chosen, length
    
    def _safe_get_length(self, file_path):
        """Attempt to get audio length. If it fails (large file or unsupported),
           fall back to reasonable defaults based on mode."""
        try:
            # pygame.mixer.Sound may load whole file into memory for some formats; wrap in try
            snd = pygame.mixer.Sound(file_path)    # may raise for huge or invalid files
            length = snd.get_length()
            return float(length)
        except Exception:
            # fallback defaults: music ~3min, news ~10min
            return 180.0 if self.mode == "FM" else 600.0
    
    def start_first_time(self):
        """Pick a starting song and random start position for a station not yet used."""
        file, length = self.pick_random()
        if file is None:
            return None
        # random start in first 70% to avoid near-end starts
        start_pos = random.uniform(0, max(0.0, length * 0.7))
        self.current_file = file
        self.length = length
        self.position = start_pos
        self.last_file = None
        return file
    
    def advance_to_next(self):
        """Select next song (no immediate repeat), reset position to 0, and set last_file."""
        previous = self.current_file
        file, length = self.pick_random()
        if file is None:
            return None
        self.last_file = previous
        self.current_file = file
        self.length = length
        self.position = 0.0
        return file

# ---------- AudioPlayer class ----------
class AudioPlayer:
    def __init__(self):
        # pygame.mixer is already initialized above
        pass
    
    def play(self, file_path, start=0.0, fade_ms=0):
        """Play file_path from start (seconds) with optional fade-in (ms)."""
        try:
            pygame.mixer.music.load(file_path)     # streaming load from disk
            # pygame supports start parameter on play; ensure start is float >=0
            pygame.mixer.music.play(start=float(start), fade_ms=fade_ms)
        except Exception:
            # if load/play fails, ignore playback but continue program logic
            pass
    
    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
    
    def set_volume(self, vol):
        """vol is float 0.0 - 1.0"""
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        except Exception:
            pass
    
    def is_busy(self):
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
    
    def get_pos_seconds(self):
        """Return position from mixer in seconds (approx). May be -1 if unsupported."""
        try:
            ms = pygame.mixer.music.get_pos()
            if ms < 0:
                return None
            return ms / 1000.0
        except Exception:
            return None

# ---------- Radio (GUI + Controller) ----------
class Radio(tk.Tk):
    def __init__(self):
        super().__init__()                        # initialize Tk
        self.title("Time Radio")                  # window title
        self.geometry("700x380")                  # initial size
        
        # state
        self.current_year = tk.IntVar(value=1950) # selected year
        self.mode = tk.StringVar(value="FM")      # "FM" or "AM"
        self.stations = {}                        # map (mode, year) -> Station instance
        self.currently_playing_key = None         # (mode, year) key of station being heard
        
        # audio helper
        self.audio = AudioPlayer()                # handles pygame playback
        
        # marquee control
        self.marquee_job = None
        self.marquee_text = ""
        self.marquee_index = 0
        self.marquee_delay = 200
        
        # build UI
        self.create_widgets()
        
        # start ticking stations every second
        self.after(1000, self.tick_stations)
    
    # ---------- UI ----------
    def create_widgets(self):
        # configure grid columns so left expands, right stays tight
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        
        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)  # left controls
        
        right_frame = tk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="n", padx=20, pady=10)     # right volume
        
        self.left_frame = left_frame
        self.right_frame = right_frame
        
        # Now Playing label (top of left)
        self.now_playing_label = tk.Label(left_frame, text="Now Playing: None", width=50, anchor="w")
        self.now_playing_label.pack(pady=(0, 8))                         # label for song
        
        # Year slider and label
        tk.Label(left_frame, text="Select Year").pack(pady=(0, 5))       # small label
        self.year_slider = tk.Scale(
            left_frame,
            from_=1900,
            to=1985,
            orient="horizontal",
            variable=self.current_year,
            command=self.update_year_label
        )
        self.year_slider.pack(fill="x", padx=12)                        # stretch horizontally
        
        self.year_label = tk.Label(left_frame, text=f"Year: {self.current_year.get()}")
        self.year_label.pack(pady=6)
        
        # Mode button
        self.mode_button = tk.Button(left_frame, text=self.mode.get(), command=self.toggle_mode)
        self.mode_button.pack(pady=6)
        
        # Play button
        self.play_button = tk.Button(left_frame, text="Play", command=self.play_audio)
        self.play_button.pack(pady=6)
        
        # Stop button
        self.stop_button = tk.Button(left_frame, text="Stop", command=self.stop_audio)
        self.stop_button.pack(pady=6)
        
        # Volume label + vertical ttk slider on right (centered relative to left content)
        tk.Label(right_frame, text="Volume").pack(pady=(0, 6))           # volume label
        
        self.volume_slider = ttk.Scale(
            right_frame,
            from_=100,
            to=0,
            orient="vertical",
            length=180,
            command=self.set_volume
        )
        self.volume_slider.set(50)
        self.volume_slider.pack(expand=True, pady=10)                   # center vertically
    
    # ---------- UI helpers ----------
    def update_year_label(self, value):
        self.year_label.config(text=f"Year: {value}")                   # update display
        # Immediately tune to new year like a radio dial (no fade-out)
        self.play_audio()
    
    def toggle_mode(self):
        new_mode = "AM" if self.mode.get() == "FM" else "FM"
        self.mode.set(new_mode)
        self.mode_button.config(text=new_mode)
        # When changing mode, immediately tune to the same year in new mode
        self.play_audio()
    
    def set_volume(self, value):
        vol = float(value) / 100.0
        self.audio.set_volume(vol)                                      # apply volume immediately
    
    def stop_audio(self):
        # stop playback but keep station positions
        self.audio.stop()
        self.currently_playing_key = None
    
    # ---------- Station management ----------
    def _get_station(self, mode, year):
        key = (mode, year)
        station = self.stations.get(key)
        if station is None:
            station = Station(mode, year)                              # create station object if new
            self.stations[key] = station
        return station
    
    # ---------- Play logic ----------
    def play_audio(self):
        year = int(self.current_year.get())
        mode = self.mode.get()
        key = (mode, year)
        station = self._get_station(mode, year)                         # ensure station exists
        
        # If no current file for station, pick one and random-start
        if station.current_file is None:
            station.start_first_time()
            if station.current_file is None:
                # no audio in folder
                self.now_playing_label.config(text="Now Playing: (no audio)")
                return
        
        # Stop currently playing station without overwriting station's live position
        if self.audio.is_busy() and self.currently_playing_key is not None:
            # Save nothing here; positions are advanced by tick_stations in background
            self.audio.stop()
        
        # Play this station's current file starting at station.position with fade-in
        file_to_play = station.current_file
        start_pos = station.position
        self.audio.play(file_to_play, start=start_pos, fade_ms=500)     # fade-in
        self.currently_playing_key = key                                # mark this station as active
        
        # Update Now Playing label (clean name)
        song_name = os.path.basename(file_to_play)
        if "_" in song_name:
            song_name = song_name.split("_", 1)[1]
        song_name = os.path.splitext(song_name)[0].strip()
        self.start_marquee(song_name)                                   # run marquee only for active station
    
    # ---------- Marquee ----------
    def start_marquee(self, text, delay=200):
        # Cancel previous marquee job if running
        if self.marquee_job is not None:
            try:
                self.after_cancel(self.marquee_job)
            except Exception:
                pass
            self.marquee_job = None
        
        # If short text, don't scroll
        label_char_width = 40                                           # approximate visible characters
        if len(text) <= label_char_width:
            self.now_playing_label.config(text=f"Now Playing: {text}")
            return
        
        # Start scrolling
        self.marquee_text = f"Now Playing: {text}   "                   # text to rotate
        self.marquee_index = 0
        self.marquee_delay = delay
        self.update_marquee()
    
    def update_marquee(self):
        display = self.marquee_text[self.marquee_index:] + self.marquee_text[:self.marquee_index]
        self.now_playing_label.config(text=display)
        self.marquee_index = (self.marquee_index + 1) % len(self.marquee_text)
        self.marquee_job = self.after(self.marquee_delay, self.update_marquee)
    
    # ---------- Tick stations (real-time simulation) ----------
    def tick_stations(self):
        # Advance only the active station's simulated position plus keep other stations ticking lightly
        # This reduces CPU and avoids interfering with audio thread
        # First, advance all stations' positions by 1 second (simulate live time)
        for key, station in list(self.stations.items()):
            station.position += 1.0                                   # tick 1 second
            if station.position >= station.length:
                # song ended for this station -> pick next
                prev = station.current_file
                next_file = station.advance_to_next()
                if key == self.currently_playing_key:
                    # if user is listening, immediately play next song (fade-in)
                    if next_file:
                        self.audio.play(next_file, start=0.0, fade_ms=500)
                        # update Now Playing marquee for new file
                        song_name = os.path.basename(next_file)
                        if "_" in song_name:
                            song_name = song_name.split("_", 1)[1]
                        song_name = os.path.splitext(song_name)[0].strip()
                        self.start_marquee(song_name)
        # schedule next tick
        self.after(1000, self.tick_stations)
    
# ---------- Run app ----------
if __name__ == "__main__":
    app = Radio()
    app.mainloop()
