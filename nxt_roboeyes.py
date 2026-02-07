#!/usr/bin/env python3
import time
import math
import random

# --- NXT Display Driver ---
SCREEN_W = 100
SCREEN_H = 64
BUFFER_SIZE = 800  
MOD_DISPLAY = 0xA0001
DISPLAY_OFFSET = 119 

class NxtDisplay:
    def __init__(self, brick):
        self.brick = brick
        # Use direct memory map if available (faster)
        self.use_iomap = hasattr(brick, 'write_io_map')
        self.buf = bytearray(BUFFER_SIZE)

    def clear(self):
        """Clear the buffer (fill with 0)"""
        for i in range(BUFFER_SIZE):
            self.buf[i] = 0

    def fill(self, color):
        val = 0xFF if color else 0x00
        for i in range(BUFFER_SIZE):
            self.buf[i] = val

    def set_pixel(self, x, y, color):
        if not (0 <= x < SCREEN_W and 0 <= y < SCREEN_H):
            return
        page = y // 8
        idx = page * SCREEN_W + x
        mask = 1 << (y % 8)
        
        if color:
            self.buf[idx] |= mask
        else:
            self.buf[idx] &= (~mask & 0xFF)

    def update(self):
        if self.use_iomap:
            try:
                # 20 chunks of 40 bytes
                for i in range(20):
                    start = i * 40
                    chunk = self.buf[start:start + 40]
                    self.brick.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + start, bytes(chunk))
            except Exception as e:
                pass # Suppress errors for robustness during animation
        else:
            # Fallback to high-level display (very slow, not recommended for animation)
            pass

    # --- Drawing Primitives (FBUtil equivalents) ---

    def fill_rect(self, x, y, w, h, color):
        # Clipping
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x + w > SCREEN_W: w = SCREEN_W - x
        if y + h > SCREEN_H: h = SCREEN_H - y
        
        if w <= 0 or h <= 0: return

        for py in range(y, y + h):
            for px in range(x, x + w):
                self.set_pixel(px, py, color)

    def fill_rrect(self, x, y, w, h, r, color):
        # Naive implementation: fill rects and circles
        # Center rect
        self.fill_rect(x, y + r, w, h - 2 * r, color)
        # Top/Bottom rects
        self.fill_rect(x + r, y, w - 2 * r, r, color)
        self.fill_rect(x + r, y + h - r, w - 2 * r, r, color)
        # Corners
        self._fill_circle_helper(x + r, y + r, r, 1, color) # Top-Left
        self._fill_circle_helper(x + w - r - 1, y + r, r, 2, color) # Top-Right
        self._fill_circle_helper(x + w - r - 1, y + h - r - 1, r, 3, color) # Bottom-Right
        self._fill_circle_helper(x + r, y + h - r - 1, r, 4, color) # Bottom-Left

    def _fill_circle_helper(self, cx, cy, r, corner, color):
        # corner: 1=TL, 2=TR, 3=BR, 4=BL
        # Uses midpoint circle algorithm logic but for filled quadrants
        
        # A simple way for small r is just checking distance for pixels in the corner box
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx*dx + dy*dy <= r*r:
                    # Check quadrant
                    if corner == 1 and dx <= 0 and dy <= 0: self.set_pixel(cx+dx, cy+dy, color)
                    if corner == 2 and dx >= 0 and dy <= 0: self.set_pixel(cx+dx, cy+dy, color)
                    if corner == 3 and dx >= 0 and dy >= 0: self.set_pixel(cx+dx, cy+dy, color)
                    if corner == 4 and dx <= 0 and dy >= 0: self.set_pixel(cx+dx, cy+dy, color)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Sort coordinates by Y
        if y0 > y1: x0, y0, x1, y1 = x1, y1, x0, y0
        if y0 > y2: x0, y0, x2, y2 = x2, y2, x0, y0
        if y1 > y2: x1, y1, x2, y2 = x2, y2, x1, y1

        # Compute dx/dy
        total_height = y2 - y0
        if total_height == 0: return # Flat triangle

        for i in range(total_height):
            y = y0 + i
            if y >= SCREEN_H: break
            if y < 0: continue
            
            second_half = i > y1 - y0 or y1 == y0
            segment_height = y2 - y1 if second_half else y1 - y0
            
            if segment_height == 0: continue # Degenerate segment

            alpha = i / total_height
            beta  = (i - (y1 - y0) if second_half else i) / segment_height
            
            ax = int(x0 + (x2 - x0) * alpha)
            bx = int(x1 + (x2 - x1) * beta) if second_half else int(x0 + (x1 - x0) * beta)

            if ax > bx: ax, bx = bx, ax
            
            for j in range(ax, bx + 1):
                self.set_pixel(j, y, color)


