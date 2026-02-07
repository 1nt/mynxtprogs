#!/usr/bin/env python3
import time
import os
import sys
import nxt.locator
from nxt.backend.devfile import DevFileSock
from nxt_roboeyes import NxtDisplay, RoboEyes, SCREEN_W, SCREEN_H, HAPPY, ANGRY, TIRED, DEFAULT

def main():
    brick = None
    # Try Bluetooth first if device exists
    if os.path.exists('/dev/rfcomm0'):
        try:
            print("Connecting via /dev/rfcomm0...")
            brick = DevFileSock('/dev/rfcomm0').connect()
        except Exception as e:
            print(f"Bluetooth connection failed: {e}")

    # Fallback to USB/Locator
    if not brick:
        print("Searching for NXT via USB/Bluetooth locator...")
        try:
            with nxt.locator.find() as b:
                brick = b
        except nxt.locator.BrickNotFoundError:
            print("No NXT brick found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error locating brick: {e}")
            sys.exit(1)

    if not brick:
        print("Could not connect to NXT.")
        sys.exit(1)

    print("Connected to NXT.")
    
    # Initialize Display Wrapper
    try:
        disp = NxtDisplay(brick)
    except RuntimeError as e:
        print(f"Display Init Error: {e}")
        sys.exit(1)

    # Callback for screen update
    def show_cb(re):
        re.fb.update()

    # Initialize RoboEyes
    # reduced framerate to match NXT slow bus speed
    eyes = RoboEyes(disp, SCREEN_W, SCREEN_H, frame_rate=10, on_show=show_cb)
    
    eyes.set_auto_blinker(True, 2, 1)
    eyes.set_idle_mode(True, 3, 2)

    print("Starting Animation Loop. Press Ctrl+C to stop.")
    
    start_time = time.time()
    mode = 0
    modes = [DEFAULT, HAPPY, ANGRY, TIRED]
    mode_names = ["Default", "Happy", "Angry", "Tired"]

    try:
        while True:
            eyes.update()
            
            # Switch mood every 5 seconds
            if time.time() - start_time > 10:
                mode = (mode + 1) % len(modes)
                eyes.mood = modes[mode]
                print(f"Switching mood to: {mode_names[mode]}")
                start_time = time.time()
                
                # Trigger specific animations on switch
                if modes[mode] == HAPPY:
                    eyes.laugh()
                elif modes[mode] == ANGRY:
                    eyes.confuse()
            
            # Small sleep to prevent 100% CPU usage on host, 
            # though eyes.update() limits framerate internally, 
            # the loop is tight.
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping...")
        disp.clear()
        disp.update()

if __name__ == "__main__":
    main()
