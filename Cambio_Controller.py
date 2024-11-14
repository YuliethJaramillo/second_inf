import socket
import matplotlib.pyplot as plt
import ssl
import os
import json
import networkx as nx
from network import Network

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar el contenido del archivo routes.json
with open(os.path.join(BASE_DIR, 'routes.json'), 'r') as f:
    route_info = json.load(f)

# Archivo para almacenar la información de los routers
routers_info_file = os.path.join(BASE_DIR, 'routers_info.json')
shortest_paths_routers = os.path.join(BASE_DIR, 'shortest_paths.json')

# Crear el socket del servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 60000))
server_socket.listen(5)

# Configurar SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=os.path.join(BASE_DIR, "../certificate/server.crt"), keyfile=os.path.join(BASE_DIR, "../certificate/server.key"))
print("Servidor escuchando en el puerto 60000...")

def send_large_message(socket, message):
    message_bytes = message.encode('utf-8')
    message_length = len(message_bytes)
    socket.sendall(message_length.to_bytes(4, byteorder='big'))
    for i in range(0, message_length, 1024):
        socket.sendall(message_bytes[i:i+1024])

def save_router_info(router_info):
    if os.path.exists(routers_info_file):
        with open(routers_info_file, 'r') as f:
            all_routers_info = json.load(f)
    else:
        all_routers_info = {}
    router_id = str(router_info['router_id'])
    all_routers_info[router_id] = router_info
    with open(routers_info_file, 'w') as f:
        json.dump(all_routers_info, f, indent=4)

def find_path_dijkstra(network, source_name, destination_name, weight='weight'):
    try:
        path = nx.dijkstra_path(network.graph, source=source_name, target=destination_name, weight=weight)
        print(f"Shortest path from {source_name} to {destination_name}: {path}")
        return path
    except nx.NetworkXNoPath:
        print(f"No path exists between {source_name} and {destination_name}.")
        return None
    except KeyError as e:
        print(f"Node {e} not found in the network.")
        return None

def compute_all_paths_dijkstra(network):
    all_paths = dict(nx.all_pairs_dijkstra_path(network.graph))
    paths_data = {}
    for source, destinations in all_paths.items():
        for destination, path in destinations.items():
            paths_data[source] = paths_data.get(source, {})
            paths_data[source][destination] = {'source': source, 'path': path, 'destination': destination}
    with open(shortest_paths_routers, 'w') as f:
        json.dump(paths_data, f, indent=4)
    print("Rutas más cortas guardadas en shortest_paths.json")

def visualize_path(path, network):
    pos = nx.spring_layout(network.graph)
    nx.draw(network.graph, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10, font_weight='bold')
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_nodes(network.graph, pos, nodelist=path, node_color='red')
    nx.draw_networkx_edges(network.graph, pos, edgelist=path_edges, edge_color='red', width=2)
    plt.show()

network_nsf = Network()
with open(os.path.join(BASE_DIR, 'routers_info.json'), 'r') as f:
    data = json.load(f)
with open(os.path.join(BASE_DIR, 'routes.json'), 'r') as f:
    dataRoutes = json.load(f)

for key, router_info in data.items():
    router_id = str(router_info.get("router_id"))
    network_nsf.add_node(key, router_id)
    routes_with_cost = [{"dst": routes["dst"], "cost": routes["cost"]} for routes in dataRoutes["routes"] if routes["src"] == router_id]
    for route in routes_with_cost:
        network_nsf.add_link(router_id, route['dst'], route['cost'])

print("Calculando rutas más cortas entre routers...")
compute_all_paths_dijkstra(network_nsf)

while True:
    client_socket, addr = server_socket.accept()
    print(f"Conexión desde {addr}")
    try:
        secure_socket = context.wrap_socket(client_socket, server_side=True)
        data = secure_socket.recv(1024).decode('utf-8')
        print(f"Recibido: {data}")
        router_info = json.loads(data)
        save_router_info(router_info)
        response = json.dumps(route_info)
        send_large_message(secure_socket, response)
    except ssl.SSLError as ssl_err:
        print(f"Error SSL al conectar: {ssl_err}")
    except Exception as e:
        print(f"Error al conectar: {e}")
    finally:
        secure_socket.close()
