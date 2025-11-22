import pygame
import random
import sys
import math
import os
import tkinter as tk
from tkinter import messagebox
import urllib.request
import json

# --- 초기화 ---
pygame.init()

# --- 사운드 로딩 함수 ---
def load_sound(file_path):
    try:
        sound = pygame.mixer.Sound(file_path)
        print(f"사운드 파일 '{file_path}' 로딩 성공!")
        return sound
    except (pygame.error, FileNotFoundError) as e:
        print(f"사운드 파일 '{file_path}' 로딩 오류: {e}.")
        return None

# --- 남극 날씨 API 호출 함수 ---
def get_weather_for_station(station_name, latitude, longitude):
    """주어진 위도와 경도에 대한 날씨 정보를 가져와 문자열로 반환합니다."""
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    try:
        # 타임아웃을 5초로 설정하여 API가 응답 없을 때 게임이 멈추는 것을 방지
        with urllib.request.urlopen(api_url, timeout=5) as url:
            data = json.loads(url.read().decode())
            if "current_weather" in data:
                weather = data["current_weather"]
                temp = weather["temperature"]
                wind = weather["windspeed"]
                return f"{station_name}: 기온 {temp}°C, 풍속 {wind}km/h"
            else:
                return f"{station_name}: 날씨 정보 없음"
    except Exception as e:
        print(f"API Error for {station_name}: {e}")
        return f"{station_name}: 정보 조회 실패"

def fetch_antarctic_weather():
    """세종 기지와 장보고 기지의 날씨 정보를 모두 가져옵니다."""
    sejong_info = get_weather_for_station("세종 과학 기지", -62.22, -58.78)
    jangbogo_info = get_weather_for_station("장보고 과학 기지", -74.62, 164.22)
    
    return f"남극 기지 현재 날씨\n- {sejong_info}\n- {jangbogo_info}"


# --- 사운드 설정 ---
pygame.mixer.init()
script_dir = os.path.dirname(os.path.abspath(__file__))
wind_sound = load_sound(os.path.join(script_dir, "432583__inchadney__the-wind.mp3"))
penguin_cry_sound = load_sound(os.path.join(script_dir, "705839__breviceps__penguin-squeak (1).wav"))
penguin_land_sound = load_sound(os.path.join(script_dir, "705839__breviceps__penguin-squeak (1).wav"))

if wind_sound:
    wind_sound.set_volume(0.3)

# --- 화면 설정 ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("펭귄 시소 게임")

# --- 색상 정의 ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
SKY_BLUE = (135, 206, 250)
WATER_BLUE = (20, 100, 180)
ICE_WHITE = (230, 240, 255)
SEESAW_COLOR = (139, 69, 19) # Brown
FULCRUM_COLOR = (112, 128, 144) # SlateGray

# --- 게임 설정 ---
clock = pygame.time.Clock()
FONT = pygame.font.SysFont('malgungothic', 30)

# --- 펭귄 설정 ---
PENGUIN_SIZES = [
    {"size": (20, 30), "weight": 1.0},
    {"size": (25, 40), "weight": 1.5},
    {"size": (30, 50), "weight": 2.0},
    {"size": (35, 60), "weight": 2.5},
    {"size": (40, 70), "weight": 3.0},
]

