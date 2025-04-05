# Framework


MILKyclicks is an advanced Auto clicker with a GUI in python for macosx. The gui should be in the shape of a minimal bar with a dropdown menu. The dropdown menu will house a slider for the speed of the auto clicker. The slider will be adjusted with an ASCII button.
When the clicker is turned on or off, there should be a short notification pop up menu from the bar notifying the user the status. A logger will manager this for the gui button

## Requirements

OS: MAC-OSX
LANGUAGE: PYTHON

### PYTHON PACKAGES
GUI: PYQT
LOGGER: Rich

## ASCII HYBRID GUI

The ASCII must be EXACT. NO STREAMLINING. CREATE TEXT ELEMENTS FOR THE ASCII IN THE GUI AS STYLING. IF YOU HAVE A MORE OPTIMIZED WAY TO IMPLEMENT IT, PLEASE DO THAT.
### FULL WINDOW VIEW
```
  ┌───────┬────────────────────────────────────────────────────────┐
  │ MILKy │  [settings]  |  [status] {OFF:[○]}  |   [ℕ]  [▼]  [x]  │
  ├───────┴────────────────────────────────────────────────────────│
  │1╠─  [cpm]           [status]  [▁▁▂▂▂▃▃▃▄▄▄▄▅▅▅▅▆▆▆]            │
  │2╠─                                                             │
  │3╠─  [click_speed]   [status]  [0 █░▒░█████████████]            │
  └────────────────────────────────────────────────────────────────┘
```

### COLLAPSED VIEW
```
  ┌───────┬────────────────────────────────────────────────────────┐
  │  MILK │ [settings]  |  [status] {OFF:[○]}  |    [ℕ]  [◀]  [x]  │
  └────────────────────────────────────────────────────────────────┘
```

## BUTTONS
Expanded window Button: `[▼]` 
Contracted window Button: `[◀]`
Exit Button: `[x]`
Log(Notification) Button: `[ℕ]`
Slider Click Speed Control Button: `░▒░`
OFF STAUTS ICON: `○`
ON STATUS ICON: `●` 
## KEYBINDINGS:
activate_autoclicker: `]` and `+`
deactivate_autoclicker: `[` and `-`

**Note:**

1.  **Permissions (macOS):** To monitor keyboard input and control the mouse system-wide, you'll need to grant Accessibility permissions to your terminal or the application bundle if you create one. Go to `System Preferences > Security & Privacy > Privacy > Accessibility` and add your Terminal application or Python interpreter.
2.  **`rich` for GUI Notifications:** `rich` is primarily a *terminal* formatting library. Using it for GUI pop-up notifications isn't its intended purpose. We'll use `rich` for *console logging* as requested and implement the GUI notification using a temporary PyQt label.
3.  **ASCII Slider:** Implementing a functional slider *exactly* matching the ASCII `[0 █░▒░█████████████]` is tricky. We'll represent it visually with `QLabel`s and use separate buttons or underlying logic (like a hidden `QSlider`) to control the actual speed. The `░▒░` will be part of the visual display, updated based on the speed. We'll add clickable elements (like `<` and `>`) for control.
4.  **`pynput` for Clicking & Keyboard:** `pynput` will handle the clicking and keyboard listening.
5.  **`rich` for Logging:** `rich` will be used for console logging.
6.  **Installation:** You need to install the required libraries:
    ```bash
    pip install PyQt6 pynput rich
    ```

**Explanation:**

1.  **Libraries:** Imports `PyQt6`, `sys`, `time`, `threading`, `pynput`, `rich`, and `logging`.
2.  **Constants & ASCII:** Defines constants for names, versions, and the ASCII characters for easier use.
3.  **Logger:** Sets up `rich` for pretty console logging.
4.  **`ClickerThread` (QThread):**
    * Handles the actual clicking in a separate thread to avoid freezing the GUI.
    * Uses `pynput.mouse.Controller` to perform clicks.
    * `_is_active` flag controls clicking, managed via `set_active`.
    * `_interval` stores the time between clicks, calculated from CPM (`set_speed`).
    * Uses `threading.Lock` for safe access to shared variables (`_is_active`, `_interval`) from different threads.
    * Includes `requestInterruption()` and checks `isInterruptionRequested()` for graceful shutdown.
