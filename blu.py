import nxt.locator

def check_connection():
    try:
        print("Попытка связи с /dev/rfcomm0 (nxt-python 3.x)...")
        
        # В версии 3.x используем nxt.locator.find
        # Параметр именуется 'comm', как и раньше
        with nxt.locator.find(comm='/dev/rfcomm0') as brick:
            name, host, bluetooth_address, signal_strength = brick.get_device_info()
            battery = brick.get_battery_level()

            print(f"✅ Связь установлена!")
            print(f"   Имя кирпича: {name}")
            print(f"   Заряд батареи: {battery} мВ")
            
            # Пищим для проверки
            brick.play_tone(440, 200)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Попробуйте выполнить: sudo chmod 666 /dev/rfcomm0")

if __name__ == "__main__":
    check_connection()
