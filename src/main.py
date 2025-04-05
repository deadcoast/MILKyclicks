#!/usr/bin/env python3
import logging
import platform  # To check OS
import sys
import threading

from pynput import keyboard, mouse
from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase  # QIcon if needed later
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                             QSlider, QVBoxLayout, QWidget)
from rich.console import Console
from rich.logging import RichHandler

# --- Constants ---
APP_NAME = "MILKy Clicks"
VERSION = "1.1" # Incremented version

# ASCII Components (using unicode box drawing characters)
T_LEFT = "┌"
T_RIGHT = "┐"
B_LEFT = "└"
B_RIGHT = "┘"
H_LINE = "─"
V_LINE = "│"
T_SEP = "┬"
B_SEP = "┴"
L_SEP = "├"
R_SEP = "┤"

BTN_EXPAND = "[▼]"
BTN_COLLAPSE = "[◀]"
BTN_EXIT = "[x]"
BTN_LOG = "[ℕ]" # Unicode 'DOUBLE-STRUCK CAPITAL N'
BTN_SETTINGS = "[settings]" # Placeholder

STATUS_OFF_ICON = "○"
STATUS_ON_ICON = "●"
STATUS_TEXT_OFF = f"{{OFF:[{STATUS_OFF_ICON}]}}"
STATUS_TEXT_ON = f"{{ON:[{STATUS_ON_ICON}]}}"

# --- Font Selection (More robust) ---
DEFAULT_FONT = "Monaco" if platform.system() == "Darwin" else "Consolas" # Basic OS check
FALLBACK_FONT = "Monospace" # Generic fallback
FONT_SIZE = 12

MIN_CPM = 1
MAX_CPM = 3000 # Clicks Per Minute
DEFAULT_CPM = 600

NOTIFICATION_DURATION_MS = 2000 # 2 seconds

# --- Rich Logger Setup ---
# Ensure logs go somewhere useful, stderr is common for console apps
log_console = Console(stderr=True)
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=log_console, rich_tracebacks=True, show_path=False)] # Cleaner output
)
log = logging.getLogger("rich")

# --- Auto Clicker Thread (Unchanged) ---
class ClickerThread(QThread):
    click_signal = pyqtSignal() # To potentially signal each click if needed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse_controller = mouse.Controller()
        self._is_active = False
        self._lock = threading.Lock()
        self._interval = 1.0 # Default: 1 click per second (60 CPM)
        self._stop_event = threading.Event() # Using Event for clearer stopping

    def run(self):
        while not self._stop_event.is_set():
            with self._lock:
                active = self._is_active
                interval = self._interval

            if active:
                try:
                    self.mouse_controller.click(mouse.Button.left, 1)
                except Exception as e:
                    log.error(f"Clicking error: {e}", exc_info=False) # Log errors concisely
                # Use event wait for interruptible sleep
                self._stop_event.wait(interval)
            else:
                # Sleep longer when inactive using event wait
                self._stop_event.wait(0.1)

        log.info("Clicker thread finished.")


    def set_active(self, active):
        with self._lock:
            if active != self._is_active:
                log.info(f"Clicker state changed to: {'ON' if active else 'OFF'}")
            self._is_active = active

    def set_speed(self, cpm):
        with self._lock:
            cpm = max(cpm, MIN_CPM)
            cpm = min(cpm, MAX_CPM)
            # Prevent division by zero if MAX_CPM could be 0 (though unlikely here)
            self._interval = 60.0 / max(cpm, 1) # Ensure cpm is at least 1 for division
            log.debug(f"Click interval set to {self._interval:.4f}s ({cpm} CPM)")

    def stop(self):
        log.info("Requesting clicker thread stop...")
        self.set_active(False) # Ensure clicking stops
        self._stop_event.set() # Signal the loop to exit


