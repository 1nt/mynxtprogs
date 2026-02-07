#!/usr/bin/env python3
import time, math, sys, nxt.locator

SCREEN_W, SCREEN_H, BUFFER_SIZE = 100, 64, 800
MOD_DISPLAY, DISPLAY_OFFSET = 0xA0001, 119
MAN_HEIGHT, HEAD_R, TORSO_LEN = 18, 3, 8
FRAMES, FRAME_DELAY = 4, 0.12

class DisplayAdapter:
    def __init__(self, brick):
        self.brick = brick
        self.mode = 'low'
        self.buf = bytearray(BUFFER_SIZE)

    def clear(self):
        self.buf[:] = b'\x00' * BUFFER_SIZE

    def set_pixel(self, x, y, val=1):
        if not (0 <= x < SCREEN_W and 0 <= y < SCREEN_H): return
        x, y = int(x), int(y)
        page, idx = y // 8, (y // 8) * SCREEN_W + x
        mask = 1 << (y % 8)
        self.buf[idx] = (self.buf[idx] | mask) if val else (self.buf[idx] & (~mask & 0xFF))

    def update(self):
        for i in range(20):
            chunk = self.buf[i*40:(i+1)*40]
            self.brick.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + i*40, bytes(chunk))
            time.sleep(0.01)

def draw_filled_circle(a, cx, cy, r):
    for dx in range(-int(r), int(r)+1):
        hh = int(math.sqrt(max(0, r*r - dx*dx)))
        for dy in range(-hh, hh+1):
            a.set_pixel(cx+dx, cy+dy, 1)

def draw_line(a, x1, y1, x2, y2):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    dx, dy = abs(x2-x1), abs(y2-y1)
    sx, sy = (1 if x1<x2 else -1), (1 if y1<y2 else -1)
    err = dx - dy
    while True:
        a.set_pixel(x1, y1, 1)
        if x1==x2 and y1==y2: break
        e2 = 2*err
        if e2 > -dy: err -= dy; x1 += sx
        if e2 < dx: err += dx; y1 += sy

def draw_man(a, cx, ty, f):
    hcy = ty + HEAD_R
    draw_filled_circle(a, int(cx), int(hcy), HEAD_R)
    tty, tby = hcy + HEAD_R + 1, hcy + HEAD_R + 1 + TORSO_LEN
    draw_line(a, cx, tty, cx, tby)
    arm_o = [(-3,-2,3,-4), (-2,-3,2,-3), (3,-4,-3,-2), (2,-3,-2,-3)]
    leg_o = [(2,6,-2,6), (1,6,-1,6), (-2,6,2,6), (-1,6,1,6)]
    ao, lo = arm_o[f%FRAMES], leg_o[f%FRAMES]
    draw_line(a, cx, tty+1, cx+ao[0], tty+1+ao[1])
    draw_line(a, cx, tty+1, cx+ao[2], tty+1+ao[3])
    draw_line(a, cx, tby, cx+lo[0], tby+lo[1])
    draw_line(a, cx, tby, cx+lo[2], tby+lo[3])

try:
    print("Поиск NXT...")
    # Попытка 1: USB
    try:
        b = nxt.locator.find()
        print("✓ Найдено по USB")
    except:
        # Попытка 2: Bluetooth по MAC
        print("USB не найден, пробую Bluetooth...")
        b = nxt.locator.find(host='00:16:53:15:91:CC')
        print("✓ Найдено по Bluetooth")
    
    a = DisplayAdapter(b)
    print("✓ Запуск анимации...\n")
    x, ty, f = -10, (SCREEN_H-MAN_HEIGHT)//2, 0
    while True:
        a.clear()
        draw_man(a, x+MAN_HEIGHT//2, ty, f)
        a.update()
        time.sleep(FRAME_DELAY)
        f = (f+1) % FRAMES
        x += 1
        if x > SCREEN_W: x = -10
except KeyboardInterrupt:
    print("\nВыход")
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