# --- Ported RoboEyes Library ---

# Colors
BGCOLOR   = 0 
FGCOLOR   = 1 

# Moods
DEFAULT = 0
TIRED   = 1
ANGRY   = 2
HAPPY   = 3
FROZEN  = 4
SCARY   = 5
CURIOUS = 6

# Directions
N  = 1 
NE = 2 
E  = 3 
SE = 4 
S  = 5 
SW = 6 
W  = 7 
NW = 8 

class StepData:
    def __init__( self, owner_seq, ms_timing, _lambda ):
        self.done = False
        self.ms_timing = ms_timing
        self._lambda = _lambda
        self.owner_seq = owner_seq 

    def update( self, ticks_ms ):
        if self.done: return 
        if (ticks_ms - self.owner_seq._start) < self.ms_timing: return
        self._lambda( self.owner_seq.owner ) 
        self.done = True

class Sequence( list ):
    def __init__( self, owner, name ):
        super().__init__()
        self.owner = owner
        self.name = name
        self._start = None

    def step( self, ms_timing, _lambda ):
        _r = StepData( self, ms_timing, _lambda )
        self.append( _r )

    def start( self ):
        self._start = int(time.time() * 1000)

    def reset( self ):
        self._start = None
        for _step in self:
            _step.done = False

    @property
    def done( self ):
        if self._start is None: return True
        return all([ _step.done for _step in self ])

    def update( self, ticks_ms ):
        if self._start is None: return
        for _step in self:
            if not _step.done: _step.update(ticks_ms)

class Sequences( list ):
    def __init__( self, owner ):
        super().__init__()
        self.owner = owner 

    def add( self, name  ):
        _r = Sequence( self.owner, name ) 
        self.append( _r )
        return _r

    @property
    def done( self ):
        return all( [ _seq.done for _seq in self ] )

    def update( self ):
        _ms_ticks = int(time.time() * 1000)
        for _seq in self: _seq.update( _ms_ticks )


