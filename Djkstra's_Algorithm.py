import socket
import json
import threading
from network import Network
from Controller import Controller
import networkx as nx
import matplotlib.pyplot as plt
import mysql.connector

# Initialize the network
nsfnet = Network()
controller = Controller()
network_initialized = False

# Default nodes and links
def initialize_network():
    """
    Initializes the default nodes and links in the network.
    """
    nsfnet.add_node(1, 'WA', node_type='Router')
    nsfnet.add_node(2, 'CA1', node_type='Router')
    nsfnet.add_node(3, 'CA2', node_type='Router')
    nsfnet.add_node(4, 'UT', node_type='Router')
    nsfnet.add_node(5, 'CO', node_type='Router')
    nsfnet.add_node(6, 'TX', node_type='Router')
    nsfnet.add_node(7, 'NE', node_type='Router')
    nsfnet.add_node(8, 'IL', node_type='Router')
    nsfnet.add_node(9, 'PA', node_type='Router')
    nsfnet.add_node(10, 'GA', node_type='Router')
    nsfnet.add_node(11, 'MI', node_type='Router')
    nsfnet.add_node(12, 'NY', node_type='Router')
    nsfnet.add_node(13, 'NJ', node_type='Router')
    nsfnet.add_node(14, 'DC', node_type='Router')

    # Add the Links between Nodes.
    nsfnet.add_link(1, 2, 2100)  # Link With 2100 Gbps bandwidth.
    nsfnet.add_link(1, 3, 3000)  # Link With 3000 Gbps bandwidth.
    nsfnet.add_link(1, 8, 4800)  # Link With 4800 Gbps bandwidth.
    nsfnet.add_link(2, 3, 1200)  # Link With 1200 Gbps bandwidth.
    nsfnet.add_link(2, 4, 1500)  # Link With 1500 Gbps bandwidth.
    nsfnet.add_link(3, 6, 3600)  # Link With 3600 Gbps bandwidth.
    nsfnet.add_link(4, 5, 1200)  # Link With 1200 Gbps bandwidth.
    nsfnet.add_link(4, 11, 3900)  # Link With 3900 Gbps bandwidth.
    nsfnet.add_link(5, 6, 2400)  # Link With 2400 Gbps bandwidth.
    nsfnet.add_link(5, 7, 1200)  # Link With 1200 Gbps bandwidth.
    nsfnet.add_link(6, 10, 200)  # Link With 2100 Gbps bandwidth.
    nsfnet.add_link(6, 14, 3600)  # Link With 3600 Gbps bandwidth.
    nsfnet.add_link(7, 8, 1500)  # Link With 1500 Gbps bandwidth.
    nsfnet.add_link(7, 10, 2700)  # Link With 2700 Gbps bandwidth.
    nsfnet.add_link(8, 9, 1500)  # Link With 1500 Gbps bandwidth.
    nsfnet.add_link(9, 10, 1500)  # Link With 1500 Gbps bandwidth.
    nsfnet.add_link(9, 12, 600)  # Link With 600 Gbps bandwidth.
    nsfnet.add_link(9, 13, 600)  # Link With 600 Gbps bandwidth.
    nsfnet.add_link(11, 12, 1200)  # Link With 1200 Gbps bandwidth.
    nsfnet.add_link(11, 13, 1500)  # Link With 1200 Gbps bandwidth.
    nsfnet.add_link(12, 14, 600)  # Link With 600 Gbps bandwidth.
    nsfnet.add_link(13, 14, 300)  # Link With 600 Gbps bandwidth.


def display_network():
    """
    Displays and visualizes the network whenever it's needed.
    """
    while True:
        input("Press Enter to display and visualize the network:")
        #nsfnet.display_network()
        nsfnet.visualize_network()
        visualize_shortest_path(nsfnet, 'Client1', 'Client2')

# Start the user input listener in a separate thread
input_thread = threading.Thread(target=display_network)
input_thread.daemon = True
input_thread.start()


# Initialize server
HOST = '127.0.0.1'
PORT = 65432

# Mapping of connection order to node names
node_map = {0: 'WA', 1: 'CA1', 2: 'CA2', 3: 'UT', 4: 'CO', 5: 'TX', 6: 'NE', 7: 'IL', 8: 'PA', 9: 'GA', 10: 'MI',
            11: 'NY', 12: 'NJ', 13: 'DC'}

connection_details = {}


def update_node_details():
    """
    Updates the Json file that stores the IP and Port of the nodes in the network.
    """
    with open('node_details.json', 'w') as f:
        json.dump(connection_details, f)

def conectDB():
    # Conectar a la base de datos
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='short_path'
    )
    cursor = connection.cursor()
    return cursor, connection

