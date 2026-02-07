import nxt.locator
import time

# Константа модуля дисплея в памяти NXT
MOD_DISPLAY = 0xA0001
# Смещение начала графических данных в памяти
DISPLAY_OFFSET = 119

def clear_display(b):
    """Очистка экрана: записываем 800 нулевых байт."""
    empty_screen = bytearray(800)
    # Записываем по частям (макс 64 байта за раз в протоколе)
    for i in range(20):
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + i * 40, bytearray(40))

def draw_eyes(b, open=True):
    """Рисуем глаза, модифицируя байты видеопамяти."""
    clear_display(b)
    
    if open:
        # Рисуем упрощенные зрачки (закрашенные области)
        # Это демонстрация: пишем байты 0xFF (столбик из 8 пикселей)
        for i in range(5):
            # Левый глаз (примерные координаты)
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 120 + i, bytearray([0x3C]))
            # Правый глаз
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 160 + i, bytearray([0x3C]))
    else:
        # Рисуем линии (один бит в байте)
        for i in range(10):
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 120 + i, bytearray([0x01]))
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 160 + i, bytearray([0x01]))

def main():
    print("Ищу робота NXT...")
    try:
        b = nxt.locator.find()
        print(f"Подключено к {b.get_device_info()[0]}")
        
        # Сигнал о начале
        b.play_tone(440, 200)

        while True:
            print("Глаза открыты")
            draw_eyes(b, open=True)
            time.sleep(3)
            
            print("Моргание")
            draw_eyes(b, open=False)
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\nОстановка...")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
