import pandas as pd

def crear_lista_adyacencia(ruta_aristas):
    df_aristas = pd.read_csv(ruta_aristas)
    adyacencia = {}
    for _, row in df_aristas.iterrows():
        origen = str(row['source'])
        destino = str(row['target'])
        peso = round(float(row['weight']), 2) 
        
        if origen not in adyacencia: adyacencia[origen] = []
        if destino not in adyacencia: adyacencia[destino] = []
            
        adyacencia[origen].append((destino, peso))
        adyacencia[destino].append((origen, peso))
    return adyacencia