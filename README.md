# FocusCam — AI-Powered Focus Tracking

A desktop application that uses your webcam to detect distractions and track your focus in real time. Built with **PyQt6**, **OpenCV**, and **MediaPipe**.

## Acknowledgments

This project is a complete overhaul of the original **FocusCam** by [Ayotomide Ogunsami](https://www.linkedin.com/in/ayotomide-ogunsami-93aa61312). The original concept — real-time distraction detection via webcam — was her creation, and this version builds on that foundation with a full PyQt6 GUI, multi-threaded architecture, focus history persistence, and extensive UX refinements.

Thank you to everyone who provided feedback and suggestions during development.

## Features

- **Real-time face & eye tracking** — MediaPipe FaceMesh with distraction degree scoring (0–100%)
- **Focus Level bar** — Color-coded progress bar (green → amber → red)
- **Focus Timeline** — 60-second mini chart showing focus fluctuations
- **Focus History grid** — 6-week contribution grid with month-indicating color borders
- **Distraction logging** — Auto-records each distraction event with timestamp and duration
- **Collapsible side panel** — Every section can be collapsed to save space
- **Login system** — User authentication with MySQL database
- **Camera settings** — Adjustable thresholds, sensitivity, and alert preferences
- **Alert sounds** — Audio feedback when distraction is detected

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt6 |
| Face Detection | MediaPipe FaceMesh |
| Computer Vision | OpenCV |
| Database (local) | SQLite |
| Database (users) | MySQL |
| Audio | QSound / winsound |
| Packaging | PyInstaller |

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/FocusCam.git
cd FocusCam

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Requirements

- Python 3.10+ (MediaPipe compatibility)
- Webcam
- MySQL server (optional, for user login system)

## Usage

1. Launch the app with `python main.py`
2. Log in or register a new account
3. The camera will start automatically
4. The side panel shows your focus statistics in real time
5. Click section headers (▼) to collapse/expand any panel

### Controls

| Key/Action | Function |
|-----------|----------|
| **Start/Stop** | Toggle camera detection |
| **Settings** | Adjust detection thresholds, alerts |
| **View → Side Panel** | Toggle statistics panel |
| **Collapse ▲** | Click any section header to hide its content |

## Project Structure

```
my_FocusCam/
├── app/                    # GUI application modules
│   ├── main_window.py      # Main window with camera view
│   ├── camera_widget.py    # Camera feed + detection worker
│   ├── statistics_widget.py# Statistics panel
│   ├── contribution_grid.py# Focus history grid
│   ├── distraction_overlay.py # Distraction alert overlay
│   ├── login_dialog.py     # User login/register
│   ├── settings_dialog.py  # Settings UI
│   └── theme.py            # Theme management
├── core/                   # Core logic
│   ├── detector.py         # Face/eye detection
│   ├── distraction_engine.py # Distraction state machine
│   └── camera_manager.py   # Camera management
├── config/                 # Configuration
├── utils/                  # Utilities
├── resources/              # Icons, sounds, models
└── main.py                 # Entry point
```

## License

This project is open source and available under the MIT License.
