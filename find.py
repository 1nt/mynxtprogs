import logging
import nxt.brick
from nxt.backend.devfile import DevFileSock

logging.basicConfig(level=logging.DEBUG)

try:
    print("Подключение к /dev/rfcomm0 через бэкенд devfile...")
    # Используем класс DevFileSock напрямую из предоставленного вами devfile.py
    sock = DevFileSock('/dev/rfcomm0')
    
    # Устанавливаем соединение
    brick = sock.connect()
    
    print(f"✅ Успех! Кирпич найден: {brick.get_device_info()[0]}")
    brick.play_tone(440, 250)
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
