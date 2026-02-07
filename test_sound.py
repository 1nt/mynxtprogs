#!/usr/bin/env python3
import nxt.locator
import time

print("Ищу NXT кирпич...")
try:
    # Попытка 1: автоматический поиск
    brick = nxt.locator.find()
    
    if not brick:
        # Попытка 2: явный Bluetooth по MAC
        print("Автопоиск не сработал, пытаюсь по MAC...")
        import nxt.socket
        sock = nxt.socket.BluetoothSocket('00:16:53:15:91:CC')
        brick = nxt.brick.Brick(sock)
    
    if brick:
        print("Подключено! Воспроизвожу звук...")
        brick.play_tone(1000, 500)  # 1000 Hz, 500 ms
        time.sleep(0.6)
        brick.play_tone(500, 500)   # 500 Hz, 500 ms
        time.sleep(0.6)
        print("Готово!")
    else:
        print("NXT не найден")
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
