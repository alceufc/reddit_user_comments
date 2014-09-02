import os
import json

def loadSettings():
    SETTINGS_JSON = '../settings.json'
    jsonFile = open(os.path.join(os.path.dirname(__file__), SETTINGS_JSON), 'r')
    settings = json.load(jsonFile)
    jsonFile.close()

    return settings
