import json
import os
import time
import requests


def tts(text):
    headers = {
        "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZWZmM2JmZmUtYjQ0Ny00Y2QxLWE5MmMtNzliYWI0NGNhNDVjIiwidHlwZSI6ImFwaV90b2tlbiJ9.6aY4-otPPlqk5ZmiGgrb4SlhPhwjRwTBDbSrKW6O1ss"}
    url = 'https://api.edenai.run/v2/audio/text_to_speech'
    payload = {
        "providers": "lovoai", "language": "ru-RU",
        "option": "MALE",
        "lovoai": "ru-RU_Pyotr Semenov",
        "text": f'{text}'
    }
    response = requests.post(url=url, json=payload, headers=headers)
    result = json.loads(response.text)
    unx = int(time.time())

    '''with open(f'{unx}.json', 'w') as file:
        json.dump(result, file, indent=4, ensure_ascii=False)'''

    audio_url = result.get('lovoai').get('audio_resource_url')
    r = requests.get(audio_url)
    file_name = 'subscribe.wav'

    with open(f'{file_name}.wav', 'wb') as file:
        file.write(r.content)


def main():
    tts(text='Ничего не знаю, все работает')


if __name__ == '__main__':
    main()