def update_shortest_paths():
    """
    Updates the shortest paths between nodes in the database.
    """
    all_paths = dict(nx.all_pairs_dijkstra_path(nsfnet.graph))
    node_ip_port_map = {}

    # Leer los detalles de los nodos
    with open('node_details.json', 'r') as f:
        node_details = json.load(f)
        for node_name, details in node_details.items():
            ip = details.get('ip')
            port = details.get('port')
            if ip and port:
                node_ip_port_map[node_name] = f"{ip}:{port}"

    shortest_paths_with_ip_port = {}
    for source, destinations in all_paths.items():
        source_identifier = node_map.get(source, source)
        shortest_paths_with_ip_port[source_identifier] = {}
        for destination, path in destinations.items():
            dest_identifier = node_map.get(destination, destination)
            shortest_paths_with_ip_port[source_identifier][dest_identifier] = [
                node_ip_port_map.get(node, node) for node in path]

    # Conectar a la base de datos
    """connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='short_path'
    )
    cursor = connection.cursor()"""
    cursor,connection = conectDB()

    # Limpiar datos antiguos
    cursor.execute("DELETE FROM paths")
    cursor.execute("ALTER TABLE paths AUTO_INCREMENT = 1;")

    # Insertar nuevos datos
    for source, destinations in shortest_paths_with_ip_port.items():
        for destination, path in destinations.items():
            path_str = ','.join(path)
            destination_str = ''.join(destination)
            source_str = ''.join(source)
            cursor.execute("INSERT INTO paths (destination, best_path, source) VALUES (%s, %s, %s)",
                           (destination_str, path_str,source_str))

    # Confirmar cambios y cerrar conexión
    connection.commit()
    cursor.close()
    connection.close()

    get_data_DB()



def start_server():
    """
    Starts the TCP server for handling incoming connections from routers and clients.

    This function initializes the network if not already initialized and listens for incoming connections. It assigns
    their IP addresses and ports to the nodes of the network as they connect, updates the network topology, and
    handles disconnections.

    """
    get_data_DB()
    global network_initialized
    if not network_initialized:
        initialize_network()
        network_initialized = True

    # Create a TCP server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the address and port
    server_socket.bind((HOST, PORT))
    # Listen for incoming connections
    server_socket.listen()
    print(f"Server started on {HOST}:{PORT}")

    # Counter for tracking the number of connections
    connection_count = 0


    # Main server loop
    while True:
        # Accept a new connection
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        if connection_count < 14:  # We only have 14 nodes
            node_name = node_map[connection_count]
            nsfnet.nodes[connection_count + 1].ip = addr[0]
            nsfnet.nodes[connection_count + 1].port = addr[1]
            connection_details[node_name] = {'ip': addr[0], 'port': addr[1]}
            print(f"Router {node_name} assigned IP {addr[0]} and Port {addr[1]}")
            update_node_details()
            update_shortest_paths()
        elif connection_count == 14:
            # Add the first client node for the fifteenth connection
            nsfnet.add_node(15, 'Client1', node_type='Client')
            nsfnet.add_link(15, 1, 100)
            print("Client1 added to the network")
            # Assign IP and port to the new node
            nsfnet.nodes[5].ip = addr[0]
            nsfnet.nodes[5].port = addr[1]
            connection_details['Client1'] = {'ip': addr[0], 'port': addr[1]}
            update_node_details()
            update_shortest_paths()
            print(f"Client1 assigned IP {addr[0]} and Port {addr[1]}")
        elif connection_count == 15:
            # Add the second client node for the sixth connection
            nsfnet.add_node(16, 'Client2', node_type='Client')
            nsfnet.add_link(16, 14, 100)
            print("Client2 added to the network")
            # Assign IP and port to the new node
            nsfnet.nodes[6].ip = addr[0]
            nsfnet.nodes[6].port = addr[1]
            connection_details['Client2'] = {'ip': addr[0], 'port': addr[1]}
            update_node_details()
            update_shortest_paths()
            print(f"Client2 assigned IP {addr[0]} and Port {addr[1]}")
            print("No more nodes available for connection.")
        else:
            print("No more nodes available for connection.")

        # Increment the connection count
        connection_count += 1

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client_router, args=(conn,))
        client_thread.start()



# Function to handle the client
def handle_client_router(conn):
    """
    Handles communication with a client.

    This function mainly handles disconnections by removing the associated node from the network.

    Args:
    - conn: The socket connection with the client.

    """
    router_name = None
    try:
        while True:
            # Receive data from the client
            data = conn.recv(1024).decode()
            if not data:
                break
            controller.handle_connection(conn, data)
            print(f"Received data from client {conn.getpeername()}: {data}")
            # Echo the received data back to the client
            conn.sendall(data.encode())
    except Exception as e:
        print(f"Connection lost with client {conn.getpeername()[0]}, {conn.getpeername()[1]}")
        # Determine the router associated with the lost connection
        for name, details in connection_details.items():
            if details['ip'] == conn.getpeername()[0] and details['port'] == conn.getpeername()[1]:
                router_name = name
                break
        # Remove the associated node from the network
        if router_name:
            node_id = next(node_id for node_id, node in nsfnet.nodes.items() if node.name == router_name)
            nsfnet.remove_node(node_id)
            print(f"Node {router_name} associated with router {conn.getpeername()[0]}:{conn.getpeername()[1]} removed from the network")
            update_shortest_paths()
            del connection_details[router_name]
            update_node_details()
        # Close the client socket
        conn.close()