class RoboEyes:
    def __init__(self, fb, width, height, frame_rate=20, on_show=None, bgcolor=BGCOLOR, fgcolor=FGCOLOR ):
        self.fb = fb # NxtDisplay instance
        self.on_show = on_show
        self.screenWidth = width 
        self.screenHeight = height 
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor

        self.sequences = Sequences( self )

        self.fpsTimer = 0 
        self._position = 0 
        
        self._mood = DEFAULT 
        self.tired = False
        self.angry = False
        self.happy = False

        self._curious = False   
        self._cyclops = False   
        self.eyeL_open = False 
        self.eyeR_open = False 

        # Geometry
        self.spaceBetweenDefault = 10

        # Left Eye
        self.eyeLwidthDefault = 36
        self.eyeLheightDefault = 36
        self.eyeLwidthCurrent = self.eyeLwidthDefault
        self.eyeLheightCurrent = 1 
        self.eyeLwidthNext = self.eyeLwidthDefault
        self.eyeLheightNext = self.eyeLheightDefault
        self.eyeLheightOffset = 0
        self.eyeLborderRadiusDefault = 8
        self.eyeLborderRadiusCurrent = self.eyeLborderRadiusDefault
        self.eyeLborderRadiusNext = self.eyeLborderRadiusDefault

        # Right Eye
        self.eyeRwidthDefault = self.eyeLwidthDefault
        self.eyeRheightDefault = self.eyeLheightDefault
        self.eyeRwidthCurrent = self.eyeRwidthDefault
        self.eyeRheightCurrent = 1 
        self.eyeRwidthNext = self.eyeRwidthDefault
        self.eyeRheightNext = self.eyeRheightDefault
        self.eyeRheightOffset = 0
        self.eyeRborderRadiusDefault = 8
        self.eyeRborderRadiusCurrent = self.eyeRborderRadiusDefault
        self.eyeRborderRadiusNext = self.eyeRborderRadiusDefault

        # Coords
        self.eyeLxDefault = int( ((self.screenWidth)-(self.eyeLwidthDefault+self.spaceBetweenDefault+self.eyeRwidthDefault))/2 )
        self.eyeLyDefault = int( (self.screenHeight-self.eyeLheightDefault)/2 )
        self.eyeLx = self.eyeLxDefault
        self.eyeLy = self.eyeLyDefault
        self.eyeLxNext = self.eyeLx
        self.eyeLyNext = self.eyeLy

        self.eyeRxDefault = self.eyeLx+self.eyeLwidthCurrent+self.spaceBetweenDefault
        self.eyeRyDefault = self.eyeLy
        self.eyeRx = self.eyeRxDefault
        self.eyeRy = self.eyeRyDefault
        self.eyeRxNext = self.eyeRx
        self.eyeRyNext = self.eyeRy

        # Eyelids
        self.eyelidsHeightMax = int(self.eyeLheightDefault/2) 
        self.eyelidsTiredHeight = 0
        self.eyelidsTiredHeightNext = self.eyelidsTiredHeight
        self.eyelidsAngryHeight = 0
        self.eyelidsAngryHeightNext = self.eyelidsAngryHeight
        self.eyelidsHappyBottomOffsetMax = int(self.eyeLheightDefault/2)+3
        self.eyelidsHappyBottomOffset = 0
        self.eyelidsHappyBottomOffsetNext = 0
        
        self.spaceBetweenCurrent = self.spaceBetweenDefault
        self.spaceBetweenNext = 10

        # Animations
        self.hFlicker = False
        self.hFlickerAlternate = False
        self.hFlickerAmplitude = 2
        self.vFlicker = False
        self.vFlickerAlternate = False
        self.vFlickerAmplitude = 10

        self.autoblinker = False 
        self.blinkInterval = 1 
        self.blinkIntervalVariation = 4 
        self.blinktimer = 0 

        self.idle = False
        self.idleInterval = 1 
        self.idleIntervalVariation = 3 
        self.idleAnimationTimer = 0 

        self._confused = False
        self.confusedAnimationTimer = 0
        self.confusedAnimationDuration = 500
        self.confusedToggle = True

        self._laugh = False
        self.laughAnimationTimer = 0
        self.laughAnimationDuration = 500
        self.laughToggle = True

        self.fb.clear()
        if self.on_show: self.on_show(self)
        self.eyeLheightCurrent = 1 
        self.eyeRheightCurrent = 1 
        self.set_framerate(frame_rate)

    def set_framerate(self, fps):
        self.frameInterval = 1000 // fps

    # --- Macro Animations ---

    def confuse(self):
        """Play confused animation - one shot animation of eyes shaking left and right"""
        self._confused = True

    def laugh(self):
        """Play laugh animation - one shot animation of eyes shaking up and down"""
        self._laugh = True

    def wink(self, left=None, right=None):
        if not left and not right:
             # Default to right wink if neither specified, or raise error? 
             # Original raised error. Let's make it safe.
             right = True
        self.autoblinker = False 
        self.idle = False 
        self.blink(left=left, right=right)

    def update(self):
        self.sequences.update()
        now = int(time.time() * 1000)
        if (now - self.fpsTimer) >= self.frameInterval:
            self.draw_eyes()
            self.fpsTimer = now

    def draw_eyes(self):
        # ... logic ported from original ...
        # Curious offsets
        if self._curious:
            if self.eyeLxNext <= 10: self.eyeLheightOffset = 8
            elif (self.eyeLxNext >= self.get_screen_constraint_X()-10) and self._cyclops: self.eyeLheightOffset = 8
            else: self.eyeLheightOffset = 0

            if self.eyeRxNext >= (self.screenWidth - self.eyeRwidthCurrent - 10): self.eyeRheightOffset = 8
            else: self.eyeRheightOffset = 0
        else:
            self.eyeLheightOffset = 0
            self.eyeRheightOffset = 0

        # Tweening
        self.eyeLheightCurrent = (self.eyeLheightCurrent + self.eyeLheightNext + self.eyeLheightOffset) // 2
        self.eyeLy += (self.eyeLheightDefault - self.eyeLheightCurrent) // 2
        self.eyeLy -= self.eyeLheightOffset // 2

        self.eyeRheightCurrent = (self.eyeRheightCurrent + self.eyeRheightNext + self.eyeRheightOffset) // 2
        self.eyeRy += (self.eyeRheightDefault - self.eyeRheightCurrent) // 2
        self.eyeRy -= self.eyeRheightOffset // 2

        # Re-open checks
        if self.eyeL_open:
            if self.eyeLheightCurrent <= (1 + self.eyeLheightOffset): self.eyeLheightNext = self.eyeLheightDefault
        if self.eyeR_open:
            if self.eyeRheightCurrent <= (1 + self.eyeRheightOffset): self.eyeRheightNext = self.eyeRheightDefault

        self.eyeLwidthCurrent = (self.eyeLwidthCurrent + self.eyeLwidthNext) // 2
        self.eyeRwidthCurrent = (self.eyeRwidthCurrent + self.eyeRwidthNext) // 2
        self.spaceBetweenCurrent = (self.spaceBetweenCurrent + self.spaceBetweenNext) // 2

        self.eyeLx = (self.eyeLx + self.eyeLxNext) // 2
        self.eyeLy = (self.eyeLy + self.eyeLyNext) // 2
        
        self.eyeRxNext = self.eyeLxNext + self.eyeLwidthCurrent + self.spaceBetweenCurrent
        self.eyeRyNext = self.eyeLyNext
        self.eyeRx = (self.eyeRx + self.eyeRxNext) // 2
        self.eyeRy = (self.eyeRy + self.eyeRyNext) // 2

        self.eyeLborderRadiusCurrent = (self.eyeLborderRadiusCurrent + self.eyeLborderRadiusNext) // 2
        self.eyeRborderRadiusCurrent = (self.eyeRborderRadiusCurrent + self.eyeRborderRadiusNext) // 2

        # Animations
        now = int(time.time() * 1000)
        
        if self.autoblinker:
            if (now - self.blinktimer) >= 0:
                self.blink()
                self.blinktimer = now + (self.blinkInterval * 1000) + (random.randint(0, self.blinkIntervalVariation) * 1000)

        if self._laugh:
            if self.laughToggle:
                self.vert_flicker(True, 5)
                self.laughAnimationTimer = now
                self.laughToggle = False
            elif (now - self.laughAnimationTimer) >= self.laughAnimationDuration:
                self.vert_flicker(False, 0)
                self.laughToggle = True
                self._laugh = False

        if self._confused:
            if self.confusedToggle:
                self.horiz_flicker(True, 20)
                self.confusedAnimationTimer = now
                self.confusedToggle = False
            elif (now - self.confusedAnimationTimer) >= self.confusedAnimationDuration:
                self.horiz_flicker(False, 0)
                self.confusedToggle = True
                self._confused = False

        if self.idle:
            if (now - self.idleAnimationTimer) >= 0:
                self.eyeLxNext = random.randint(0, self.get_screen_constraint_X())
                self.eyeLyNext = random.randint(0, self.get_screen_constraint_Y())
                self.idleAnimationTimer = now + (self.idleInterval * 1000) + (random.randint(0, self.idleIntervalVariation) * 1000)

        # Flickering
        if self.hFlicker:
            if self.hFlickerAlternate:
                self.eyeLx += self.hFlickerAmplitude
                self.eyeRx += self.hFlickerAmplitude
            else:
                self.eyeLx -= self.hFlickerAmplitude
                self.eyeRx -= self.hFlickerAmplitude
            self.hFlickerAlternate = not self.hFlickerAlternate

        if self.vFlicker:
            if self.vFlickerAlternate:
                self.eyeLy += self.vFlickerAmplitude
                self.eyeRy += self.vFlickerAmplitude
            else:
                self.eyeLy -= self.vFlickerAmplitude
                self.eyeRy -= self.vFlickerAmplitude
            self.vFlickerAlternate = not self.vFlickerAlternate

        if self._cyclops:
            self.eyeRwidthCurrent = 0
            self.eyeRheightCurrent = 0
            self.spaceBetweenCurrent = 0

        # DRAWING
        self.fb.clear()
        
        # Eyes
        self.fb.fill_rrect(self.eyeLx, self.eyeLy, self.eyeLwidthCurrent, self.eyeLheightCurrent, self.eyeLborderRadiusCurrent, self.fgcolor)
        if not self._cyclops:
            self.fb.fill_rrect(self.eyeRx, self.eyeRy, self.eyeRwidthCurrent, self.eyeRheightCurrent, self.eyeRborderRadiusCurrent, self.fgcolor)

        # Eyelids calculations
        if self.tired:
            self.eyelidsTiredHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsAngryHeightNext = 0
        else:
            self.eyelidsTiredHeightNext = 0
        if self.angry:
            self.eyelidsAngryHeightNext = self.eyeLheightCurrent // 2
            self.eyelidsTiredHeightNext = 0
        else:
            self.eyelidsAngryHeightNext = 0
        if self.happy:
            self.eyelidsHappyBottomOffsetNext = self.eyeLheightCurrent // 2
        else:
            self.eyelidsHappyBottomOffsetNext = 0

        # Tired
        self.eyelidsTiredHeight = (self.eyelidsTiredHeight + self.eyelidsTiredHeightNext) // 2
        if not self._cyclops:
            self.fb.fill_triangle(self.eyeLx, self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy-1, self.eyeLx, self.eyeLy+self.eyelidsTiredHeight-1, self.bgcolor)
            self.fb.fill_triangle(self.eyeRx, self.eyeRy-1, self.eyeRx+self.eyeRwidthCurrent, self.eyeRy-1, self.eyeRx+self.eyeRwidthCurrent, self.eyeRy+self.eyelidsTiredHeight-1, self.bgcolor)
        else:
            self.fb.fill_triangle(self.eyeLx, self.eyeLy-1, self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy-1, self.eyeLx, self.eyeLy+self.eyelidsTiredHeight-1, self.bgcolor)
            self.fb.fill_triangle(self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy+self.eyelidsTiredHeight-1, self.bgcolor)

        # Angry
        self.eyelidsAngryHeight = (self.eyelidsAngryHeight + self.eyelidsAngryHeightNext) // 2
        if not self._cyclops:
            self.fb.fill_triangle(self.eyeLx, self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy+self.eyelidsAngryHeight-1, self.bgcolor)
            self.fb.fill_triangle(self.eyeRx, self.eyeRy-1, self.eyeRx+self.eyeRwidthCurrent, self.eyeRy-1, self.eyeRx, self.eyeRy+self.eyelidsAngryHeight-1, self.bgcolor)
        else:
             self.fb.fill_triangle(self.eyeLx, self.eyeLy-1, self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy-1, self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy+self.eyelidsAngryHeight-1, self.bgcolor)
             self.fb.fill_triangle(self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy-1, self.eyeLx+self.eyeLwidthCurrent, self.eyeLy-1, self.eyeLx+(self.eyeLwidthCurrent//2), self.eyeLy+self.eyelidsAngryHeight-1, self.bgcolor)

        # Happy
        self.eyelidsHappyBottomOffset = (self.eyelidsHappyBottomOffset + self.eyelidsHappyBottomOffsetNext) // 2
        self.fb.fill_rrect(self.eyeLx-1, (self.eyeLy+self.eyeLheightCurrent)-self.eyelidsHappyBottomOffset+1, self.eyeLwidthCurrent+2, self.eyeLheightDefault, self.eyeLborderRadiusCurrent, self.bgcolor)
        if not self._cyclops:
             self.fb.fill_rrect(self.eyeRx-1, (self.eyeRy+self.eyeRheightCurrent)-self.eyelidsHappyBottomOffset+1, self.eyeRwidthCurrent+2, self.eyeRheightDefault, self.eyeRborderRadiusCurrent, self.bgcolor)

        if self.on_show: self.on_show(self)

    # ... Setters/Getters ...
    def get_screen_constraint_X(self):
        return self.screenWidth - self.eyeLwidthCurrent - self.spaceBetweenCurrent - self.eyeRwidthCurrent

    def get_screen_constraint_Y(self):
        return self.screenHeight - self.eyeLheightDefault

    def blink(self, left=None, right=None):
        if left is None and right is None:
            self.close()
            self.open()
        else:
            self.close(left, right)
            self.open(left, right)

    def close(self, left=None, right=None):
        if left is None and right is None:
            self.eyeLheightNext = 1
            self.eyeRheightNext = 1
            self.eyeL_open = False
            self.eyeR_open = False
        else:
            if left:
                self.eyeLheightNext = 1
                self.eyeL_open = False
            if right:
                self.eyeRheightNext = 1
                self.eyeR_open = False

    def open(self, left=None, right=None):
        if left is None and right is None:
            self.eyeL_open = True
            self.eyeR_open = True
        else:
            if left: self.eyeL_open = True
            if right: self.eyeR_open = True

    def set_auto_blinker(self, active, interval=None, variation=None):
        self.autoblinker = active
        if interval is not None: self.blinkInterval = interval
        if variation is not None: self.blinkIntervalVariation = variation

    def set_idle_mode(self, active, interval=None, variation=None):
        self.idle = active
        if interval is not None: self.idleInterval = interval
        if variation is not None: self.idleIntervalVariation = variation

    @property
    def mood(self): return self._mood

    @mood.setter
    def mood(self, mood):
        if (self._mood in (SCARY, FROZEN)) and not (mood in (SCARY, FROZEN)):
            self.horiz_flicker(False)
            self.vert_flicker(False)
        
        if self._curious and (mood != CURIOUS):
             self._curious = False

        if mood == TIRED:
            self.tired = True; self.angry = False; self.happy = False
        elif mood == ANGRY:
            self.tired = False; self.angry = True; self.happy = False
        elif mood == HAPPY:
            self.tired = False; self.angry = False; self.happy = True
        elif mood == FROZEN:
            self.tired = False; self.angry = False; self.happy = False
            self.horiz_flicker(True, 2)
            self.vert_flicker(False)
        elif mood == SCARY:
            self.tired = True; self.angry = False; self.happy = False
            self.horiz_flicker(False)
            self.vert_flicker(True, 2)
        elif mood == CURIOUS:
            self.tired = False; self.angry = False; self.happy = False
            self._curious = True
        else:
            self.tired = False; self.angry = False; self.happy = False
        self._mood = mood

    def set_mood(self, value): self.mood = value

    def horiz_flicker(self, enable, amplitude=None):
        self.hFlicker = enable
        if amplitude is not None: self.hFlickerAmplitude = amplitude

    def vert_flicker(self, enable, amplitude=None):
        self.vFlicker = enable
        if amplitude is not None: self.vFlickerAmplitude = amplitude