# --- Keyboard Listener (Corrected Approach) ---
# This class now runs the listener in a thread and uses callbacks
# to trigger actions in the main GUI thread safely.
class KeyboardListener:
    # No pyqtSignals here!

    def __init__(self, activate_callback, deactivate_callback):
        """
        Initializes the listener.
        :param activate_callback: Function to call (thread-safely) on activation key press.
        :param deactivate_callback: Function to call (thread-safely) on deactivation key press.
        """
        self.listener = None
        self._thread = None
        self._activate_callback = activate_callback
        self._deactivate_callback = deactivate_callback
        self._stop_event = threading.Event() # To signal thread stop

    def _on_press(self, key):
        try:
            # Use key.char for simple characters, works for '+', '-', '[', ']'
            char = getattr(key, 'char', None)

            # Handle activation keys
            if char in (']', '+'):
                 if self._activate_callback:
                     # Call the provided callback function
                     self._activate_callback()

            # Handle deactivation keys
            elif char in ('[', '-'):
                if self._deactivate_callback:
                    # Call the provided callback function
                    self._deactivate_callback()

        except Exception as e:
            # Log errors happening within the listener thread
            log.error(f"Error in key press handler: {e}", exc_info=False)

    def _run_listener(self):
        """Target function for the listener thread."""
        try:
            self._keyboard_listener()
        except Exception as e:
            # Log errors specific to listener setup or runtime
            log.error(f"Keyboard listener failed: {e}", exc_info=True)
            log.error("Check Accessibility permissions (System Settings > Privacy & Security > Accessibility).")
        finally:
            self.listener = None # Clean up listener instance
            log.info("Keyboard listener thread finished.")

    def _keyboard_listener(self):
        # Create and run the listener within this thread's context
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start() # Start the listener
        log.info("Keyboard listener started successfully.")
        self._stop_event.wait() # Keep thread alive until stop is called
        log.info("Keyboard listener stopping...")
        self.listener.stop() # Stop the pynput listener
        self.listener.join() # Wait for pynput listener to exit fully


    def start(self):
        if self._thread is None or not self._thread.is_alive():
            log.info("Starting keyboard listener thread...")
            self._stop_event.clear() # Reset stop event
            # Run listener in a daemon thread so it exits with the main app if forced
            self._thread = threading.Thread(target=self._run_listener, daemon=True, name="KeyboardListenerThread")
            self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            log.info("Requesting keyboard listener thread stop...")
            self._stop_event.set() # Signal the thread's main loop to exit
            # No need to call self.listener.stop() here, it's handled in _run_listener exit
            self._thread.join(timeout=1.0) # Wait for the thread to exit
            if self._thread.is_alive():
                log.warning("Keyboard listener thread did not stop gracefully.")
        self._thread = None


