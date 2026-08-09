import os

import pybiwenger
from dotenv import load_dotenv


print("==========================================")
print("          BORDALÁS IA v0.1")
print("==========================================")
print()

load_dotenv()

username = os.getenv("BIWENGER_USERNAME")
password = os.getenv("BIWENGER_PASSWORD")

print("Credenciales encontradas:", bool(username and password))
print("Intentando conectar con Biwenger...")
print()

try:
    pybiwenger.authenticate(username, password)

    print("Credenciales cargadas.")
    print("Creando cliente Biwenger...")

    client = pybiwenger.BiwengerBaseClient()

    print()
    print("==========================================")
    print("       CONEXIÓN CORRECTA")
    print("==========================================")
    print()
    print(f"Usuario: {client.user.name}")
    print(f"Liga: {client.user_league[0].name}")
    print()

except Exception as error:
    print()
    print("==========================================")
    print("          ERROR DE CONEXIÓN")
    print("==========================================")
    print()
    print(f"Tipo: {type(error).__name__}")
    print(f"Mensaje: {error}")