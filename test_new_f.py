import subprocess

def toggle_bluetooth(state):
    try:
        if state == "on":
            # Включаем Bluetooth
            subprocess.run(["powershell", "-Command", "Get-PnpDevice | Where-Object { $_.FriendlyName -like '*Bluetooth*' } | Enable-PnpDevice -Confirm:$false"], check=True)
            print("Bluetooth включен")
        elif state == "off":
            # Отключаем Bluetooth
            subprocess.run(["powershell", "-Command", "Get-PnpDevice | Where-Object { $_.FriendlyName -like '*Bluetooth*' } | Disable-PnpDevice -Confirm:$false"], check=True)
            print("Bluetooth отключен")
        else:
            print("Укажите 'on' или 'off'")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка: {e}")

# Включить Bluetooth
toggle_bluetooth("on")