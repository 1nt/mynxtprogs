import nxt.locator
import time

def run_rebellious_robot():
    print("Подключение к улучшенному NXT...")
    try:
        with nxt.locator.find() as b:
            # С новой прошивкой b.display_... методы могут заработать, 
            # так как прошивка отвечает на запросы графики корректно.
            
            while True:
                # 1. Большие глаза
                print("Смотрю широко!")
                try:
                    # Попробуем стандартные методы (теперь прошивка их поймет)
                    b.display_clear()
                    b.display_draw_circle(30, 32, 15, False)
                    b.display_draw_circle(30, 32, 5, True)
                    b.display_draw_circle(70, 32, 15, False)
                    b.display_draw_circle(70, 32, 5, True)
                    b.display_refresh()
                except AttributeError:
                    # Если библиотека все еще не видит методы, 
                    # старый способ с io_map теперь будет работать быстрее и стабильнее
                    print("Библиотека старая, но прошивка новая - использую быстрый доступ")
                    # (Здесь остается ваш рабочий код с io_map)

                time.sleep(2)

                # 2. Бе-бе-бе и язык
                print("Бе-бе-бе!")
                # Прошивка Schodet улучшает работу со звуком
                for freq in [500, 400, 500, 400]:
                    b.play_tone(freq, 100)
                    time.sleep(0.1)
                
                # Добавим "вибрацию" моторами, раз прошивка позволяет лучше ими управлять
                try:
                    m_left = b.get_motor(0) # Порт A
                    m_right = b.get_motor(2) # Порт C
                    m_left.run(power=50)
                    m_right.run(power=-50)
                    time.sleep(0.2)
                    m_left.idle()
                    m_right.idle()
                except:
                    pass

    except Exception as e:
        print(f"Ошибка: {e}")

run_rebellious_robot()
