from gtts import gTTS
import speech_recognition as sr
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
# import pyttsx3
import time
import os

file_name = "Temp_audio/sample_audio.mp3"

# Function to capture audio and recognize speech
def recognize_Response():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening for speech... Speak now.")
        
        try:
            audio_data = recognizer.listen(source, timeout=5)
            print("Processing audio...")
            text = recognizer.recognize_google(audio_data)
            print("You said: " + text)
            return text
        except sr.WaitTimeoutError:
            print("No speech was detected within the timeout duration.")
            print("exiting module")
            exit
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

# Convert text to speech and play it
def text_to_audio(text, language='en', file_name=file_name):
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(file_name)
    time.sleep(1)
    # Load and play the saved audio file
    playsound(file_name)
    os.remove(file_name)


# Evaluation function
def evaluate():
    global user_speech  # Make sure to modify the global variable
    if user_speech == sample_text.lower():
        print("Success!!")
        text_to_audio("You are all set.")
    else:
        text_to_audio("Please try again.")
        user_speech = recognize_Response()  # Update user_speech
        evaluate()

sample_text = "The quick brown fox jumps over the lazy dog"
print("Repeat the sentence below: \n", sample_text,"\n")

user_speech = recognize_Response()

evaluate()