# --- 펭귄 이미지 생성 함수 ---
def create_penguin_image(size):
    width, height = size
    image = pygame.Surface(size, pygame.SRCALPHA)
    body_radius = width // 2
    pygame.draw.circle(image, BLACK, (body_radius, height - body_radius), body_radius)
    belly_radius = body_radius - 4
    pygame.draw.circle(image, WHITE, (body_radius, height - body_radius), belly_radius)
    head_radius = width // 3
    pygame.draw.circle(image, BLACK, (body_radius, height - body_radius * 2 - head_radius // 2), head_radius)
    beak_points = [(body_radius, height - body_radius * 2 - head_radius), (body_radius + 5, height - body_radius * 2), (body_radius - 5, height - body_radius * 2)]
    pygame.draw.polygon(image, (255, 165, 0), beak_points)
    return image

PENGUIN_IMAGES = [create_penguin_image(p["size"]) for p in PENGUIN_SIZES]

# --- 펭귄 클래스 ---
class Penguin(pygame.sprite.Sprite):
    def __init__(self, index):
        super().__init__()
        self.index = index
        self.original_image = PENGUIN_IMAGES[index]
        self.image = self.original_image
        self.weight = PENGUIN_SIZES[index]["weight"]
        self.rect = self.image.get_rect()
        self.x, self.y = 0.0, 0.0
        self.is_falling = True
        self.roll_angle = 0

    def update_image_angle(self, angle):
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def roll(self, slide_direction):
        self.roll_angle += slide_direction * 15
        center = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, self.roll_angle)
        self.rect = self.image.get_rect(center=center)

# --- 시소 클래스 ---
class Seesaw:
    def __init__(self):
        self.width = 600
        self.height = 20
        self.fulcrum_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.7)
        self.angle = 0.0
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(SEESAW_COLOR)
        self.rect = self.image.get_rect(center=self.fulcrum_pos)

    def update(self, penguins):
        left_torque = 0
        right_torque = 0
        for p in penguins:
            dist_from_center = p.x - self.fulcrum_pos[0]
            torque = p.weight * dist_from_center
            if dist_from_center < 0:
                left_torque += abs(torque)
            else:
                right_torque += torque

        net_torque = right_torque - left_torque
        target_angle = -net_torque * 0.05
        self.angle += (target_angle - self.angle) * 0.1
        self.angle = max(-45, min(45, self.angle))

    def draw(self, surface):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rotated_rect = rotated_image.get_rect(center=self.fulcrum_pos)
        surface.blit(rotated_image, rotated_rect)
        pygame.draw.polygon(surface, FULCRUM_COLOR, [
            (self.fulcrum_pos[0], self.fulcrum_pos[1] + self.height // 2),
            (self.fulcrum_pos[0] - 30, self.fulcrum_pos[1] + 50),
            (self.fulcrum_pos[0] + 30, self.fulcrum_pos[1] + 50)
        ])

# --- 배경 그리기 함수 ---
def draw_background():
    screen.fill(WATER_BLUE)
    pygame.draw.rect(screen, SKY_BLUE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT * 0.7))
    pygame.draw.polygon(screen, ICE_WHITE, [(0, SCREEN_HEIGHT * 0.6), (SCREEN_WIDTH, SCREEN_HEIGHT * 0.65), (SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)])
    pygame.draw.rect(screen, ICE_WHITE, (100, SCREEN_HEIGHT * 0.8, 150, 40))
    pygame.draw.rect(screen, ICE_WHITE, (700, SCREEN_HEIGHT * 0.9, 200, 50))

# --- 텍스트 출력 함수 ---
def draw_text(text, surface, x, y, size=40, color=BLACK):
    font = pygame.font.SysFont('malgungothic', size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)

