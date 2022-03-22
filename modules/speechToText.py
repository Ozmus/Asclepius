import soundfile
import speech_recognition as sr
import os

from modules.dialogFlow import detectIntent


def speechRecognition():
    filename = "voiceOfAsclepius/records/newOut.wav"
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
    path = "voiceOfAsclepius/records"
    absolutePath = os.path.abspath(path)
    outFile = absolutePath + "/out.wav"
    command = f"ffmpeg -f s16le -ar 48000 -ac 2 -i " + path + "/merge.pcm" + " " + outFile
    os.system(command)
    os.remove(path + "/merge.pcm")
    data, samplerate = soundfile.read(outFile)
    soundfile.write(path + '/newOut.wav', data, samplerate, subtype="PCM_16")
    os.remove(outFile)
    text = speechRecognition()
    detectedIntent, fullfillmentText, sentimentScore = detectIntent(text)
    return detectedIntent, fullfillmentText, sentimentScore
