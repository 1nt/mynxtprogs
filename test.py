import nxt.locator
import time

# Константы дисплея
MOD_DISPLAY = 0xA0001
DISPLAY_OFFSET = 119

def clear_display(b):
    for i in range(20):
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + i * 40, bytearray(40))

def draw_big_eyes(b, tongue=False):
    clear_display(b)
    
    # Рисуем большие глаза (занимают 2 строки по вертикали)
    for i in range(15):
        # Верхняя часть глаз (строка 2)
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 100 + 20 + i, bytearray([0xFF])) # Левый
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 100 + 60 + i, bytearray([0xFF])) # Правый
        # Нижняя часть глаз (строка 3)
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 200 + 20 + i, bytearray([0xFF])) # Левый
        b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 200 + 60 + i, bytearray([0xFF])) # Правый

    if tongue:
        # Рисуем язык (строка 5 и 6 в центре)
        for i in range(10):
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 400 + 45 + i, bytearray([0xFF]))
            b.write_io_map(MOD_DISPLAY, DISPLAY_OFFSET + 500 + 45 + i, bytearray([0x1F]))

def tease(b):
    # Звук "бе-бе-бе" (три коротких сигнала разной тональности)
    for _ in range(3):
        b.play_tone(400, 100)
        time.sleep(0.1)
        b.play_tone(300, 100)
        time.sleep(0.1)

def main():
    print("Запуск робота-хулигана...")
    try:
        b = nxt.locator.find()
        
        while True:
            # Спокойное состояние
            print("Смотрю...")
            draw_big_eyes(b, tongue=False)
            time.sleep(2)
            
            # Робот дразнится
            print("Бе-бе-бе!")
            draw_big_eyes(b, tongue=True)
            tease(b)
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\nПрограмма завершена.")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