# --- 메인 게임 루프 (빠른 낙하 기능 추가) ---
def game_loop():
    seesaw = Seesaw()
    landed_penguins = pygame.sprite.Group()
    
    falling_penguin = None
    fall_speed = 2
    
    score = 0
    last_score_time = pygame.time.get_ticks()

    game_state = "playing"
    animation_started = True

    while game_state != "quit_loop":
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state = "quit_loop"

        if game_state == "playing":
            if falling_penguin is None:
                penguin_index = random.randint(0, len(PENGUIN_SIZES) - 1)
                falling_penguin = Penguin(penguin_index)

                # 시소의 왼쪽(200-400) 또는 오른쪽(600-800) 구역에만 펭귄이 떨어지도록 설정
                if random.random() < 0.5: # 50% 확률로 좌측 구역
                    random_x = random.randint(200, 400)
                else: # 50% 확률로 우측 구역
                    random_x = random.randint(600, 800)

                falling_penguin.rect.center = (random_x, 50)
                falling_penguin.x, falling_penguin.y = falling_penguin.rect.center
                fall_speed = min(10, fall_speed + 0.05)

            keys = pygame.key.get_pressed()
            if falling_penguin:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    falling_penguin.x -= 5
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    falling_penguin.x += 5
                
                # 빠른 낙하 로직
                effective_fall_speed = fall_speed
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    effective_fall_speed *= 4 # 4배 빠르게
                    score += 1 # 보너스 점수

                falling_penguin.y += effective_fall_speed
                falling_penguin.rect.center = (falling_penguin.x, falling_penguin.y)

                # 펭귄이 화면 밖으로 떨어졌는지 확인
                if falling_penguin.rect.top > SCREEN_HEIGHT:
                    if penguin_cry_sound:
                        penguin_cry_sound.play()
                    game_state = "game_over_animation"

            seesaw.update(landed_penguins)

            if falling_penguin and game_state == "playing":
                landed = False
                seesaw_y_at_penguin_x = seesaw.fulcrum_pos[1] - math.sin(math.radians(seesaw.angle)) * (falling_penguin.x - seesaw.fulcrum_pos[0])
                if falling_penguin.rect.bottom >= seesaw_y_at_penguin_x and abs(falling_penguin.x - seesaw.fulcrum_pos[0]) < seesaw.width / 2:
                    falling_penguin.y = seesaw_y_at_penguin_x - falling_penguin.rect.height / 2
                    landed = True
                else:
                    for p in landed_penguins:
                        # 떨어지는 펭귄과 이미 착지한 펭귄이 충돌했는지 확인
                        if pygame.sprite.collide_rect(falling_penguin, p):
                            # 아래에 있던 펭귄을 밀어냅니다.
                            if falling_penguin.x < p.x:
                                p.x += 20  # 오른쪽으로 20픽셀 밀기
                            else:
                                p.x -= 20  # 왼쪽으로 20픽셀 밀기

                            # 떨어지는 펭귄은 시소 위에 착지시킵니다.
                            seesaw_y_at_penguin_x = seesaw.fulcrum_pos[1] - math.sin(math.radians(seesaw.angle)) * (falling_penguin.x - seesaw.fulcrum_pos[0])
                            if falling_penguin.rect.bottom >= seesaw_y_at_penguin_x:
                                falling_penguin.y = seesaw_y_at_penguin_x - falling_penguin.rect.height / 2
                                landed = True
                                break
                if landed:
                    if penguin_land_sound:
                        print("펭귄 착지! 사운드 재생 시도.")
                        penguin_land_sound.play()
                    falling_penguin.is_falling = False
                    landed_penguins.add(falling_penguin)
                    falling_penguin = None

            slide_force = -math.sin(math.radians(seesaw.angle)) * 0.15
            for p in landed_penguins:
                p.x += slide_force * p.weight
                p_seesaw_y = seesaw.fulcrum_pos[1] - math.sin(math.radians(seesaw.angle)) * (p.x - seesaw.fulcrum_pos[0])
                p.y = p_seesaw_y - p.rect.height / 2
                p.rect.center = (p.x, p.y)
                p.update_image_angle(seesaw.angle)

                seesaw_end_x1 = seesaw.fulcrum_pos[0] - (seesaw.width / 2) * math.cos(math.radians(seesaw.angle))
                seesaw_end_x2 = seesaw.fulcrum_pos[0] + (seesaw.width / 2) * math.cos(math.radians(seesaw.angle))
                if not (seesaw_end_x1 < p.x < seesaw_end_x2):
                    if penguin_cry_sound:
                        print("펭귄 낙하! 사운드 재생 시도.")
                        penguin_cry_sound.play()
                    game_state = "game_over_animation"
                    break
            
            if now - last_score_time > 1000:
                score += len(landed_penguins)
                last_score_time = now

        elif game_state == "game_over_animation":
            if animation_started:
                # 애니메이션 시작 시 시소 각도를 강제로 기울입니다.
                if seesaw.angle >= 0:
                    seesaw.angle = 40
                else:
                    seesaw.angle = -40
                animation_started = False

            slide_force = -math.sin(math.radians(seesaw.angle)) * 2
            for p in landed_penguins:
                p.x += slide_force * p.weight
                p.y += 5
                p.rect.center = (p.x, p.y)
                p.roll(math.copysign(1, slide_force))
            
            if len(landed_penguins) == 0:
                return "game_over"

        draw_background()
        seesaw.draw(screen)
        landed_penguins.draw(screen)
        if falling_penguin:
            screen.blit(falling_penguin.image, falling_penguin.rect)
        
        draw_text(f"점수: {score}", screen, 80, 30)

        pygame.display.flip()
        clock.tick(60)

        for p in list(landed_penguins):
            if p.rect.top > SCREEN_HEIGHT:
                p.kill()

    return game_state

# --- 게임 시작 함수 ---
if __name__ == '__main__':
    if wind_sound:
        wind_sound.play(loops=-1)

    while True:
        game_result = game_loop()
        if game_result == "quit_loop":
            break
        
        if game_result == "game_over":
            antarctic_weather_info = fetch_antarctic_weather() # API 호출
            game_over_message = f"다시 하시겠습니까?\n\n{antarctic_weather_info}" # 날씨 정보 추가

            root = tk.Tk()
            root.withdraw()
            play_again = messagebox.askyesno("게임 오버", game_over_message) # 수정된 메시지 사용
            root.destroy()

            if not play_again:
                break

    pygame.quit()
    sys.exit()
