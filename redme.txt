Final Project Overview
My final project is a music player that functions similarly to a Radio, where every "station" is filled with music and historical broadcasts from their respective years ranging from 1900 to 1985.
In this upload I have included music files from 1940 - 1945. More years may be added to the system simply by adding a folder inside the "music" folder with its name being the year (I.E: 1961), and then storing mp3 or wav files inside.

Features include:
  A slider to select the year.
  FM/AM toggle to switch between music and historical broadcasts
  Automatic playback of songs from the selected year
  Volume control

Setup & Installation
  Install pygame using pip:
    "pip install pygame"
  Make sure audio files are organized in the following folder structure inside the project folder:
    audio/
    ├─ music/
    │  ├─ 1950/
    │  ├─ 1951/
    │  └─ ...
    └─ news/
       ├─ 1950/
       ├─ 1951/
       └─ ...
  Music files go in the music folders and broadcast files go in the news folders. File names should include the year and title, e.g., 1950 Hoop-Dee-Doo - Kay Starr.mp3

Running the Project
  1. Open a terminal or commland prompt in the project directory.
  2. Run the Python script
      python project2.py
  3. The GUI will appear with the year slider, mode button (AM/FM), volume slider, and now playing label.

Usage
  Move the year slider to change the station. The song or broadcast for that year will start automatically.
  Click the AM/FM button to switch between music and historical broadcasts
  Use the volume slider on the right to adjust playback volume
  The now playing label shows the current song or broadcast title. Longer titles scroll like a real radio marquee.

Dependencies
  Python 3.12 or higher
  Pygame for audio playback
