import os
import time
import datetime



pathfile = os.path.join("\\\\10.147.10.11\RadioComercial\Programacao","")

import requests
url = "https://www.youtube.com"

if requests.get(pathfile).status_code == 200:
    print("O servidor está disponível.")
else:
    print("O servidor está indisponível.")