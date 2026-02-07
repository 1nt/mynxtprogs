#!/usr/bin/env python3
# Моргающие глаза с высовыванием языка на NXT
# Поддерживает автоматический выбор режима работы с дисплеем

import time
import math
import sys
import nxt.locator

# Параметры экрана
SCREEN_W = 100
SCREEN_H = 64
BUFFER_SIZE = 800  # 100 * (64/8)

# Константы для write_io_map
MOD_DISPLAY = 0xA0001
DISPLAY_OFFSET = 119

# Параметры глаз
LEFT_EYE_CX = 30
RIGHT_EYE_CX = 70
EYE_CY = 32
EYE_R = 8

# Параметры рта и языка
MOUTH_CY = 50
MOUTH_W = 20
TONGUE_X = 50
TONGUE_Y_BASE = 55

OPEN_TIME = 0.8
CLOSED_TIME = 0.2
TONGUE_ANIMATION_FRAMES = 4


class DisplayAdapter:
    """Адаптер дисплея для работы как с brick.display, так и с write_io_map."""
    def __init__(self, brick):
        self.brick = brick
        if hasattr(brick, 'display') and brick.display is not None:
            self.mode = 'high'
            self.disp = brick.display
        elif hasattr(brick, 'write_io_map'):
            self.mode = 'low'
            self.buf = bytearray(BUFFER_SIZE)
        else:
            raise RuntimeError("Нет display и нет write_io_map")

    def clear(self):
        if self.mode == 'high':
            if hasattr(self.disp, 'clear'):
                self.disp.clear()
        else:
            for i in range(BUFFER_SIZE):
                self.buf[i] = 0

    def set_pixel(self, x, y, val=1):
        if not (0 <= x < SCREEN_W and 0 <= y < SCREEN_H):
            return
        x, y = int(x), int(y)
        if self.mode == 'high':
            if hasattr(self.disp, 'set_pixel'):
                try:
                    self.disp.set_pixel(x, y, 1 if val else 0)
                except:
                    pass
        else:
            page = y // 8
            idx = page * SCREEN_W + x
            mask = 1 << (y % 8)
            if val:
                self.buf[idx] |= mask
            else:
                self.buf[idx] &= (~mask & 0xFF)

    def update(self):
        if self.mode == 'high':
            if hasattr(self.disp, 'update'):
                self.disp.update()
        else:
            self._flush_buffer()

    def _flush_buffer(self):
        """Пишет буфер по 40-байтным блокам."""
        try:
            for i in range(20):
                start = i * 40
                chunk = self.buf[start:start + 40]
                self.brick.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + start, bytes(chunk))
                time.sleep(0.01)
        except Exception as e:
            print(f"Ошибка при записи буфера: {e}")


def draw_filled_circle(adapter, cx, cy, r):
    r = int(r)
    for dx in range(-r, r + 1):
        hh = int(math.sqrt(max(0, r * r - dx * dx)))
        x = cx + dx
        for dy in range(-hh, hh + 1):
            y = cy + dy
            adapter.set_pixel(x, y, 1)


def draw_eyes_open(adapter):
    adapter.clear()
    draw_filled_circle(adapter, LEFT_EYE_CX, EYE_CY, EYE_R)
    draw_filled_circle(adapter, RIGHT_EYE_CX, EYE_CY, EYE_R)


def draw_eyes_closed(adapter):
    adapter.clear()
    thickness = 3
    for t in range(-thickness // 2, thickness // 2 + 1):
        y = EYE_CY + t
        for x in range(LEFT_EYE_CX - EYE_R - 2, LEFT_EYE_CX + EYE_R + 3):
            adapter.set_pixel(x, y, 1)
        for x in range(RIGHT_EYE_CX - EYE_R - 2, RIGHT_EYE_CX + EYE_R + 3):
            adapter.set_pixel(x, y, 1)


def draw_mouth(adapter):
    """Рисует улыбку (дугу)."""
    cx = 50
    cy = MOUTH_CY
    r = MOUTH_W
    for angle in range(0, 180):
        x = cx + r * math.cos(math.radians(angle))
        y = cy + r * math.sin(math.radians(angle))
        adapter.set_pixel(x, y, 1)


def draw_tongue(adapter, extension=0):
    """Рисует язык с анимацией выпячивания."""
    if extension <= 0:
        return
    
    cx = TONGUE_X
    base_y = TONGUE_Y_BASE
    
    for i in range(int(extension)):
        y = base_y + i
        width = max(1, int((extension - i) * 0.8))
        for dx in range(-width, width + 1):
            adapter.set_pixel(cx + dx, y, 1)


def main():
    print("Ищу NXT кирпич...")
    try:
        brick = nxt.locator.find()
        if brick is None:
            print("NXT не найден. Проверьте питание и соединение.")
            sys.exit(1)

        try:
            adapter = DisplayAdapter(brick)
        except RuntimeError as e:
            print(f"Ошибка инициализации дисплея: {e}")
            sys.exit(1)

        print(f"Подключено к NXT (режим: {adapter.mode}).")
        print("Запускаю анимацию моргания с высовыванием языка.")
        print("Нажмите Ctrl-C для выхода.\n")

        try:
            while True:
                # Открытые глаза с ртом, язык выходит и входит
                for tongue_len in range(0, TONGUE_ANIMATION_FRAMES + 1):
                    draw_eyes_open(adapter)
                    draw_mouth(adapter)
                    draw_tongue(adapter, tongue_len * 2)
                    adapter.update()
                    time.sleep(0.15)
                
                # Язык входит обратно
                for tongue_len in range(TONGUE_ANIMATION_FRAMES, -1, -1):
                    draw_eyes_open(adapter)
                    draw_mouth(adapter)
                    draw_tongue(adapter, tongue_len * 2)
                    adapter.update()
                    time.sleep(0.15)
                
                # Закрытые глаза
                draw_eyes_closed(adapter)
                adapter.update()
                time.sleep(CLOSED_TIME)
                
        except KeyboardInterrupt:
            print("\n\nВыход: очищаю экран.")
            adapter.clear()
            adapter.update()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
