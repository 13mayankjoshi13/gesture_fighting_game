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
start_music = pygame.mixer.Sound("start_music.mp3")
fight_effect = pygame.mixer.Sound("fight_effect.mp3")
main_music = pygame.mixer.Sound("main_music.mp3")

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

while running:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if start_screen:
        screen.fill((0, 0, 0))

        # Flashing Title Text
        text_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (0, 255, 255)])
        title_text = FONT.render("Say 'Start' to Begin", True, text_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
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

        # Health Bars
        pygame.draw.rect(screen, (50, 50, 50), (50, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 350, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (0, 200, 0), (50, 50, (player1_health / 500) * 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (200, 0, 0), (WIDTH - 350, 50, (player2_health / 500) * 300, HEALTH_BAR_HEIGHT))

        player1_punching = False
        player2_punching = False
        current_time = pygame.time.get_ticks()

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x

                # Instant Punch Detection
                if wrist_x < 0.5 and not p1_punched:
                    player1_punching = True
                    player2_health -= 10
                    punch_sound.play()
                    p1_punched = True
                    last_punch_time_p1 = current_time
                elif wrist_x >= 0.5 and not p2_punched:
                    player2_punching = True
                    player1_health -= 10
                    punch_sound.play()
                    p2_punched = True
                    last_punch_time_p2 = current_time

        # Reset Punch Cooldown
        if current_time - last_punch_time_p1 > cooldown_time:
            p1_punched = False
        if current_time - last_punch_time_p2 > cooldown_time:
            p2_punched = False

        # Blit Players
        screen.blit(player1_punch if player1_punching else player1_idle, player1_pos)
        screen.blit(player2_punch if player2_punching else player2_idle, player2_pos)

        # Display Winner
        if player1_health <= 0 or player2_health <= 0:
            winner_text = "Player 1 Wins!" if player2_health <= 0 else "Player 2 Wins!"
            screen.blit(FONT.render(winner_text, True, (255, 255, 0)), (WIDTH // 2 - 150, HEIGHT // 2 - 50))
            pygame.display.update()
            pygame.time.wait(3000)
            running = False

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
sys.exit()
