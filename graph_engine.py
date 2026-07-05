import heapq


def dijkstra(grafo, inicio, destino):
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[inicio] = 0
    padres = {nodo: None for nodo in grafo}
    cola_prioridad = [(0, inicio)]

    while cola_prioridad:
        distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)
        if distancia_actual > distancias[nodo_actual]: continue
        if nodo_actual == destino: break

        for vecino, peso in grafo[nodo_actual]:
            distancia = distancia_actual + peso
            if distancia < distancias[vecino]:
                distancias[vecino] = distancia
                padres[vecino] = nodo_actual
                heapq.heappush(cola_prioridad, (distancia, vecino))

    camino = []
    nodo_paso = destino
    while nodo_paso is not None:
        camino.append(nodo_paso)
        nodo_paso = padres[nodo_paso]
    
    camino.reverse() 
    return distancias[destino], camino



def orden_recoleccion_voraz(grafo, punto_inicio, lista_productos):
    ruta_completa = []
    distancia_total = 0
    nodo_actual = punto_inicio
    pendientes = lista_productos

    while pendientes:
        nodo_mas_cercano = None
        menor_distancia = float('inf')
        mejor_camino = []

        for producto in pendientes:
            dist, camino = dijkstra(grafo, nodo_actual, producto)
            if dist < menor_distancia:
                menor_distancia = dist
                nodo_mas_cercano = producto
                mejor_camino = camino
        
        if mejor_camino:
            if ruta_completa:
                ruta_completa.extend(mejor_camino[1:])
            else:
                ruta_completa.extend(mejor_camino)
                
            distancia_total += menor_distancia
            nodo_actual = nodo_mas_cercano
            pendientes.remove(nodo_mas_cercano) 
    return distancia_total, ruta_completa



def procesar_pedido_por_zonas(grafo, punto_inicio, lista_productos):
    zonas = {}
    for producto in lista_productos:
        
        partes = producto.split('_')
        if len(partes) >= 4:
            zona_letra = partes[3]
            if zona_letra not in zonas:
                zonas[zona_letra] = []
            # Guardamos la base del nodo sin la zona (ej. RACK_62_20)
            zonas[zona_letra].append(producto[:-2])

    zonas_ordenadas = sorted(zonas.keys())
    ruta_global = []
    distancia_global = 0
    nodo_actual = punto_inicio

    for zona in zonas_ordenadas:
        productos_en_zona = zonas[zona]
        distancia_zona, ruta_zona = orden_recoleccion_voraz(grafo, nodo_actual, productos_en_zona)
        distancia_global += distancia_zona
        
        if ruta_zona:
            if ruta_global:
                ruta_global.extend(ruta_zona[1:])
            else:
                ruta_global.extend(ruta_zona)
            nodo_actual = ruta_zona[-1]

    return distancia_global, ruta_global

