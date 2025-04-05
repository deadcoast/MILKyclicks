# MILKyclicks

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)]()

An advanced auto-clicker with a minimal ASCII-styled GUI for macOS. MILKyclicks provides a lightweight, customizable solution for automating mouse clicks with precise control over clicking speed.

![MILKyclicks Screenshot](assets/preview.png)

## Features

- **Minimal Interface**: Sleek, compact design with expandable interface
- **ASCII Art Design**: Unique retro-inspired aesthetic with precise ASCII elements
- **Adjustable Click Speed**: Control click frequency from 1 to 1000 clicks per minute
- **Keyboard Shortcuts**: Easy activation/deactivation with hotkeys
- **Status Notifications**: Clear visual feedback on operation status
- **Customizable**: Adjustable settings with visual feedback

## Table of Contents

- [Installation](#installation)
- [System Requirements](#system-requirements)
- [Usage](#usage)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [GUI Elements](#gui-elements)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Installation

### Option 1: Use the pre-built application (Recommended)

1. Download the latest release from the [Releases](https://github.com/deadcoast/MILKyclicks/releases) page
2. Move `MILKyclicks.app` to your Applications folder
3. Launch the application

### Option 2: Run from source

1. Clone the repository:
```bash
git clone https://github.com/deadcoast/MILKyclicks.git
cd MILKyclicks
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python src/main.py
```

## System Requirements

- **Operating System**: macOS 10.14 (Mojave) or newer
- **Python**: 3.10 or newer (if running from source)
- **Required Permissions**: Accessibility permissions (see [Troubleshooting](#troubleshooting))

## Usage

### First Launch

1. On first launch, MILKyclicks will request Accessibility permissions
2. Follow the on-screen instructions to grant these permissions
3. You may need to restart the application after granting permissions

### Basic Operation

1. Launch MILKyclicks
2. The application appears as a minimal bar at the top of your screen
3. Expand the interface using the dropdown button (`[▼]`)
4. Adjust clicking speed using the slider
5. Position your mouse where you want clicks to occur
6. Activate clicking using the keyboard shortcuts

## Keyboard Shortcuts

| Action | Shortcuts |
|--------|-----------|
| Activate auto-clicking | `]` or `+` |
| Deactivate auto-clicking | `[` or `-` |

## GUI Elements

### Collapsed View
```
  ┌───────┬────────────────────────────────────────────────────────┐
  │  MILK │ [settings]  |  [status] {OFF:[○]}  |    [ℕ]  [◀]  [x]  │
  └────────────────────────────────────────────────────────────────┘
```

### Expanded View
```
  ┌───────┬────────────────────────────────────────────────────────┐
  │ MILKy │  [settings]  |  [status] {OFF:[○]}  |   [ℕ]  [▼]  [x]  │
  ├───────┴────────────────────────────────────────────────────────│
  │1╠─  [cpm]           [status]  [▁▁▂▂▂▃▃▃▄▄▄▄▅▅▅▅▆▆▆]            │
  │2╠─                                                             │
  │3╠─  [click_speed]   [status]  [0 █░▒░█████████████]            │
  └────────────────────────────────────────────────────────────────┘
```

### Interface Controls

- **Expanded window Button**: `[▼]` 
- **Contracted window Button**: `[◀]`
- **Exit Button**: `[x]`
- **Log/Notification Button**: `[ℕ]`
- **Slider Click Speed Control**: `░▒░`
- **OFF Status Icon**: `○`
- **ON Status Icon**: `●`

## Troubleshooting

### Accessibility Permissions

MILKyclicks requires Accessibility permissions to monitor keyboard input and control the mouse system-wide.

1. If you see the warning: "Process is not trusted! Input event monitoring will not be possible", you need to grant permissions
2. Go to `System Preferences > Security & Privacy > Privacy > Accessibility`
3. Add MILKyclicks to the list of allowed applications
4. Ensure the checkbox next to MILKyclicks is selected
5. Restart the application

### Permission Helper

The included `permissions_helper.py` script can guide you through the permissions setup process:

```bash
python permissions_helper.py
```

### Common Issues

- **Application won't start**: Ensure Python 3.10+ is installed
- **No clicking occurs**: Check if Accessibility permissions are granted
- **Hotkeys don't work**: Ensure there are no keyboard shortcut conflicts with other applications
- **Interface doesn't appear**: Try running with elevated privileges

## Development

### Project Structure

```
MILKyclicks/
├── src/
│   ├── main.py          # Main application code
│   └── docs/            # Documentation
├── .venv/               # Virtual environment (created during installation)
├── requirements.txt     # Project dependencies
├── permissions_helper.py # Helper for setting up macOS permissions
└── README.md            # This file
```

### Dependencies

- **GUI**: PyQt6
- **Keyboard/Mouse Control**: pynput
- **Logging**: rich

### Type Checking

The codebase uses mypy for type checking:

```bash
mypy .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ASCII art design inspired by classic terminal interfaces
- Special thanks to the PyQt and pynput projects

---

*MILKyclicks © 2025 - Crafted with ♥*
