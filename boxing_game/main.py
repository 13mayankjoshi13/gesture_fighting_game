import pygame
import sys
import cv2
import mediapipe as mp
import numpy as np
import speech_recognition as sr
import random
import time

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boxing Game")

# Load images and scale
background = pygame.image.load("boxing_ring.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

player1_idle = pygame.image.load("player1_idle.png")
player1_idle = pygame.transform.scale(player1_idle, (150, 300))
player1_punch = pygame.image.load("player1_punch.png")
player1_punch = pygame.transform.scale(player1_punch, (150, 300))
player1_block = pygame.image.load("player1_block.png")
player1_block = pygame.transform.scale(player1_block, (150, 300))

player2_idle = pygame.image.load("player2_idle.png")
player2_idle = pygame.transform.scale(player2_idle, (150, 300))
player2_punch = pygame.image.load("player2_punch.png")
player2_punch = pygame.transform.scale(player2_punch, (150, 300))
player2_block = pygame.image.load("player2_block.png")
player2_block = pygame.transform.scale(player2_block, (150, 300))

# Sounds
punch_sound = pygame.mixer.Sound("punch.wav")
start_music = pygame.mixer.Sound("start_music.mp3")
fight_effect = pygame.mixer.Sound("fight_effect.mp3")
main_music = pygame.mixer.Sound("main_music.mp3")

# Positions and health
player1_pos = [100, 300]
player2_pos = [550, 300]
player1_health = 500
player2_health = 500
move_step = 15

# Health bar settings
FONT = pygame.font.Font(None, 50)
HEALTH_BAR_HEIGHT = 30

# MediaPipe hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
cap = cv2.VideoCapture(0)

# Speech recognition
recognizer = sr.Recognizer()

# Game states
running = True
game_over = False
fight_mode = False
start_screen = True
mode = None

# AI variables
bot_blocking = False
bot_block_start = 0
bot_block_duration = 1000
bot_punch_cooldown = 1000
last_bot_punch_time = 0

# Cooldowns and flags
cooldown_time = 500
last_punch_time_p1 = 0
last_punch_time_p2 = 0
p1_punched = False
p2_punched = False
p1_blocking = False
p2_blocking = False
block_duration = 1500
p1_block_start = 0
p2_block_start = 0

# Timing for voice command throttling
last_voice_time = 0
voice_command = ""

# Restart button
restart_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)

# Voice listener
def listen_commands(timeout=1, phrase_time_limit=2):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            command = recognizer.recognize_google(audio).lower()
            return command
    except:
        return ""

def move_player(pos, direction):
    if direction == "forward":
        if pos == player1_pos and pos[0] + move_step + 150 < player2_pos[0]:
            pos[0] += move_step
        elif pos == player2_pos and pos[0] - move_step > player1_pos[0] + 150:
            pos[0] -= move_step
    elif direction == "back":
        if pos == player1_pos and pos[0] - move_step > 0:
            pos[0] -= move_step
        elif pos == player2_pos and pos[0] + move_step + 150 < WIDTH:
            pos[0] += move_step

def flash_text(text, color):
    screen.fill((0, 0, 0))
    for _ in range(5):
        flash_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (0, 255, 255)])
        rendered = FONT.render(text, True, flash_color)
        rect = rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(rendered, rect)
        pygame.display.update()
        pygame.time.delay(200)

