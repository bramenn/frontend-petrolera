import json
from typing import Dict, List

import pandas as pd
from fastapi import APIRouter, Request

router = APIRouter()

lista_datos: List[Dict] = [
    {
        "id_activo_petroleo": 1,
        "timestamp": 0,
        "presion": 0,
        "flujo": 0,
        "temperatura": 0,
        "almacenamiento_disponible": 0,
        "longitud": 0,
        "latitud": 0,
    }
]
df = pd.DataFrame(lista_datos)


@router.post("/", status_code=200)
async def recibir_datos_real_time(request: Request):
    global lista_datos
    global df
    sns_request: dict = json.loads(await request.body())

    if sns_request.get("Type") == "SubscriptionConfirmation":
        print(
            "Debes aceptar la subcripción de la sns por: ",
            sns_request.get("SubscribeURL"),
        )
        return
    elif sns_request.get("Type") == "Notification":
        try:
            datos_nuevos: dict = json.loads(sns_request.get("Message"))
            lista_datos.append(datos_nuevos)
            df.loc[len(df.index)] = datos_nuevos
        except Exception as e:
            print("No cumple con el formato esperado:", e)
            return
