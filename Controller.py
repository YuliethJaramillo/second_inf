
import json


class Controller:
    """
    A class to represent a network controller.

    Attributes:
    - host (str): The host address to bind the server socket.
    - port (int): The port number to bind the server socket.
    - server_socket: The server socket object.
    - node_details (dict): A dictionary containing node details.
    - shortest_paths (dict): A dictionary containing shortest paths.
    - connection_order (list): A list containing the order of client connections.

    Methods:
    - __init__(self, host, port): Initializes a Controller object with the given attributes.
    - start(self): Starts the Controller server to listen for incoming connections.
    - handle_connection(self, client_socket): Handles communication with a client.
    - extract_router_message(self, data): Extracts router address and message from received data.
    - load_node_details(self): Loads node details from the 'node_details.json' file.
    - load_shortest_paths(self): Loads shortest paths from the 'shortest_paths.json' file.
    - get_sender_type(self): Gets the type of the sender based on the connection order.
    - send_message_to_router(self, router_address, message): Sends a message to a router.
    """

    def __init__(self):

        self.node_details = self.load_node_details()
        self.shortest_paths = self.load_shortest_paths()
        self.connection_order = []

    def handle_connection(self,client_socket,data):

        sender_label = self.get_sender_type()
        try:

            shortest_paths = self.load_shortest_paths()
            print(f"Received data from {sender_label}: {data}")

            if sender_label.startswith("Client"):
                # Determine destination client
                destination_client_label = "Client1" if sender_label == "Client2" else "Client2"
                # Check if shortest path exists
                if sender_label in shortest_paths and destination_client_label in shortest_paths[sender_label]:
                    # Get the shortest path (excluding sender)
                    path = shortest_paths[sender_label][destination_client_label][1:]
                    print("Shortest path:", path)
                    # Add headers to the message
                    headers = ','.join(path)
                    message = f"{headers},{data}"
                    print("Modified message with headers:", message)
                    # Send message to the first router
                    self.send_message_to_router(path[0], message)
                else:
                    print(f"No shortest path found between {sender_label} and {destination_client_label}.")
            else:  # Message received from a router
                router_address, message = self.extract_router_message(data)
                print(f"Received data from {sender_label}: {message}")
                # Send the message back to the first router
                self.send_message_to_router(router_address, message)
        except Exception as e:
            print(f"Connection lost with {sender_label}")
            # Remove the disconnected client from the connection_order list
            self.connection_order = [(socket, address) for socket, address in self.connection_order
                                     if socket != client_socket]
            client_socket.close()

    def extract_router_message(self,data):   ## FUNCION PARA ROURER, OBTENER DATOS DEL ROUETER COMO LA DIRECCION Y MENSAJE
        """
        Extracts router address and the message from received data.

        Parameters:
        - data (str): The received data containing router address and the message.

        Returns:
        - router_address (str): The address of the router.
        - message_with_headers (str): The message with headers.
        """
        # Split the message into router address and message with headers
        router_address, message_with_headers = data.split(",", 1)
        return router_address, message_with_headers

    def load_node_details(self):
        """
        Loads node details from the 'node_details.json' file.

        Returns:
        - node_details (dict): A dictionary containing node details.
        """
        with open('node_details.json', 'r') as f:
            return json.load(f)

    def load_shortest_paths(self):
        """
        Loads shortest paths from the 'shortest_paths.json' file.

        Returns:
        - shortest_paths (dict): A dictionary containing shortest paths.
        """
        with open('data_paths_router.json', 'r') as f:
            return json.load(f)

    def get_sender_type(self):
        """
        Identifies the connection from either a client or a router. The way it does it is by doing an element to element
        Comparison between the connection_order list and the node_details.json file, since the routers/clients connect
        to both servers at the same time, they gey get stored in the same order, so by comparing the order of arrival in
        the list to the elements of the Json file, the controller gets to know the type of connection is handling.

        Returns:
        - sender_type (str): The type of the sender.
        """
        sender_index = len(self.connection_order) - 1
        print(sender_index)
        if sender_index < len(self.node_details):
            return list(self.node_details.keys())[sender_index]
        return "Unknown"

    def send_message_to_router(self, router_address, message):
        """
        Sends a message to a router based on the headers added to the message.

        Parameters:
        - router_address (str): The address of the router.
        - message (str): The message to be sent.
        """
        # Load node details from JSON
        node_details = self.load_node_details()

        # Find the position of the router in the node details
        router_position = None
        for position, details in enumerate(node_details.values()):
            if details["ip"] == router_address.split(':')[0] and details["port"] == int(router_address.split(':')[1]):
                router_position = position
                break

        if router_position is not None:
            # Use the socket corresponding to the router position in the connection order
            router_socket, _ = self.connection_order[router_position]
            # Send the message to the router
            router_socket.sendall(message.encode())
            print(f"Sending message to router {router_address}: {message}")
        else:
            print(f"Router {router_address} not found in node details.")