5.  **`KeyboardListener` (threading.Thread):**
    * Uses `pynput.keyboard.Listener` to capture global key presses. This *must* run in a standard Python `threading.Thread`, not `QThread`, due to how `pynput` integrates with event loops.
    * `_on_press` checks for the specified activation/deactivation keys.
    * Crucially, it uses `QMetaObject.invokeMethod(self.activate_signal, "emit")` (and similarly for deactivate) to *safely* emit a PyQt signal from the listener thread back to the main GUI thread. Directly modifying GUI elements or calling GUI methods from other threads is unsafe in PyQt.
6.  **`MilkyClickerApp` (QWidget):**
    * **Initialization (`__init__`)**:
        * Sets up state variables (`_is_active`, `_is_expanded`, `_current_cpm`).
        * Initializes `ClickerThread` and `KeyboardListener`.
        * Connects signals from the keyboard listener to `activate_clicker`/`deactivate_clicker` slots.
        * Sets up internal signals (`update_status_signal`, etc.) for thread-safe GUI updates.
        * Configures the window (frameless, always on top, tool window style).
        * Sets a monospace font (`Monaco` preferred for macOS).
        * Calls helper methods to create widgets, layout, and styles.
        * Starts the clicker and keyboard listener threads.
        * Initializes a `QTimer` for hiding notifications.
    * **`_create_widgets`**: Instantiates all `QLabel`s and `QPushButton`s needed for the ASCII interface. Includes the *hidden* `QSlider` for speed control logic.
    * **`_create_layout`**: Uses nested `QHBoxLayout` and `QVBoxLayout` to arrange the widgets. `addStretch` is used to push elements like buttons to the right. Manages the visibility of the `expandable_widget`. The border layout is tricky and might need refinement for pixel-perfect ASCII alignment.
    * **`_apply_styling`**: Uses CSS-like `setStyleSheet` to remove button borders, set colors (semi-transparent background, white text), and apply the monospace font. Specific styles are added for the "MILKy" label and exit button.
    * **`update_ui_state`**: Central method to refresh the UI based on whether the window is expanded or collapsed (updates button text, widget visibility, window size).
    * **`toggle_expand`**: Slot connected to the `[▼]` / `[◀]` button.
    * **`update_speed`**: Slot connected to the *hidden* `QSlider`. Updates `_current_cpm`, tells the `ClickerThread` the new speed, and triggers `_update_speed_display` via a signal.
    * **`_update_speed_display`**: Updates the `cpm_value_label` and reconstructs the `speed_ascii_label` string to visually represent the slider's position. **Thread-safe**.
    * **`activate_clicker` / `deactivate_clicker`**: Slots connected to signals from the `KeyboardListener`. They update the internal state, tell the `ClickerThread` to start/stop, and trigger status label and notification updates via signals.
    * **`_update_status_label`**: Updates the text of the main status label. **Thread-safe**.
    * **`_display_notification`**: Shows the `notification_label` with a message, positions it, logs to the console, and starts the timer to hide it. **Thread-safe**.
    * **`close_app`**: Stops threads cleanly before closing.
    * **`mousePressEvent`, `mouseMoveEvent`**: Implement basic dragging for the frameless window.
    * **`closeEvent`**: Overridden to ensure `close_app` is called when the window is closed via any means.
7.  **Main Execution (`if __name__ == "__main__":`)**: Creates the `QApplication`, instantiates and shows the `MilkyClickerApp`, and starts the event loop. Includes basic error handling.

Remember to grant Accessibility permissions on your Mac!