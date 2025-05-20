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
move_step = 15  # amount player moves per command

# Health bar settings
FONT = pygame.font.Font(None, 50)
HEALTH_BAR_HEIGHT = 30

# MediaPipe hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
cap = cv2.VideoCapture(0)

# Speech recognition
recognizer = sr.Recognizer()

# Punch cooldown
cooldown_time = 500
last_punch_time_p1 = 0
last_punch_time_p2 = 0
p1_punched = False
p2_punched = False

# Block states and timers
p1_blocking = False
p2_blocking = False
block_duration = 1500  # milliseconds
p1_block_start = 0
p2_block_start = 0

# Game states
running = True
game_over = False
fight_mode = False
start_screen = True
mode = None  # "friend" or "bot"

# Bot AI variables
bot_blocking = False
bot_block_start = 0
bot_block_duration = 1000  # ms
bot_punch_cooldown = 1000
last_bot_punch_time = 0

# Function to safely listen to voice commands (non-blocking)
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
        # For player1, forward means move right; player2, move left (facing each other)
        if pos == player1_pos:
            if pos[0] + move_step + 150 < player2_pos[0]:  # prevent overlap
                pos[0] += move_step
        else:
            if pos[0] - move_step > player1_pos[0] + 150:
                pos[0] -= move_step
    elif direction == "back":
        if pos == player1_pos:
            if pos[0] - move_step > 0:
                pos[0] -= move_step
        else:
            if pos[0] + move_step + 150 < WIDTH:
                pos[0] += move_step

while running:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if start_screen:
        screen.fill((0, 0, 0))
        text_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (0, 255, 255)])
        title_text = FONT.render("Say 'Start' to Begin", True, text_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(title_text, title_rect)
        mode_text = FONT.render("Say 'Bot' or 'Friend' mode", True, text_color)
        mode_rect = mode_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(mode_text, mode_rect)

        pygame.display.update()

        command = listen_commands(timeout=2, phrase_time_limit=2)
        if 'start' in command and mode in ['bot', 'friend']:
            start_music.stop()
            fight_effect.play()
            fight_mode = True
            start_screen = False
            main_music.play(-1)
        elif 'quit' in command:
            running = False
        elif 'bot' in command:
            mode = 'bot'
        elif 'friend' in command:
            mode = 'friend'

        continue

    if fight_mode:
        screen.blit(background, (0, 0))

        # Draw health bars
        pygame.draw.rect(screen, (50, 50, 50), (50, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 350, 50, 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (0, 200, 0), (50, 50, (player1_health / 500) * 300, HEALTH_BAR_HEIGHT))
        pygame.draw.rect(screen, (200, 0, 0), (WIDTH - 350, 50, (player2_health / 500) * 300, HEALTH_BAR_HEIGHT))

        player1_punching = False
        player2_punching = False

        current_time = pygame.time.get_ticks()

        # Voice commands
        voice_command = listen_commands(timeout=0.5, phrase_time_limit=1)

        # --- Player 1 commands ---
        if mode == "friend":
            if "p1 forward" in voice_command:
                move_player(player1_pos, "forward")
            elif "p1 back" in voice_command:
                move_player(player1_pos, "back")
            elif "p1 block" in voice_command:
                p1_blocking = True
                p1_block_start = current_time

        # --- Player 2 commands ---
        if mode == "friend":
            if "p2 forward" in voice_command:
                move_player(player2_pos, "forward")
            elif "p2 back" in voice_command:
                move_player(player2_pos, "back")
            elif "p2 block" in voice_command:
                p2_blocking = True
                p2_block_start = current_time

        # --- Bot mode AI ---
        if mode == "bot":
            # Bot randomly blocks
            if not bot_blocking and random.random() < 0.01:
                bot_blocking = True
                bot_block_start = current_time

            # Bot stops blocking after duration
            if bot_blocking and current_time - bot_block_start > bot_block_duration:
                bot_blocking = False

            # Bot punches if cooldown passed and close enough
            if current_time - last_bot_punch_time > bot_punch_cooldown:
                if player2_pos[0] - player1_pos[0] < 200:
                    player1_punching = True
                    if not p1_blocking:
                        player1_health -= 10
                        punch_sound.play()
                    last_bot_punch_time = current_time

        # Hand landmarks punch detection
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x

                # For friend mode, detect punch from hand position (left side = p1, right side = p2)
                if mode == "friend":
                    # Player 1 punch detection (left side)
                    if wrist_x < 0.5 and not p1_punched:
                        if not p2_blocking:
                            player2_health -= 10
                            punch_sound.play()
                        player1_punching = True
                        p1_punched = True
                        last_punch_time_p1 = current_time

                    # Player 2 punch detection (right side)
                    elif wrist_x >= 0.5 and not p2_punched:
                        if not p1_blocking:
                            player1_health -= 10
                            punch_sound.play()
                        player2_punching = True
                        p2_punched = True
                        last_punch_time_p2 = current_time

        # Reset punch flags after cooldown
        if current_time - last_punch_time_p1 > cooldown_time:
            p1_punched = False
        if current_time - last_punch_time_p2 > cooldown_time:
            p2_punched = False

        # Block duration check
        if p1_blocking and current_time - p1_block_start > block_duration:
            p1_blocking = False
        if p2_blocking and current_time - p2_block_start > block_duration:
            p2_blocking = False

        # Draw players with states
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

        # Check game over
        if player1_health <= 0 or player2_health <= 0:
            fight_mode = False
            game_over = True

        pygame.display.update()

    elif game_over:
        screen.fill((0, 0, 0))
        if player1_health <= 0:
            winner_text = FONT.render("Player 2 Wins!", True, (255, 0, 0))
        else:
            winner_text = FONT.render("Player 1 Wins!", True, (0, 255, 0))
        winner_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(winner_text, winner_rect)
        pygame.display.update()

        # Wait for quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        continue

    # Event handling (closing window)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
sys.exit()
