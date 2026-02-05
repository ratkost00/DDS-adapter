import sys
import re
from multiprocessing import Process, Queue, Pipe
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

def acceptConn(localTopic : str, receivedTopic : str)  -> bool:
    if localTopic == receivedTopic:
        return False
    else:
        pattern : re.Pattern[str] = re.compile(r"^peer/\d+$")
        return bool(pattern.match(receivedTopic))

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

    instance_topic: str = "peer/" + str(local_port) 
    print(instance_topic)
    
    # Set the lst of the addresses of the peer node's servers
    remote_server_addresses: list[tuple[str, int]] = [('localhost', port) for port in remote_ports]

    queue : Queue = Queue()
    parentConn , childConn = Pipe()
    commProcess = Process(target=server_fun, args=(childConn, queue, instance_topic,))
    commProcess.start()
    peers : list[str] = []

    while True:
        command = int(input("Messaging method: \n\t1.Broadcast\n\t2.Receive message\n\t3.Receive all messages\n\t4.Send direct message\nEnter method here: "))
        if command == 1:
            # Broadcast local topic to all peers in communication
            broadcastMsg(parentConn, instance_topic)
        elif command == 2:
            msg : str = rcvMsg(queue=queue)
            if acceptConn(instance_topic, msg):
                print("Connection with " + msg + " accepted")
            else:
                print("Connection with " + msg + " declined")
        elif command == 3:
            print("Queued messages: ")
            for msg in rcvAllMsgs(queue=queue):
                if acceptConn(instance_topic, msg):
                    print("Connection with " + msg + " accepted")
                    peers.append(msg)
                    parentConn.send(["accept", msg])
                else:
                    print("Connection with " + msg + " declined")
        elif command == 4:
            print("Connected peers: ")
            for peer in peers:
                print("\t " + peer)
            selection = int(input("Select peer: "))
            mess: str = "message from " + instance_topic
            parentConn.send(["direct", peers[selection], mess])
        else:
            print("No available commands for selected option")
        
    commProcess.join()    

if __name__ == '__main__':
    main()

