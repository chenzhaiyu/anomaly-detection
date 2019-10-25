import pyttsx3
import pygame
import time


def warn_object(object_name="object"):
    engine = pyttsx3.init()
    sentence = object_name + "detected"
    engine.say(sentence)
    engine.runAndWait()


def warn_change():
    music_file = r"/home/zk/PycharmProjects/Detection-v1.0/alarm.mp3"
    pygame.mixer.init()
    print("start alarming")
    track = pygame.mixer.music.load(music_file)

    pygame.mixer.music.play(-1)
    time.sleep(1.5)
    pygame.mixer.music.stop()


if __name__ == '__main__':
    warn_object()
    warn_change()