import pygame
import socket
import threading
import pickle
import random
import time

# Параметры экрана
WIDTH, HEIGHT = 1200, 700
PLAYER_SIZE = 29
BULLET_SIZE = 5
BOMB_SIZE = 15
FRAGMENT_SIZE = 10
FRAGMENT_COUNT = 100  # Количество осколков от одной бомбы
FPS = 60

# Цвета игроков, пуль, бомб, осколков
COLORS = [(0, 255, 0), (255, 0, 0)]  # Зеленый и красный
BULLET_COLORS = [(0, 128, 0), (128, 0, 0)]
BOMB_COLOR = (255, 255, 0)
FRAGMENT_COLOR = (255, 165, 0)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (169, 169, 169)

# Параметры игроков
positions = [[WIDTH // 4, HEIGHT // 2], [3 * WIDTH // 4, HEIGHT // 2]]
directions = [[0, -1], [0, -1]]  # Начальное направление: вверх
bullets = [[], []]  # Пули каждого игрока
bombs = [[], []]  # Бомбы каждого игрока
fragments = []  # Осколки
health = [100, 100]  # Здоровье игроков
scores = [0, 0]  # Очки игроков
bomb_limits = [3, 3]  # Лимит бомб для каждого игрока


# Аптечки и ускорение
health_packs = []
speed_packs = []
power_up_time = time.time()

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Сетевая игра со здоровьем и очками")
clock = pygame.time.Clock()

# Звук попадания
hit_sound = pygame.mixer.Sound("sound/laser-blast-descend_gy7c5deo.mp3")
hit_sound1 = pygame.mixer.Sound("sound/[Из аниме Наруто [vkhp.net] - Итачи против Саске, битва].mp3")
bomb3_set_sound = pygame.mixer.Sound("sound/bombpl.mp3")  # Звук установки бомбы
bomb_explode_sound = pygame.mixer.Sound("sound/vasa.mp3")  # Звук взрыва бомбы
bomb1_explode_sound = pygame.mixer.Sound("sound/laser-sword-hum_m14hvyno (1).mp3")  # Звук взрыва бомбы

# Сетевые переменные
server_socket = None
client_socket = None
is_server = False
running = True



# Инициализация времени для появления аптечек и ускорений
power_up_time = time.time()  # Изначально установим время старта

def generate_powerups():
    """Генерация аптечек и ускорений на карте"""
    global power_up_time  # Указываем, что работаем с глобальной переменной

    if time.time() - power_up_time > 19:  # Каждые 10 секунд
        # Аптечка
        health_packs.append([random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)])
        # Ускорение
        speed_packs.append([random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)])
        power_up_time = time.time()  # Обновляем время


def handle_client(client_conn):
    global positions, directions, bullets, bombs, fragments, health, scores, running
    while running:
        try:
            data = client_conn.recv(1024)
            if not data:
                break
            client_data = pickle.loads(data)
            positions[1] = client_data['position']
            directions[1] = client_data['direction']
            bullets[1] = client_data['bullets']
            bombs[1] = client_data['bombs']
            health[1] = client_data['health']
            scores[1] = client_data['score']
            server_data = {
                'position': positions[0],
                'direction': directions[0],
                'bullets': bullets[0],
                'bombs': bombs[0],
                'health': health[0],
                'score': scores[0]
            }
            client_conn.send(pickle.dumps(server_data))
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            break
    client_conn.close()

def start_server():
    global server_socket, running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(1)
    print("Сервер запущен. Ожидание подключения...")
    client_conn, addr = server_socket.accept()
    print(f"Игрок подключился: {addr}")
    threading.Thread(target=handle_client, args=(client_conn,)).start()

def connect_to_server(ip):
    global client_socket, positions, directions, bullets, bombs, health, scores, running
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, 12345))
    print("Подключение к серверу успешно!")
    while running:
        try:
            client_data = {
                'position': positions[1],
                'direction': directions[1],
                'bullets': bullets[1],
                'bombs': bombs[1],
                'health': health[1],
                'score': scores[1]
            }
            client_socket.send(pickle.dumps(client_data))
            server_data = pickle.loads(client_socket.recv(1024))
            positions[0] = server_data['position']
            directions[0] = server_data['direction']
            bullets[0] = server_data['bullets']
            bombs[0] = server_data['bombs']
            health[0] = server_data['health']
            scores[0] = server_data['score']
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            break
    client_socket.close()

