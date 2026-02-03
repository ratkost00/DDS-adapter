import sys
from multiprocessing import Process, Queue
from src.message_api.msg_passing_api import *

# Each application instance shall have one boradcast topic and multiple other topics for peer to peer communication
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

    # Creat list of all pors
    allPorts = [6000+i for i in range(number_of_proc)]
    
    # Set ports
    local_port =   allPorts[proc_index]
    remote_ports = [x for x in allPorts if x != local_port]

    # Each instance must have one broadcast topic(hadnshake)
    # When broadcast topic is matched all instances that are interested in broadcasted topic will create local instance of writer for that topic
    boradcast_topic = "broadcast"
    # Format for instance topic will be peer/port_number (port number does not play role in this since everything is handled by middleware)
    instance_topic = "peer/" + str(local_port) 
    print(instance_topic)
    
    
    # Create queue for messages from the local server
    queue = Queue()
    
    # Create and start server process
    server = Process(target=server_fun, args=(local_port,queue))
    server.start()
    
    # Set the lst of the addresses of the peer node's servers
    remote_server_addresses = [('localhost', port) for port in remote_ports]
    
    # Send a message to the peer node and receive message from the peer node.
    # To exit send message: exit.
    print('Send a message to the peer node and receive message from the peer node.')
    print('To exit send message: exit.')

    for addr in remote_server_addresses:
        print(addr)
    
    while True:
        # Input message
        msg = input('Enter message: ')
        #print('Message sent: %s \n' % (msg))
        
        if msg == 'exit':
            sendMsg( ('localhost', local_port), 'exit')
            break
        
        # Send message to peer node's servers
        broadcastMsg(remote_server_addresses, msg)
        
        # Get message from local node's server
        msgs = rcvMsgs(queue, number_of_proc - 1)
        print('Messages received:', msgs)
    
    # Join with server process
    server.join()
    
    # Delete queue and server
    del queue
    del server

if __name__ == '__main__':
    main()

