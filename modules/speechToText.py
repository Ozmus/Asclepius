import soundfile
import speech_recognition as sr
import os
import time
from modules.dialogFlow import detectIntent
from pydub import AudioSegment


def speechRecognition():
    filename = "/home/irem/Asclepius/voiceOfAsclepius/records/newOut.wav"
    r = sr.Recognizer()
    text = ""
    try:
        with sr.AudioFile(filename) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="en-EN")

    except:
        pass
    return text


def stopSoundRecord():
    time.sleep(7)
    os.chdir("voiceOfAsclepius/records")
    mp3_sound = AudioSegment.from_mp3("audio.mp3")
    mp3_sound.export("{0}.wav".format("newOut"), format="wav")
    data, samplerate = soundfile.read("newOut.wav")
    soundfile.write("newOut.wav", data, 48000)
    text = speechRecognition()
    detectedIntent, fullfillmentText, sentimentScore = detectIntent(text)
    return detectedIntent, fullfillmentText, sentimentScore
