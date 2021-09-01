# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



import speech_recognition as sr
from os import path
import moviepy.editor as mp
from pydub import AudioSegment

sound = AudioSegment.from_mp3("darkside.mp3")
sound.export("transcript.wav",format="wav")

# transcribe audio file
AUDIO_FILE = "transcript.wav"

# use the audio file as the audio source
r = sr.Recognizer()
with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)  # read the entire audio file

        print("Transcription: " + r.recognize_google(audio))