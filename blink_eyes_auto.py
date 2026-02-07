#!/usr/bin/env python3
# Универсальный "моргающие глаза" для NXT — автоматически выбирает display или write_io_map
# Поддерживает: nxt-python с brick.display или версии без display (через write_io_map)
#
# Запуск: python3 blink_eyes_auto.py

import time
import math
import sys
import os
import logging
import nxt.brick
from nxt.backend.devfile import DevFileSock

logging.basicConfig(level=logging.DEBUG)

# Параметры экрана
SCREEN_W = 100
SCREEN_H = 64
BUFFER_SIZE = 800  # 100 * (64/8)

# Константы для write_io_map fallback
MOD_DISPLAY = 0xA0001
# Часто используемое смещение в примерах — у вас было 119
DISPLAY_OFFSET = 119

# Параметры глаз
LEFT_EYE_CX = 30
RIGHT_EYE_CX = 70
EYE_CY = 32
EYE_R = 8

OPEN_TIME = 0.8
CLOSED_TIME = 0.2


class DisplayAdapter:
    """Адаптер дисплея: обеспечивает clear(), set_pixel(x,y,val), update()."""
    def __init__(self, brick):
        self.brick = brick
        # режим: 'high' если brick.display доступен, 'low' если используем write_io_map
        if hasattr(brick, 'display') and brick.display is not None:
            self.mode = 'high'
            self.disp = brick.display
        elif hasattr(brick, 'write_io_map'):
            self.mode = 'low'
            self.buf = bytearray(BUFFER_SIZE)
        else:
            raise RuntimeError("В brick нет display и нет write_io_map — не могу рисовать.")

    # --- Общие методы ---
    def clear(self):
        if self.mode == 'high':
            # пробуем общие методы
            if hasattr(self.disp, 'clear'):
                self.disp.clear()
            elif hasattr(self.disp, 'clear_screen'):
                self.disp.clear_screen()
            else:
                # если display есть, но нет метода очистки — пытаемся заполнить нулями через set_pixel
                for y in range(SCREEN_H):
                    for x in range(SCREEN_W):
                        if hasattr(self.disp, 'set_pixel'):
                            self.disp.set_pixel(x, y, 0)
            # не делаем update здесь — caller должен вызвать update если надо
        else:
            # очистка буфера
            for i in range(BUFFER_SIZE):
                self.buf[i] = 0
            # сразу записываем на устройство
            self._flush_buffer()

    def set_pixel(self, x, y, val=1):
        if not (0 <= x < SCREEN_W and 0 <= y < SCREEN_H):
            return
        if self.mode == 'high':
            # разные реализации: set_pixel(x,y,val) или set_pixel(x,y) with bool
            if hasattr(self.disp, 'set_pixel'):
                try:
                    # стараемся передать 1/0
                    self.disp.set_pixel(int(x), int(y), 1 if val else 0)
                except TypeError:
                    # возможно set_pixel принимает только x,y (необычно) — игнорируем
                    try:
                        self.disp.set_pixel(int(x), int(y))
                    except Exception:
                        pass
            else:
                # fallback: ничего
                pass
        else:
            # вычисляем индекс в буфере: страница = y // 8, индекс = page*100 + x
            page = y // 8
            idx = page * SCREEN_W + x
            mask = 1 << (y % 8)
            if val:
                self.buf[idx] |= mask
            else:
                self.buf[idx] &= (~mask & 0xFF)

    def update(self):
        if self.mode == 'high':
            # разные имена: update() / commit() / refresh()
            if hasattr(self.disp, 'update'):
                self.disp.update()
            elif hasattr(self.disp, 'commit'):
                self.disp.commit()
            elif hasattr(self.disp, 'refresh'):
                self.disp.refresh()
            else:
                # ничего — может быть immediate
                pass
        else:
            self._flush_buffer()

    def _flush_buffer(self):
        # запись буфера по 40-байтным блокам, с DISPLAY_OFFSET как в ваших примерах
        # некоторые реализации write_io_map требуют длину 40, поэтому разбиваем на 20 блоков по 40
        if not hasattr(self.brick, 'write_io_map'):
            raise RuntimeError("Нет write_io_map для записи буфера.")
        try:
            for i in range(20):
                start = i * 40
                chunk = self.buf[start:start + 40]
                # write_io_map(mod, offset, bytearray)
                self.brick.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + start, bytes(chunk))
        except Exception as e:
            raise RuntimeError("Ошибка записи буфера в io_map: " + str(e))


# --- Вспомогательные рисовалки ---
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
    adapter.update()


def draw_eyes_closed(adapter):
    adapter.clear()
    thickness = 3
    for t in range(-thickness // 2, thickness // 2 + 1):
        y = EYE_CY + t
        for x in range(LEFT_EYE_CX - EYE_R - 2, LEFT_EYE_CX + EYE_R + 3):
            adapter.set_pixel(x, y, 1)
        for x in range(RIGHT_EYE_CX - EYE_R - 2, RIGHT_EYE_CX + EYE_R + 3):
            adapter.set_pixel(x, y, 1)
    adapter.update()


def run_with_brick(brick):
    try:
        adapter = DisplayAdapter(brick)
    except RuntimeError as e:
        print("Не могу инициализировать адаптер дисплея:", e)
        print("dir(brick) ->", ", ".join(a for a in dir(brick) if not a.startswith("_")))
        sys.exit(1)

    print("Использую режим:", adapter.mode)
    print("Запускаю анимацию. Ctrl-C для выхода.")
    try:
        while True:
            draw_eyes_open(adapter)
            time.sleep(OPEN_TIME)
            draw_eyes_closed(adapter)
            time.sleep(CLOSED_TIME)
    except KeyboardInterrupt:
        print("\nВыход: очищаю экран.")
        try:
            adapter.clear()
        except Exception:
            pass


def main():
    rfcomm_path = '/dev/rfcomm0'
    brick = None

    # Попытка прямого подключения по devfile (часто используется для Bluetooth RFCOMM)
    if os.path.exists(rfcomm_path):
        print('Пробую подключиться к кирпичу через', rfcomm_path)
        try:
            sock = DevFileSock(rfcomm_path)
            brick = sock.connect()
            print('Подключено через', rfcomm_path)
        except Exception as e:
            print('Не удалось подключиться через', rfcomm_path + ':', e)
            brick = None

    # Фоллбек: поиск кирпича (USB/Bluetooth через nxt.locator)
    if brick is None:
        # Пытаемся использовать модуль locator, если он доступен в установленном пакете
        if hasattr(nxt, 'locator') and hasattr(nxt.locator, 'find'):
            print('Ищу NXT кирпич (использую nxt.locator.find)...')
            try:
                with nxt.locator.find() as found:
                    if found is None:
                        print('NXT не найден. Проверьте питание/соединение.')
                        sys.exit(1)
                    run_with_brick(found)
                    return
            except Exception as e:
                print('Ошибка при попытке найти кирпич:', e)
                sys.exit(1)
        else:
            print('Модуль nxt.locator не доступен в этой установке. Подключитесь вручную или используйте /dev/rfcomm0.')
            sys.exit(1)

    # Если дошли сюда, используем явно созданный brick
    try:
        run_with_brick(brick)
    finally:
        try:
            if hasattr(brick, 'sock') and brick.sock is not None:
                try:
                    brick.sock.close()
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == "__main__":
    main()