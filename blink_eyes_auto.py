#!/usr/bin/env python3
import time
import math
import sys
import os
import nxt.brick
from nxt.backend.devfile import DevFileSock

# Параметры экрана NXT
SCREEN_W = 100
SCREEN_H = 64
# 100 столбцов по 8 строк (байт) в каждой странице. Всего 8 страниц.
BUFFER_SIZE = 800  

# Константы прямого доступа к памяти
MOD_DISPLAY = 0xA0001
DISPLAY_OFFSET = 119 # Смещение начала видеобуфера

class NxtDisplayDirect:
    def __init__(self, brick):
        self.brick = brick
        if not hasattr(brick, 'write_io_map'):
            raise RuntimeError("Этот кирпич не поддерживает write_io_map.")
        self.buf = bytearray(BUFFER_SIZE)

    def clear(self):
        """Полная очистка буфера"""
        for i in range(BUFFER_SIZE):
            self.buf[i] = 0

    def set_pixel(self, x, y, val=1):
        """Установка пикселя в буфере"""
        if not (0 <= x < SCREEN_W and 0 <= y < SCREEN_H):
            return
        # Вычисляем индекс: страница (y // 8) + столбец (x)
        page = y // 8
        idx = page * SCREEN_W + x
        mask = 1 << (y % 8)
        
        if val:
            self.buf[idx] |= mask
        else:
            self.buf[idx] &= (~mask & 0xFF)

    def update(self):
        """Отправка всего буфера в NXT порциями по 40 байт"""
        try:
            # Дисплей NXT требует записи блоками. 800 байт / 40 = 20 блоков.
            for i in range(20):
                start = i * 40
                chunk = self.buf[start:start + 40]
                self.brick.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + start, bytes(chunk))
        except Exception as e:
            print(f"Ошибка обновления экрана: {e}")

# --- Функции отрисовки ---

def draw_filled_circle(disp, cx, cy, r):
    for dx in range(-r, r + 1):
        hh = int(math.sqrt(max(0, r * r - dx * dx)))
        for dy in range(-hh, hh + 1):
            disp.set_pixel(cx + dx, cy + dy, 1)

def show_eyes(disp, closed=False):
    disp.clear()
    cx_l, cx_r, cy, r = 30, 70, 32, 10
    
    if closed:
        # Рисуем линии вместо кругов (закрытые глаза)
        for x in range(cx_l - r, cx_l + r):
            for t in range(-1, 2): disp.set_pixel(x, cy + t, 1)
        for x in range(cx_r - r, cx_r + r):
            for t in range(-1, 2): disp.set_pixel(x, cy + t, 1)
    else:
        # Открытые глаза
        draw_filled_circle(disp, cx_l, cy, r)
        draw_filled_circle(disp, cx_r, cy, r)
    
    disp.update()

def run_animation(brick):
    disp = NxtDisplayDirect(brick)
    print("Режим прямого управления IO_MAP активирован.")
    try:
        while True:
            show_eyes(disp, closed=False)
            time.sleep(1.5)
            show_eyes(disp, closed=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        disp.clear()
        disp.update()
        print("\nОстановлено.")

# --- Поиск и запуск ---

def main():
    # Попытка Bluetooth (rfcomm0) или USB
    brick = None
    if os.path.exists('/dev/rfcomm0'):
        try:
            brick = DevFileSock('/dev/rfcomm0').connect()
        except: pass

    if not brick:
        import nxt.locator
        try:
            with nxt.locator.find() as b:
                if b: run_animation(b)
        except Exception as e:
            print(f"NXT не найден: {e}")
    else:
        run_animation(brick)

if __name__ == "__main__":
    main()