# Additional functionality for adding or removing nodes
def add_node(node_id, name, node_type='Router'):
    """
    Add a node to the network.

    This function adds a new node to the network with the specified ID, name, and node type. It then calls the
    corresponding functions to update the json files

    Args:
    - node_id: The ID of the node to be added.
    - name: The name of the node.
    - node_type: The type of the node (default is 'Router').

    """
    nsfnet.add_node(node_id, name, node_type=node_type)
    update_shortest_paths()


def remove_node(node_id):
    """
    Remove a node from the network.

    This function removes a node from the network based on its ID. It also updates the Json files.

    Args:
    - node_id: The ID of the node to be removed.

    """
    nsfnet.remove_node(node_id)
    update_shortest_paths()


def find_shortest_path(network, source_name, destination_name, weight='weight'):
    """
    Find the shortest path between two nodes in the network.

    This function calculates the shortest path between two nodes in the network using either Dijkstra's algorithm or
    Bellman-Ford algorithm based on the operation specified in the 'Operation.json' file.

    Args:
    - network: The network graph.
    - source_name: The name of the source node.
    - destination_name: The name of the destination node.
    - weight: The weight attribute used for calculating the shortest path.

    Returns:
    - path: The shortest path between the source and destination nodes, or None if no path exists.

    """
    global network_initialized
    if not network_initialized:
        initialize_network()
        network_initialized = True

        try:
            path = nx.dijkstra_path(network.graph, source=source_name, target=destination_name, weight=weight)
            print(f"Shortest path from {source_name} to {destination_name} using Dijkstra: {path}")
            return path
        except nx.NetworkXNoPath:
            print(f"No path exists between {source_name} and {destination_name}.")
            return None


def compute_all_shortest_paths(network):
    """
    Compute and print all shortest paths in the network.

    This function computes and prints all shortest paths in the network using either Dijkstra's algorithm or
    Bellman-Ford algorithm based on the operation specified in the 'Operation.json' file.

    Args:
    - network: The network graph.

    """
    global network_initialized
    if not network_initialized:
        initialize_network()
        network_initialized = True

    all_paths = dict(nx.all_pairs_dijkstra_path(network.graph))


    for source, destinations in all_paths.items():
        for destination, path in destinations.items():
            print(f"Shortest path from {source} to {destination}: {path}")
    update_shortest_paths()


# This function is not used right now, but don't remove it, it could be used later
def visualize_shortest_path(network, source_name, destination_name):
    """
    Visualize the shortest path between two nodes in the network.

    This function visualizes the shortest path between two nodes in the network calculated by using either Dijkstra's
    algorithm or Bellman-Ford algorithm based on the operation specified in the 'Operation.json' file.

    Args:
    - network: The network graph.
    - source_name: The name of the source node.
    - destination_name: The name of the destination node.

    """
    global network_initialized
    if not network_initialized:
        initialize_network()
        network_initialized = True

    path = nx.dijkstra_path(network.graph, source=source_name, target=destination_name)

    pos = nx.spring_layout(network.graph)
    nx.draw(nsfnet.graph, pos, with_labels=True, node_color='gold', node_size=500, font_size=10,
            font_weight='bold')
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_nodes(nsfnet.graph, pos, nodelist=path, node_color='red')
    nx.draw_networkx_edges(nsfnet.graph, pos, edgelist=path_edges, edge_color='red', width=2)
    plt.show()

def get_data_DB():
    #print("base de datos Datos")
    cursor, connection = conectDB()  # Obtener cursor y conexión
    cursor = connection.cursor(dictionary=True)  # Crear el cursor usando la conexión
    cursor.execute("SELECT * FROM paths")
    row = cursor.fetchall()

    cursor.close()
    connection.close()

    # Guardar los datos en un archivo JSON
    with open('data_paths_router.json', 'w') as f:
        json.dump(row, f)

    #print("Datos guardados en data_paths_router.json")


# Compute and print the shortest path from NodeA to NodeC
print("------------")
find_shortest_path(nsfnet, 'DC', 'MI')
# Visualize the shortest path from Node 1 to Node 2. Commented for now.
 #visualize_shortest_path(nsfnet, 'UT', 'TX')

print("------------")
# Compute and print all shortest paths in the network
compute_all_shortest_paths(nsfnet)
#get_data_DB()


# Main loop
if __name__ == '__main__':
    start_server()