while running:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_time = pygame.time.get_ticks()
    if current_time - last_voice_time > 1000:
        voice_command = listen_commands(timeout=1, phrase_time_limit=2)
        last_voice_time = current_time

    if start_screen:
        screen.fill((0, 0, 0))
        title_text = FONT.render("Say 'Start' to Begin", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(title_text, title_rect)
        mode_text = FONT.render("Say 'Bot' or 'Friend' mode", True, (255, 255, 255))
        mode_rect = mode_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(mode_text, mode_rect)
        pygame.display.update()

        if 'start' in voice_command and mode in ['bot', 'friend']:
            start_screen = False
            fight_mode = True
            fight_effect.play()
            main_music.play(-1)
        elif 'quit' in voice_command:
            running = False
        elif 'bot' in voice_command:
            mode = 'bot'
        elif 'friend' in voice_command:
            mode = 'friend'
        continue

    if fight_mode:
        screen.blit(background, (0, 0))
        pygame.draw.rect(screen, (50, 50, 50), (50, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 350, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (0, 200, 0), (50, 50, (player1_health / 500) * 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (200, 0, 0), (WIDTH - 350, 50, (player2_health / 500) * 300, HEALTH_BAR_HEIGHT))

        player1_punching = False
        player2_punching = False

        if mode == "friend":
            if "p1 forward" in voice_command:
                move_player(player1_pos, "forward")
            elif "p1 back" in voice_command:
                move_player(player1_pos, "back")
            elif "p1 block" in voice_command:
                p1_blocking = True
                p1_block_start = current_time

            if "p2 forward" in voice_command:
                move_player(player2_pos, "forward")
            elif "p2 back" in voice_command:
                move_player(player2_pos, "back")
            elif "p2 block" in voice_command:
                p2_blocking = True
                p2_block_start = current_time

        elif mode == "bot":
            if not bot_blocking and random.random() < 0.01:
                bot_blocking = True
                bot_block_start = current_time
            if bot_blocking and current_time - bot_block_start > bot_block_duration:
                bot_blocking = False
            if current_time - last_bot_punch_time > bot_punch_cooldown:
                if player2_pos[0] - player1_pos[0] < 200:
                    if not p1_blocking:
                        player1_health -= 10
                        punch_sound.play()
                    last_bot_punch_time = current_time

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
                if mode == "friend":
                    if wrist_x < 0.5 and not p1_punched:
                        if not p2_blocking:
                            player2_health -= 10
                            punch_sound.play()
                        player1_punching = True
                        p1_punched = True
                        last_punch_time_p1 = current_time
                    elif wrist_x >= 0.5 and not p2_punched:
                        if not p1_blocking:
                            player1_health -= 10
                            punch_sound.play()
                        player2_punching = True
                        p2_punched = True
                        last_punch_time_p2 = current_time

        if current_time - last_punch_time_p1 > cooldown_time:
            p1_punched = False
        if current_time - last_punch_time_p2 > cooldown_time:
            p2_punched = False
        if p1_blocking and current_time - p1_block_start > block_duration:
            p1_blocking = False
        if p2_blocking and current_time - p2_block_start > block_duration:
            p2_blocking = False

        if p1_blocking:
            screen.blit(player1_block, player1_pos)
        elif player1_punching:
            screen.blit(player1_punch, player1_pos)
        else:
            screen.blit(player1_idle, player1_pos)

        if p2_blocking or bot_blocking:
            screen.blit(player2_block, player2_pos)
        elif player2_punching:
            screen.blit(player2_punch, player2_pos)
        else:
            screen.blit(player2_idle, player2_pos)

        if player1_health <= 0 or player2_health <= 0:
            fight_mode = False
            game_over = True

        pygame.display.update()

    elif game_over:
        winner = "Player 2 Wins!" if player1_health <= 0 else "Player 1 Wins!"
        flash_text(winner, (255, 255, 255))
        while True:
            screen.fill((0, 0, 0))
            restart_text = FONT.render("Say 'Restart' or 'Quit' or Click Below", True, (255, 255, 255))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 - 60))
            pygame.draw.rect(screen, (100, 100, 255), restart_button)
            btn_label = FONT.render("Restart", True, (255, 255, 255))
            screen.blit(btn_label, (restart_button.x + 30, restart_button.y + 5))
            pygame.display.update()

            cmd = listen_commands(timeout=2, phrase_time_limit=2)
            if "restart" in cmd:
                player1_health = 500
                player2_health = 500
                player1_pos = [100, 300]
                player2_pos = [550, 300]
                game_over = False
                start_screen = True
                mode = None
                break
            elif "quit" in cmd:
                running = False
                break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN and restart_button.collidepoint(event.pos):
                    player1_health = 500
                    player2_health = 500
                    player1_pos = [100, 300]
                    player2_pos = [550, 300]
                    game_over = False
                    start_screen = True
                    mode = None
                    break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
sys.exit()
