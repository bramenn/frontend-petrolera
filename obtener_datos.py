from typing import Dict
import requests

def obtener_todos_datos_activo_petroleo() -> Dict:

    data = {
        "query": {}
    }
    response = requests.post("https://h6bvbaq4wfay65fhv7luvhobye0ipeka.lambda-url.us-east-1.on.aws/", json=data)

    if response.status_code != 200:
        return {}
    
    return response.json()

def obtener_datos_activo_id_activo_petroleo(id_activo_petroleo) -> Dict:

    data = {
        "numero_datos": 100,
        "query": {"id_activo_petroleo": id_activo_petroleo}
    }
    response = requests.post("https://h6bvbaq4wfay65fhv7luvhobye0ipeka.lambda-url.us-east-1.on.aws/", json=data)


    if response.status_code != 200:
        print("Un error a ocurrdio: ", response.text)
        return {}
    
    return response.json()