# --- Main Application Window (Inherits QWidget, uses QObject features) ---
class MilkyClickerApp(QWidget):
    # --- Signals defined in the QObject context ---
    # Internal signals for safe GUI updates from any thread
    update_status_signal = pyqtSignal(bool)
    update_speed_display_signal = pyqtSignal(int)
    show_notification_signal = pyqtSignal(str)

    # Signals triggered by keyboard listener callbacks
    keyboard_activate_signal = pyqtSignal()
    keyboard_deactivate_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_active = False
        self._is_expanded = False
        self._current_cpm = DEFAULT_CPM
        self._drag_pos = QPoint() # For moving frameless window

        # --- Initialize Core Components ---
        self.clicker_thread = ClickerThread()

        # Instantiate KeyboardListener, passing thread-safe trigger methods
        # NOTE: Using lambda ensures `self` is captured correctly at call time
        # Pass self as the parent object instead of trying to invoke the signal directly
        self.keyboard_listener = KeyboardListener(
            activate_callback=lambda: self.keyboard_activate_signal.emit(),
            deactivate_callback=lambda: self.keyboard_deactivate_signal.emit()
        )

        # --- Connect Signals/Slots ---
        # Connect keyboard signals (now emitted safely from GUI thread) to slots
        self.keyboard_activate_signal.connect(self.activate_clicker)
        self.keyboard_deactivate_signal.connect(self.deactivate_clicker)

        # Connect internal signals for safe GUI updates
        self.update_status_signal.connect(self._update_status_label)
        self.update_speed_display_signal.connect(self._update_speed_display)
        self.show_notification_signal.connect(self._display_notification)

        # --- Setup Window ---
        self.setWindowTitle(APP_NAME)
        # Consider removing FramelessWindowHint initially if dragging/styling is complex
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True) # Enable transparency
        self.setStyleSheet("background-color: rgba(30, 30, 30, 0.85);") # Base background

        # --- Setup Font ---
        self.monospace_font = self._get_monospace_font()
        self.setFont(self.monospace_font) # Apply to whole widget

        # --- Create Widgets ---
        self._create_widgets()
        self._create_layout()
        self._apply_styling() # Apply custom styles

        # --- Set Initial State ---
        self.update_ui_state()
        self.clicker_thread.set_speed(self._current_cpm) # Set initial speed
        self.update_speed_display_signal.emit(self._current_cpm)

        # --- Start Threads ---
        self.clicker_thread.start()
        self.keyboard_listener.start() # Start listener after GUI setup

        # --- Notification Timer ---
        self.notification_timer = QTimer(self)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.notification_label.hide)

        log.info(f"{APP_NAME} v{VERSION} initialized. Waiting for activation...")
        log.info("Activate: ']' or '+', Deactivate: '[' or '-'")
        log.info(f"Using Font: {self.monospace_font.family()} {self.monospace_font.pointSize()}pt")


    def _get_monospace_font(self):
        """Attempts to load the preferred monospace font, falling back if needed."""
        # In PyQt6, we need to use the static methods of QFontDatabase
        available_families = QFontDatabase.families()
        
        if DEFAULT_FONT in available_families:
            log.debug(f"Using preferred font: {DEFAULT_FONT}")
            font = QFont(DEFAULT_FONT, FONT_SIZE)
        elif FALLBACK_FONT in available_families:
            log.warning(f"Font '{DEFAULT_FONT}' not found. Using fallback: {FALLBACK_FONT}")
            font = QFont(FALLBACK_FONT, FONT_SIZE)
        else:
            log.warning(f"Fonts '{DEFAULT_FONT}' and '{FALLBACK_FONT}' not found. Using system default monospace.")
            font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
            font.setPointSize(FONT_SIZE) # Ensure correct size

        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    def _create_widgets(self):
        # --- Top Bar Widgets ---
        # Use fixed-width spaces for more reliable ASCII alignment
        self.milky_label = QLabel() # Text set in update_ui_state
        self.settings_button = QPushButton(BTN_SETTINGS)
        self.status_separator_label = QLabel("|")
        self.status_label = QLabel() # Text set in update_ui_state
        self.status_separator_label2 = QLabel("|")
        self.log_button = QPushButton(BTN_LOG)
        self.expand_collapse_button = QPushButton() # Text set in update_ui_state
        self.exit_button = QPushButton(BTN_EXIT)

        # --- Expandable Area Widgets ---
        self.expandable_widget = QWidget() # Container

        # Line 1: CPM Display
        self.line1_prefix = QLabel("1╠─")
        self.cpm_label_static = QLabel("[cpm]")
        self.cpm_value_label = QLabel(f"{self._current_cpm: <4}") # Updated via signal
        self.cpm_status_placeholder = QLabel("[status]") # Placeholder
        self.cpm_graph_label = QLabel("[  ▂▂▂▃▃▃▄▄▄▄▅▅▅▅▆▆▆]") # Static visual

        # Line 2: Spacer
        self.line2_prefix = QLabel("2╠─")
        self.line2_spacer = QLabel(" " * 60) # Adjust as needed

        # Line 3: Click Speed Slider Representation
        self.line3_prefix = QLabel("3╠─")
        self.click_speed_label_static = QLabel("[click_speed]")
        self.click_speed_status_placeholder = QLabel("[status]") # Placeholder

        # ASCII Slider Visualisation & Controls
        self.speed_decrease_button = QPushButton("<")
        self.speed_ascii_label = QLabel() # Updated via signal
        self.speed_increase_button = QPushButton(">")

        # Hidden Real Slider for Control Logic
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(MIN_CPM, MAX_CPM)
        self.speed_slider.setValue(self._current_cpm)
        self.speed_slider.setVisible(False) # Keep hidden

        # --- Top/Bottom Border Labels (Simplified - adjust H_LINE counts) ---
        # Calculate width based on content later if possible, fixed for now
        # Width estimates to be implemented later
        # top_bar_content_width = 56 # Estimate width needed for top bar items
        # expandable_content_width = 64 # Estimate width for expanded items
        self.top_border_left = QLabel(f"  {T_LEFT}{H_LINE * 7}{T_SEP}")
        self.top_border_right = QLabel() # Text set later
        self.mid_separator_left = QLabel(f"  {L_SEP}{H_LINE * 7}{B_SEP}")
        self.mid_separator_right = QLabel() # Text set later
        self.bottom_border_left = QLabel(f"  {B_LEFT}{H_LINE * 7}") # For collapsed
        self.bottom_border_right = QLabel() # Text set later

        # Expanded bottom border (one single widget for simplicity)
        self.bottom_border_expanded = QLabel() # Text set later

        # --- Notification Label ---
        self.notification_label = QLabel("", self)
        self.notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_label.setVisible(False) # Hidden initially

        # --- Connect Button/Slider Signals ---
        self.expand_collapse_button.clicked.connect(self.toggle_expand)
        self.exit_button.clicked.connect(self.close_app)
        self.log_button.clicked.connect(self.show_log_info)
        self.settings_button.clicked.connect(self.show_settings_info)
        self.speed_slider.valueChanged.connect(self.update_speed) # Connect hidden slider
        self.speed_decrease_button.clicked.connect(lambda: self.speed_slider.setValue(self.speed_slider.value() - self.calculate_step(self.speed_slider.value())))
        self.speed_increase_button.clicked.connect(lambda: self.speed_slider.setValue(self.speed_slider.value() + self.calculate_step(self.speed_slider.value())))


    def calculate_step(self, current_value):
        """ Calculate dynamic step for +/- buttons """
        if current_value <= 10:
            return 1
        if current_value < 100:
            return 10
        elif current_value < 1000:
            return 50
        else:
            return 100

    def _create_layout(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Top Border ---
        top_border_layout = QHBoxLayout()
        top_border_layout.setSpacing(0)
        top_border_layout.addWidget(self.top_border_left)
        top_border_layout.addWidget(self.top_border_right, 1) # Allow stretch
        self.main_layout.addLayout(top_border_layout)

        # --- Top Bar Content ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(4) # Give a little space
        top_bar_layout.setContentsMargins(4, 0, 4, 0)
        top_bar_layout.addWidget(self.milky_label)
        top_bar_layout.addWidget(self.settings_button)
        top_bar_layout.addWidget(self.status_separator_label)
        top_bar_layout.addWidget(self.status_label)
        top_bar_layout.addWidget(self.status_separator_label2)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(self.log_button)
        top_bar_layout.addWidget(self.expand_collapse_button)
        top_bar_layout.addWidget(self.exit_button)
        self.main_layout.addLayout(top_bar_layout)

        # --- Mid Separator ---
        mid_separator_layout = QHBoxLayout()
        mid_separator_layout.setSpacing(0)
        mid_separator_layout.addWidget(self.mid_separator_left)
        mid_separator_layout.addWidget(self.mid_separator_right, 1) # Allow stretch
        self.main_layout.addLayout(mid_separator_layout)

        # --- Expandable Area Layout ---
        expandable_layout = QVBoxLayout(self.expandable_widget)
        expandable_layout.setContentsMargins(4, 2, 4, 2)
        expandable_layout.setSpacing(1)
        # Line 1
        line1_layout = QHBoxLayout()
        line1_layout.addWidget(self.line1_prefix)
        line1_layout.addWidget(self.cpm_label_static)
        line1_layout.addWidget(self.cpm_value_label)
        line1_layout.addSpacing(10)
        line1_layout.addWidget(self.cpm_status_placeholder)
        line1_layout.addSpacing(10)
        line1_layout.addWidget(self.cpm_graph_label)
        line1_layout.addStretch(1)
        expandable_layout.addLayout(line1_layout)
        # Line 2
        line2_layout = QHBoxLayout()
        line2_layout.addWidget(self.line2_prefix)
        line2_layout.addWidget(self.line2_spacer)
        line2_layout.addStretch(1)
        expandable_layout.addLayout(line2_layout)
        # Line 3
        line3_layout = QHBoxLayout()
        line3_layout.addWidget(self.line3_prefix)
        line3_layout.addWidget(self.click_speed_label_static)
        line3_layout.addSpacing(10)
        line3_layout.addWidget(self.click_speed_status_placeholder)
        line3_layout.addSpacing(10)
        line3_layout.addWidget(self.speed_decrease_button)
        line3_layout.addWidget(self.speed_ascii_label)
        line3_layout.addWidget(self.speed_increase_button)
        line3_layout.addStretch(1)
        expandable_layout.addLayout(line3_layout)
        # Add expandable widget to main layout
        self.main_layout.addWidget(self.expandable_widget)

        # --- Bottom Border ---
        # Collapsed border layout
        self.bottom_border_layout_collapsed = QHBoxLayout()
        self.bottom_border_layout_collapsed.setSpacing(0)
        self.bottom_border_layout_collapsed.addWidget(self.bottom_border_left)
        self.bottom_border_layout_collapsed.addWidget(self.bottom_border_right, 1) # Stretch
        self.main_layout.addLayout(self.bottom_border_layout_collapsed)

        # Expanded border widget (simpler)
        self.main_layout.addWidget(self.bottom_border_expanded)

        self.setLayout(self.main_layout)
        self.expandable_widget.setVisible(False) # Start hidden
        self.bottom_border_expanded.setVisible(False) # Start hidden


    def _apply_styling(self):
        # Base styles using f-strings for font family/size
        font_family = self.monospace_font.family()
        font_size_pt = self.monospace_font.pointSize()

        base_button_style = f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                color: white;
                padding: 0px 2px; /* Add small horizontal padding */
                margin: 0px;
                font-family: '{font_family}';
                font-size: {font_size_pt}pt;
                text-align: center;
                min-height: 14px; /* Ensure minimum height */
            }}
            QPushButton:hover {{ color: #ccc; }}
            QPushButton:pressed {{ color: #999; }}
        """
        base_label_style = f"""
            QLabel {{
                background-color: transparent;
                color: white;
                padding: 0px;
                margin: 0px;
                font-family: '{font_family}';
                font-size: {font_size_pt}pt;
                min-height: 14px; /* Ensure minimum height */
            }}
        """
        # Main widget style sets background and applies base styles
        self.setStyleSheet(f"""
            QWidget {{ background-color: rgba(30, 30, 30, 0.85); }}
            {base_button_style}
            {base_label_style}
        """)

        # Specific widget adjustments
        self.milky_label.setStyleSheet("color: #FFD700;") # Gold
        self.exit_button.setStyleSheet(f"{base_button_style} color: red;")
        self.exit_button.setToolTip("Exit Application")
        self.expand_collapse_button.setToolTip("Expand/Collapse Details")
        self.log_button.setToolTip("Show Log Info (in console)")
        self.settings_button.setToolTip("Settings (Not Implemented)")
        self.speed_decrease_button.setToolTip("Decrease Click Speed")
        self.speed_increase_button.setToolTip("Increase Click Speed")


        # Fixed widths based on text for critical alignment buttons
        fm = self.fontMetrics()
        self.expand_collapse_button.setFixedWidth(fm.horizontalAdvance(BTN_COLLAPSE + " ")) # Use widest text
        self.exit_button.setFixedWidth(fm.horizontalAdvance(BTN_EXIT + " "))
        self.log_button.setFixedWidth(fm.horizontalAdvance(BTN_LOG + " "))
        self.speed_decrease_button.setFixedWidth(fm.horizontalAdvance("< "))
        self.speed_increase_button.setFixedWidth(fm.horizontalAdvance("> "))

        # Notification Label Styling
        self.notification_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 4px 8px;
                font-family: '{font_family}';
                font-size: {font_size_pt - 1}pt; /* Slightly smaller */
            }}
        """)

    def _update_border_widths(self):
         # Rough calculation based on estimated content width
        # This is hard to get perfect without complex geometry calculations
        top_width = 56 # Matches original ASCII approximately
        expanded_width = 64

        # Set text for the right parts of borders based on state
        hr_count_top = top_width
        hr_count_mid = top_width
        hr_count_bottom_collapsed = top_width

        self.top_border_right.setText(f"{H_LINE * hr_count_top}{T_RIGHT}")
        self.mid_separator_right.setText(f"{H_LINE * hr_count_mid}{V_LINE}")
        self.bottom_border_right.setText(f"{H_LINE * hr_count_bottom_collapsed}{B_RIGHT}")

        # Set text for the single expanded bottom border
        self.bottom_border_expanded.setText(f"  {B_LEFT}{H_LINE * expanded_width}{B_RIGHT}")


    def update_ui_state(self):
        """Updates the UI based on the current state (_is_expanded, _is_active)."""
        # Update Expand/Collapse Button and Visibility
        self.expand_collapse_button.setText(BTN_COLLAPSE if self._is_expanded else BTN_EXPAND)
        self.expandable_widget.setVisible(self._is_expanded)

        # Update Top Bar Text
        self.milky_label.setText(f"{V_LINE} MILKy {V_LINE}" if self._is_expanded else f"{V_LINE}  MILK {V_LINE}")

        # Update Borders visibility
        for i in range(self.bottom_border_layout_collapsed.count()):
             widget = self.bottom_border_layout_collapsed.itemAt(i).widget()
             if widget:
                 widget.setVisible(not self._is_expanded)
        self.bottom_border_expanded.setVisible(self._is_expanded)

        # Ensure status label is correct
        self._update_status_label(self._is_active)

        # Update border text content (lengths)
        self._update_border_widths()

        # Adjust window size smoothly
        # self.adjustSize() # This can be jerky with show/hide
        # Fixed size might be better if layout is stable
        self.setFixedSize(self.main_layout.sizeHint()) # Try fixing size based on hint


    def toggle_expand(self):
        self._is_expanded = not self._is_expanded
        log.debug(f"Window {'expanded' if self._is_expanded else 'collapsed'}")
        # Update state *before* showing/hiding for smoother size calculation
        self.update_ui_state()


    def update_speed(self, value):
        self._current_cpm = value
        self.clicker_thread.set_speed(self._current_cpm)
        # Emit signal to safely update GUI elements related to speed
        self.update_speed_display_signal.emit(self._current_cpm)

    def _update_speed_display(self, cpm):
        """ Updates the visual representation of the speed. Thread-safe."""
        self.cpm_value_label.setText(f"{cpm: <4}") # Update numeric CPM

        # --- Update ASCII Slider Visual ---
        slider_char_width = 15 # Width of the '█' bar part in the ASCII '[0 █░▒░███]'
        handle = "░▒░"
        handle_len = len(handle)
        track_len = slider_char_width - handle_len # Available space for actual track chars

        # Prevent division by zero or invalid range
        range_cpm = max(1, MAX_CPM - MIN_CPM)
        norm_val = (cpm - MIN_CPM) / range_cpm

        # Calculate number of '█' before and after handle
        left_chars = int(norm_val * track_len)
        right_chars = track_len - left_chars

        # Build the visual string
        visual_track = ('█' * left_chars) + handle + ('█' * right_chars)
        # Pad if needed (e.g., if handle_len makes track_len negative, though unlikely)
        visual_track = visual_track.ljust(slider_char_width, ' ')[:slider_char_width]

        final_ascii = f"[0 {visual_track}]" # Construct the final string
        self.speed_ascii_label.setText(final_ascii)


    def activate_clicker(self):
        if not self._is_active:
            self._active_status_icon(True)
            self.show_notification_signal.emit(f"Activated {STATUS_ON_ICON} ({self._current_cpm} CPM)")

    def deactivate_clicker(self):
        if self._is_active:
            self._active_status_icon(False)
            self.show_notification_signal.emit(f"Deactivated {STATUS_OFF_ICON}")

    def _active_status_icon(self, arg0):
        self._is_active = arg0
        self.clicker_thread.set_active(arg0)
        self.update_status_signal.emit(arg0)

    def _update_status_label(self, is_active):
        """Updates the status label text and icon. Thread-safe."""
        status_text = STATUS_TEXT_ON if is_active else STATUS_TEXT_OFF
        self.status_label.setText(f"[status] {status_text}")

    def _display_notification(self, message):
        """Shows a temporary notification label. Thread-safe."""
        log.info(message) # Log to console via rich
        self.notification_label.setText(message)
        self.notification_label.adjustSize() # Fit content

        # Position it centered, slightly below the top bar
        # Get heights after text is set
        top_border_h = self.top_border_left.sizeHint().height()
        top_bar_h = self.milky_label.sizeHint().height() # Approx height of top bar content row
        y_offset = top_border_h + top_bar_h + 5 # Position below top bar

        x = (self.width() - self.notification_label.width()) // 2
        # Ensure it doesn't go off-screen if window is tiny
        x = max(5, x)
        y = min(y_offset, self.height() - self.notification_label.height() - 5) # Don't go below bottom

        self.notification_label.move(x, y)
        self.notification_label.raise_() # Bring to front
        self.notification_label.setVisible(True)
        self.notification_timer.start(NOTIFICATION_DURATION_MS)


    def show_log_info(self):
        self.show_notification_signal.emit("[INFO] Logs are shown in the terminal/console.")

    def show_settings_info(self):
        self.show_notification_signal.emit("[INFO] Settings not yet implemented.")

    def close_app(self):
        log.info("Shutdown sequence initiated...")
        # Stop threads gracefully
        self.keyboard_listener.stop()
        self.clicker_thread.stop()
        # Wait briefly for threads (optional, helps ensure cleanup)
        # self.clicker_thread.wait(500) # Wait up to 500ms for clicker thread
        log.info("Exiting application.")
        self.close() # Close the GUI window

    # --- Window Dragging for Frameless Window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Only allow dragging from the top bar area (approximate)
            draggable_height = self.top_border_left.height() + self.milky_label.height()
            if event.position().y() <= draggable_height:
                 self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                 event.accept()
            else:
                event.ignore() # Don't start drag if clicked below top bar


    def mouseMoveEvent(self, event):
        # Check if left button is pressed (drag is active)
        # Use buttons() instead of button() for move events
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
         if event.button() == Qt.MouseButton.LeftButton:
              self._drag_pos = QPoint() # Reset drag position
              event.accept()


    # --- Ensure threads are stopped on close ---
    def closeEvent(self, event):
        # This event is triggered by window close button, self.close(), etc.
        self.close_app() # Initiate the full shutdown sequence
        event.accept() # Accept the close event


# --- Main Execution ---
if __name__ == "__main__":
    # Add basic check for Accessibility permissions on Mac
    if platform.system() == "Darwin":
        # NOTE: This is a *very basic* check. A real app might use pyobjc
        # to try and check permissions more reliably, but that adds complexity.
        # We rely on the listener logging an error if it fails.
        pass # No simple way to check programmatically without extra libs

    app = QApplication(sys.argv)
    try:
        milky_clicker = MilkyClickerApp()
        milky_clicker.show()
        exit_code = app.exec()
        log.info(f"Application finished with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception:
        # Use log.exception to include the traceback automatically
        log.exception("Critical error during application startup or execution.")
        sys.exit(1) # Exit with error code        exit_code = app.exec()
        log.info(f"Application finished with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception:
        # Use log.exception to include the traceback automatically
        log.exception("Critical error during application startup or execution.")
        sys.exit(1) # Exit with error code