# Функция для отрисовки экрана окончания игры
def draw_end_screen(winner):
    screen.fill((30, 30, 30))
    font = pygame.font.Font(None, 74)
    text = font.render(f"{winner} победил!", True, (255, 255, 255))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))
    pygame.display.flip()
    pygame.time.wait(3000)

# Улучшенное отображение здоровья, очков и бомб
font = pygame.font.Font(None, 36)

# Цвета для здоровья в зависимости от уровня
def get_health_color(health_value):
    if health_value > 70:
        return (0, 255, 0)  # Зеленый (высокое здоровье)
    elif health_value > 30:
        return (255, 255, 0)  # Желтый (среднее здоровье)
    else:
        return (255, 0, 0)  # Красный (низкое здоровье)


# Функция для отрисовки символов бомб
def draw_bombs(x, y, count):
    for i in range(count):
        bomb_text = font.render("💣", True, (255, 255, 255))  # Используем символ бомбы
        screen.blit(bomb_text, (x + i * 30, y))  # Размещаем их на экране


def game_loop(player_id):
    global positions, directions, bullets, bombs, fragments, health, scores, running, bomb_limits
    lazarus_active = [False, False]  # Использован ли Лазер для каждого игрока
    lazarus_timer = [0, 0]  # Таймер для Лазера
    lazarus_positions = [None, None]  # Позиции для Лазера
    lazarus_directions = [None, None]  # Направления для Лазера

    shield_active = [False, False]  # Активен ли щит
    shield_timer = [0, 0]  # Таймер для щита
    shield_used = [False, False]  # Использован ли щит за игру





    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:# Стрельба
                if event.key == pygame.K_SPACE:


                    hit_sound.play()
                    hit_sound.set_volume(0.2)

                    bullets[player_id].append({
                        'pos': positions[player_id][:],
                        'dir': directions[player_id][:],
                        'speed': 20
                    })


                # Установка бомбы
                if event.key == pygame.K_b and bomb_limits[player_id] > 0:
                    bomb3_set_sound.play()
                    bombs[player_id].append({
                        'pos': positions[player_id][:],
                        'dir': directions[player_id][:],
                        'speed': 10,
                        'timer': 50
                    })
                    bomb_limits[player_id] -= 1

                # Обработчик активации бомбы и генерации осколков
                if event.key == pygame.K_v:  # Активация бомбы
                    bomb_explode_sound.play()
                    for bomb in bombs[player_id]:
                        for _ in range(120):  # Создание множества осколков
                            fragment = {
                                'pos': bomb['pos'][:],  # Копируем позицию бомбы
                                'dir': [random.uniform(-1, 1), random.uniform(-1, 1)],  # Случайное направление
                                'speed': 0.7,  # Скорость осколков
                                'timer': 50  # Время жизни осколка
                            }
                            fragments.append(fragment)  # Добавляем фрагмент
                        bombs[player_id].remove(bomb)  # Удаляем бомбу после взрыва


                # Активация Лазера
                if event.key == pygame.K_p and not lazarus_active[player_id]:  # Лазер активируется один раз
                    bomb1_explode_sound.play()
                    bomb1_explode_sound.set_volume(300)
                    lazarus_active[player_id] = True
                    lazarus_timer[player_id] = 118 # 3 секунды (60 FPS * 3)
                    lazarus_positions[player_id] = positions[player_id][:]
                    lazarus_directions[player_id] = directions[player_id][:]


                # Активация щита
                if event.key == pygame.K_c and not shield_used[player_id]:
                    shield_active[player_id] = True
                    shield_timer[player_id] = 580  # 3 секунды (60 FPS * 3)
                    shield_used[player_id] = True  # Щит можно активировать только один раз за игру


                # Обновление состояния щита
        for i in range(len(shield_active)):
            if shield_active[i]:
                shield_timer[i] -= 1
                if shield_timer[i] <= 0:
                    shield_active[i] = False  # Щит выключается после 3 секунд





        # Обновление Лазера
        for i in range(len(lazarus_timer)):
            if lazarus_active[i]:
                lazarus_timer[i] -= 1
                if lazarus_timer[i] <= 0:
                    lazarus_active[i] = False  # Отключение Лазера
                    lazarus_positions[i] = None
                    lazarus_directions[i] = None

                # Лазер движется в направлении игрока
                if lazarus_positions[i]:
                    lazarus_positions[i][0] = positions[i][0]
                    lazarus_positions[i][1] = positions[i][1]
                    lazarus_directions[i] = directions[i][:]

                    # Проверка на столкновение с другими игроками
                    for j, pos in enumerate(positions):
                        if j != i:  # Не проверяем столкновение с самим собой
                            laser_rect = pygame.Rect(
                                lazarus_positions[i][0],
                                lazarus_positions[i][1],
                                110, 25  # Размер Лазера
                            )
                            player_rect = pygame.Rect(pos[0], pos[1], 40, 40)  # Размер игрока
                            if laser_rect.colliderect(player_rect):  # Если лазер касается игрока
                                health[j] -= 1


        # Отрисовка Лазера
        for i in range(len(lazarus_positions)):
            if lazarus_active[i] and lazarus_positions[i]:
                laser_start = lazarus_positions[i]
                laser_end = [
                    lazarus_positions[i][0] + lazarus_directions[i][0] * 110,
                    lazarus_positions[i][1] + lazarus_directions[i][1] * 110
                ]
                pygame.draw.line(screen, (255, 0, 0), laser_start, laser_end, 5)  # Красный лазер# Проверка на столкновение с осколками
        for fragment in fragments:
            for i in range(len(positions)):
                if shield_active[i]:  # Если щит активен, отталкиваем осколки
                    fragment_dir = [
                        fragment['pos'][0] - positions[i][0],
                        fragment['pos'][1] - positions[i][1]
                    ]
                    distance = (fragment_dir[0] ** 2 + fragment_dir[1] ** 2) ** 0.5
                    if distance < 50:  # Радиус отталкивания щита
                        fragment_dir[0] /= distance
                        fragment_dir[1] /= distance
                        fragment['pos'][0] += fragment_dir[0] * 20  # Отталкиваем осколок
                        fragment['pos'][1] += fragment_dir[1] * 20
                else:  # Если щита нет, проверяем столкновение с игроком
                    player_rect = pygame.Rect(positions[i][0], positions[i][1], 40, 40)
                    fragment_rect = pygame.Rect(fragment['pos'][0], fragment['pos'][1], 5, 5)
                    if player_rect.colliderect(fragment_rect):
                        health[i] -= 1  # Наносим урон# Отрисовка щита
        for i in range(len(shield_active)):
            if shield_active[i]:
                player_rect = pygame.Rect(positions[i][0] - 50, positions[i][1] - 50, 140, 140)
                pygame.draw.ellipse(screen, (0, 0, 250, 128), player_rect, 5)  # Полупрозрачный синий щит

        # Отрисовка щита
        for i in range(len(shield_active)):
            if shield_active[i]:
                player_rect = pygame.Rect(positions[i][0] - 50, positions[i][1] - 50, 140, 140)
                pygame.draw.ellipse(screen, (0, 0, 255, 128), player_rect, 5)  # Полупрозрачный синий щит






        # Обновление экрана
        pygame.display.flip()


        # Управление движением и направлением
        keys = pygame.key.get_pressed()
        if player_id == 0:  # Управление для первого игрока (сервер)
            if keys[pygame.K_LEFT]:
                directions[0] = [-1, 0]
                positions[0][0] -= 5
            if keys[pygame.K_RIGHT]:
                directions[0] = [1, 0]
                positions[0][0] += 5
            if keys[pygame.K_UP]:
                directions[0] = [0, -1]
                positions[0][1] -= 5
            if keys[pygame.K_DOWN]:
                directions[0] = [0, 1]
                positions[0][1] += 5
        elif player_id == 1:  # Управление для второго игрока (клиент)
            if keys[pygame.K_a]:
                directions[1] = [-1, 0]
                positions[1][0] -= 5
            if keys[pygame.K_d]:
                directions[1] = [1, 0]
                positions[1][0] += 5
            if keys[pygame.K_w]:
                directions[1] = [0, -1]
                positions[1][1] -= 5
            if keys[pygame.K_s]:
                directions[1] = [0, 1]
                positions[1][1] += 5



        # Обновление пуль
        for i, player_bullets in enumerate(bullets):
            for bullet in player_bullets:
                bullet['pos'][0] += bullet['dir'][0] * bullet['speed']
                bullet['pos'][1] += bullet['dir'][1] * bullet['speed']

                # Проверка попадания в другого игрока
                target_id = 1 - i
                if (positions[target_id][0] < bullet['pos'][0] < positions[target_id][0] + PLAYER_SIZE and
                    positions[target_id][1] < bullet['pos'][1] < positions[target_id][1] + PLAYER_SIZE):
                    health[target_id] -= 1
                    scores[i] += 1  # За попадание дается 1 очко
                    player_bullets.remove(bullet)
                    # Логика взрыва бомбы


            # Удаление пуль за границей экрана
            bullets[i] = [b for b in player_bullets if 0 <= b['pos'][0] <= WIDTH and 0 <= b['pos'][1] <= HEIGHT]# Обновление бомб
        for i, player_bombs in enumerate(bombs):
            for bomb in player_bombs:
                bomb['pos'][0] += bomb['dir'][0] * bomb['speed']
                bomb['pos'][1] += bomb['dir'][1] * bomb['speed']

        # Обновление осколков
        for fragment in fragments:
            fragment['pos'][0] += fragment['dir'][0] * fragment['speed']
            fragment['pos'][1] += fragment['dir'][1] * fragment['speed']

            # Проверка попадания в игроков
            for i, pos in enumerate(positions):
                if (pos[0] < fragment['pos'][0] < pos[0] + PLAYER_SIZE and pos[1] < fragment['pos'][1] < pos[1] + PLAYER_SIZE):
                    health[i] -= 1  # Урон от осколка

        fragments = [f for f in fragments if 0 <= f['pos'][0] <= WIDTH and 0 <= f['pos'][1] <= HEIGHT]

        # Проверка на конец игры
        if health[0] <= 0 or health[1] <= 0:
            running = False
            winner = "Игрок 2" if health[0] <= 0 else "Игрок 1"
            draw_end_screen(winner)

        # Генерация аптечек и ускорений
        generate_powerups()


        # Обработка аптечек и ускорений
        for i, pack in enumerate(health_packs[:]):
            if positions[player_id][0] < pack[0] < positions[player_id][0] + PLAYER_SIZE and \
                positions[player_id][1] < pack[1] < positions[player_id][1] + PLAYER_SIZE:
                health[player_id] = min(100, health[player_id] + 20)  # Восстановление здоровья
                health_packs.remove(pack)
        for i, pack in enumerate(speed_packs[:]):
            if positions[player_id][0] < pack[0] < positions[player_id][0] + PLAYER_SIZE and \
                positions[player_id][1] < pack[1] < positions[player_id][1] + PLAYER_SIZE:
                positions[player_id][0] += directions[player_id][0] * 120  # Увеличение скорости
                positions[player_id][1] += directions[player_id][1] * 120
                speed_packs.remove(pack)

        # Отрисовка игроков, пуль, бомб, осколков, аптечек и ускорений
        screen.fill((0, 0, 0))

