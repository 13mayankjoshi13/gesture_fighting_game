import pygame
import sys
import cv2
import mediapipe as mp
import numpy as np
import speech_recognition as sr
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boxing Game")

background = pygame.image.load("boxing_ring.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
player1_idle = pygame.image.load("player1_idle.png")
player1_idle = pygame.transform.scale(player1_idle, (150, 300))
player1_punch = pygame.image.load("player1_punch.png")
player1_punch = pygame.transform.scale(player1_punch, (150, 300))
player2_idle = pygame.image.load("player2_idle.png")
player2_idle = pygame.transform.scale(player2_idle, (150, 300))
player2_punch = pygame.image.load("player2_punch.png")
player2_punch = pygame.transform.scale(player2_punch, (150, 300))
punch_sound = pygame.mixer.Sound("punch.wav")
game_over_sound = pygame.mixer.Sound("game_over.mp3")
fight_effect = pygame.mixer.Sound("fight_effect.mp3")
start_music = pygame.mixer.Sound("start_music.mp3")
main_music = pygame.mixer.Sound("main_music.mp3")
winner_music = pygame.mixer.Sound("winner_music.mp3")

player1_pos = [100, 300]
player2_pos = [550, 300]
player1_health = 500
player2_health = 500
FONT = pygame.font.Font(None, 50)
HEALTH_BAR_HEIGHT = 30

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
cap = cv2.VideoCapture(0)

recognizer = sr.Recognizer()

p1_punched = False
p2_punched = False
cooldown_time = 500
last_punch_time_p1 = 0
last_punch_time_p2 = 0

running = True
game_over = False
fight_mode = False
start_screen = True

start_music.play(-1)

flash_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (0, 255, 255)]
particles = []
shake_offset = [0, 0]
shake_intensity = 5

health_bar_flash_duration = 300
p1_health_flash_time = 0
p2_health_flash_time = 0
p1_health_flash = False
p2_health_flash = False

while running:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if start_screen:
        screen.fill((0, 0, 0))

        # Particle Effects
        if random.randint(0, 1):
            particles.append([[random.randint(0, WIDTH), random.randint(0, HEIGHT)], [random.uniform(-2, 2), random.uniform(-2, 2)], random.choice(flash_colors)])
        for particle in particles[:]:
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[1][1] += 0.1  # Gravity effect
            pygame.draw.circle(screen, particle[2], (int(particle[0][0]), int(particle[0][1])), 5)
            if particle[0][1] > HEIGHT or particle[0][0] < 0 or particle[0][0] > WIDTH:
                particles.remove(particle)

        # Flashing Title Text with Shake
        if random.randint(0, 5) == 0:
            shake_offset = [random.randint(-shake_intensity, shake_intensity), random.randint(-shake_intensity, shake_intensity)]
        else:
            shake_offset = [0, 0]
        text_color = random.choice(flash_colors)
        title_text = FONT.render("Say 'Start' to Begin", True, text_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2 + shake_offset[0], HEIGHT // 2 + shake_offset[1]))
        screen.blit(title_text, title_rect)

        pygame.display.update()

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                if 'start' in command:
                    start_music.stop()
                    fight_effect.play()
                    fight_mode = True
                    start_screen = False
                    main_music.play(-1)
                elif 'quit' in command:
                    running = False
                elif 'restart' in command:
                    player1_health = 500
                    player2_health = 500
                    game_over = False
        except:
            pass
        continue

    # FIGHT MODE
    if fight_mode:
        screen.blit(background, (0, 0))

        # Blit Player 1
        screen.blit(player1_punch if p1_punched else player1_idle, player1_pos)

        # Blit Player 2
        screen.blit(player2_punch if p2_punched else player2_idle, player2_pos)

        # Health Bars
        pygame.draw.rect(screen, (50, 50, 50), (50, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 350, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (0, 200, 0), (50, 50, (player1_health / 500) * 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (200, 0, 0), (WIDTH - 350, 50, (player2_health / 500) * 300, HEALTH_BAR_HEIGHT))

        # Health Percentage Text
        p1_health_text = FONT.render(f"{int((player1_health / 500) * 100)}%", True, (255, 255, 255))
        p2_health_text = FONT.render(f"{int((player2_health / 500) * 100)}%", True, (255, 255, 255))
        screen.blit(p1_health_text, (50, 50 + HEALTH_BAR_HEIGHT + 10))
        screen.blit(p2_health_text, (WIDTH - 350, 50 + HEALTH_BAR_HEIGHT + 10))

        pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
sys.exit()
