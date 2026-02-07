# NXT Project Programs

This document describes the python programs available in this directory for controlling the LEGO NXT brick.

## Animation & Display

### `blink_eyes_auto.py`
**Universal Blinking Eyes**
- **Description:** Displays a pair of eyes on the NXT screen that blink periodically.
- **Key Features:**
  - Automatically detects the best way to draw on the screen: uses `brick.display` if available (high-level), otherwise falls back to `write_io_map` (low-level direct memory access).
  - Robust connection handling (supports `DevFileSock` for RFCOMM and `nxt.locator`).

### `blink_eyes_nxt.py`
**Blinking Eyes with Tongue Animation**
- **Description:** An advanced version of the blinking eyes program.
- **Key Features:**
  - Animates the eyes blinking.
  - Adds a "tongue sticking out" animation sequence.
  - Uses the same robust display adapter pattern as `blink_eyes_auto.py`.

### `running_man.py`
**Running Man Animation**
- **Description:** Displays a stick figure animation of a man running across the screen.
- **Key Features:**
  - Implements a custom low-level graphics engine using `write_io_map`.
  - Includes primitives for drawing filled circles and lines.
  - Tries to connect via USB first, then falls back to a specific Bluetooth MAC address.

## Behaviors

### `disp.py`
**Rebellious Robot (Behavior Test)**
- **Description:** A script that attempts to simulate a "rebellious" robot.
- **Key Features:**
  - Cycles between a "wide-eyed" look and a "teasing" behavior (sounds + motor vibration).
  - Attempts to use new firmware display methods, with a fallback to older methods.

### `test.py`
**Robot Hooligan**
- **Description:** A dedicated "hooligan" robot behavior script.
- **Key Features:**
  - manually draws "big eyes" by writing bytes directly to the display memory map.
  - Alternates between a calm "staring" state and a "teasing" state with sound effects and a graphical "tongue".

## Utilities & Testing

### `blu.py`
**Bluetooth Connection Check**
- **Description:** A simple utility to verify Bluetooth connectivity.
- **Key Features:**
  - Connects to `/dev/rfcomm0` (or via locator).
  - Prints brick name and battery level.
  - Plays a test tone.

### `find.py`
**DevFile Connection Test**
- **Description:** Minimal test for direct device file connection.
- **Key Features:**
  - Specifically targets `/dev/rfcomm0` using `DevFileSock`.
  - Useful for debugging low-level communication issues.

### `test_sound.py`
**Sound Subsystem Test**
- **Description:** Verifies the NXT speaker functionality.
- **Key Features:**
  - Tries automatic discovery, then falls back to a hardcoded Bluetooth MAC address.
  - Plays a sequence of tones (1000Hz and 500Hz) to confirm audio output.