# Отрисовка игроков
        for i, pos in enumerate(positions):
            pygame.draw.rect(screen, COLORS[i], (pos[0], pos[1], PLAYER_SIZE, PLAYER_SIZE))

        # Отрисовка пуль
        for i, player_bullets in enumerate(bullets):
            for bullet in player_bullets:
                pygame.draw.rect(screen, BULLET_COLORS[i], (bullet['pos'][0], bullet['pos'][1], BULLET_SIZE, BULLET_SIZE))

        # Отрисовка бомб
        for i, player_bombs in enumerate(bombs):
            for bomb in player_bombs:
                pygame.draw.circle(screen, BOMB_COLOR, (int(bomb['pos'][0]), int(bomb['pos'][1])), BOMB_SIZE)


        for fragment in fragments:
            pygame.draw.rect(screen, FRAGMENT_COLOR, (fragment['pos'][0], fragment['pos'][1], FRAGMENT_SIZE, FRAGMENT_SIZE))

        # Отрисовка аптечек
        for pack in health_packs:
            pygame.draw.rect(screen, (0, 255, 255), (pack[0], pack[1], 20, 20))

        # Отрисовка ускорений
        for pack in speed_packs:
            pygame.draw.rect(screen, (255, 255, 0), (pack[0], pack[1], 20, 20))


        for i, pos in enumerate(positions):
            pygame.draw.rect(screen, COLORS[i], (pos[0], pos[1], PLAYER_SIZE, PLAYER_SIZE))  # Игроки
            # Отображение здоровья
            pygame.draw.rect(screen, (255, 255, 255), (pos[0], pos[1] - 10, PLAYER_SIZE, 5))  # Белая полоса
            pygame.draw.rect(screen, (0, 255, 0), (pos[0], pos[1] - 10, PLAYER_SIZE * health[i] // 100, 5))  # Здоровье

        for i, pos in enumerate(positions):
            # Отрисовка игрока
            pygame.draw.rect(screen, COLORS[i], (pos[0], pos[1], PLAYER_SIZE, PLAYER_SIZE))# Отображение информации
            health_text_1 = font.render(
                f"Игрок 1 Здоровье: {health[0]} Очки: {scores[0]}",
                True,
                get_health_color(health[0])
            )
            health_text_2 = font.render(
                f"Игрок 2 Здоровье:-{health[1]}-Очки:-{scores[1]}",
                True,
                get_health_color(health[1])
            )

            # Рисуем информацию на экране
            screen.blit(health_text_1, (10, 10))
            draw_bombs(300, 10, bomb_limits[0])  # Бомбы для Игрока 1

            screen.blit(health_text_2, (10, 50))
            draw_bombs(300, 50, bomb_limits[1])  # Бомбы для Игрока 2



            # Фон полосы здоровья
            pygame.draw.rect(screen, (255, 255, 255), (pos[0], pos[1] - 15, PLAYER_SIZE, 8))  # Белая полоса

            # Фон полосы здоровья
            pygame.draw.rect(screen, (255, 255, 255), (pos[0], pos[1] - 15, PLAYER_SIZE, 8))  # Белая полоса
        for i, pos in enumerate(positions):
            # Отрисовка игрока
            pygame.draw.rect(screen, COLORS[i], (pos[0], pos[1], PLAYER_SIZE, PLAYER_SIZE))

            # Градиентная шкала здоровья
            for x in range(PLAYER_SIZE * health[i] // 100):
                color = (255 - int(255 * x / PLAYER_SIZE), int(255 * x / PLAYER_SIZE), 0)  # От красного к зеленому
                pygame.draw.line(screen, color, (pos[0] + x, pos[1] - 15), (pos[0] + x, pos[1] - 7))



        pygame.display.flip()
        clock.tick(FPS)



def main():
    global is_server, running

    choice = input("Введите 's' для запуска сервера или 'c' для подключения к серверу: ").strip().lower()

    if choice == 's'  :
        hit_sound1.play()
        hit_sound1.set_volume(0.05)
        is_server = True
        threading.Thread(target=start_server).start()
        game_loop(0)  # Сервер - первый игрок

    elif choice == 'c' :
        server_ip = input("Введите IP-адрес сервера: ").strip()
        threading.Thread(target=connect_to_server, args=(server_ip,)).start()
        game_loop(1)  # Клиент - второй игрок
    else:
        print("Неверный выбор. Выход...")
        running = False

main()