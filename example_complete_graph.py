import sys
from multiprocessing import Process, Queue
from src.message_api.msg_passing_api import *

# Each application instance shall have one broadcast topic and multiple other topics for peer to peer communication
# Broadcast topic shall be universal and shall be used to notify existing peers about new peers
# Interested peers shall accept new peer if interested in its topic
# Each peer shall keep list of topics which are topics of interest
# Topics of interest shall be used for direct communication between peers
# There shall be topics which will create sub-groups between peers (larger scale than direct topic and smaller scale than broadcast topic)
# Sub-groups are used to create logical groups inside one application domain
# All of the above implies that each application instance shall have multiple publishers and subscribers

# Steps towards goals above:
#   1. Expand publisher and subscriber class to accept custom topics
#   2. Instantiate broadcast publisher/subscriber
#   3. Try to exchange custom topics for direct communication
#   4. Instantiate publishers/subscribers for direct communication
#   5. Establish direct communication between peers


def main():
    # Parse command line arguments
    if len(sys.argv) != 3:
        print('Program usage: example_complete_graph proc_index number_of_proc')
        print('Example: If number_of_proc = 3, we must start 3 instances of program in 3 terminals:')
        print('example_complete_graph 0 3, example_complete_graph 1 3, and example_complete_graph 2 3')
        exit()
    
    # Process command line arguments
    proc_index = int( sys.argv[1] )
    number_of_proc = int( sys.argv[2] )

    # Create list of all ports
    allPorts: list[int] = [6000+i for i in range(number_of_proc)]
    
    # Set ports
    local_port: int =   allPorts[proc_index]
    remote_ports: list[int] = [x for x in allPorts if x != local_port]

    # Each instance must have one broadcast topic(handshake)
    # When broadcast topic is matched all instances that are interested in broadcasted topic will create local instance of writer for that topic
    broadcast_topic = "broadcast"
    # Format for instance topic will be peer/port_number (port number does not play role in this since everything is handled by middleware)
    instance_topic: str = "peer/" + str(local_port) 
    print(instance_topic)
    
    # Set the lst of the addresses of the peer node's servers
    remote_server_addresses: list[tuple[str, int]] = [('localhost', port) for port in remote_ports]
    
    # Send a message to the peer node and receive message from the peer node.
    # To exit send message: exit.
    print('Send a message to the peer node and receive message from the peer node.')
    print('To exit send message: exit.')

    queue : Queue[str] = Queue()

    commHandler = CommunicationHandler(msgQueue=queue)

    while True:
        command = int(input("Messaging method: \n\t1.Broadcast\nEnter method here:"))
        if command == 1:
            # Broadcast local topic to all peers in communication
            broadcastMsg(remote_server_addresses, instance_topic)
        else:
            print("No available commands for selected option")
    

if __name__ == '__main__':
    main()

