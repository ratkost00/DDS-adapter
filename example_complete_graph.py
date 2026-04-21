import sys
import re
import queue as queue_module
from multiprocessing import Process, Queue
from src.message_api.msg_passing_api import MessageWriter, server_fun, rcvMsg, broadcastMsg, sendMsg

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


def acceptConn(localTopic: str, receivedTopic: str) -> bool:
    if localTopic == receivedTopic:
        return False
    pattern: re.Pattern[str] = re.compile(r"^peer/\d+$")
    return bool(pattern.match(receivedTopic))


def main():
    if len(sys.argv) != 3:
        print('Program usage: example_complete_graph proc_index number_of_proc')
        print('Example: If number_of_proc = 3, we must start 3 instances of program in 3 terminals:')
        print('example_complete_graph 0 3, example_complete_graph 1 3, and example_complete_graph 2 3')
        sys.exit(1)

    try:
        proc_index = int(sys.argv[1])
        number_of_proc = int(sys.argv[2])
    except ValueError:
        print("Error: proc_index and number_of_proc must be integers")
        sys.exit(1)

    allPorts: list[int] = [6000 + i for i in range(number_of_proc)]
    local_port: int = allPorts[proc_index]

    instance_topic: str = "peer/" + str(local_port)
    print(instance_topic)

    q: Queue = Queue()
    commProcess = Process(target=server_fun, args=(q, local_port))
    commProcess.start()

    writer = MessageWriter()
    writer.wait_for_peers()
    peers: list[str] = []

    try:
        while True:
            try:
                command = int(input("Messaging method: \n\t1.Broadcast\n\t2.Receive message\n\t3.Receive all messages\n\t4.Send direct message\nEnter method here: "))
            except ValueError:
                print("Invalid input: please enter a number")
                continue

            if command == 1:
                broadcastMsg(instance_topic)
            elif command == 2:
                msg: str = rcvMsg(queue=q)
                peer_port = msg.split('/')[1]
                if acceptConn(instance_topic, msg) and peer_port not in peers:
                    writer.add_writer(peer_port)
                    peers.append(peer_port)
                    print("Connection with " + msg + " accepted")
                else:
                    print("Connection with " + msg + " declined")
            elif command == 3:
                print("Queued messages: ")
                pending = []
                while True:
                    try:
                        pending.append(q.get_nowait())
                    except queue_module.Empty:
                        break
                for msg in pending:
                    peer_port = msg.split('/')[1]
                    if acceptConn(instance_topic, msg) and peer_port not in peers:
                        writer.add_writer(peer_port)
                        peers.append(peer_port)
                        print("Connection with " + msg + " accepted")
                    else:
                        print("Connection with " + msg + " declined")
            elif command == 4:
                if not peers:
                    print("No connected peers")
                    continue
                print("Connected peers: ")
                for i, peer in enumerate(peers):
                    print(f"\t{i}: peer/{peer}")
                try:
                    selection = int(input("Select peer: "))
                    if selection < 0 or selection >= len(peers):
                        print("Invalid selection")
                        continue
                except ValueError:
                    print("Invalid input: please enter a number")
                    continue
                sendMsg(peers[selection], f"Direct message from {instance_topic}")
            else:
                print("No available commands for selected option")
    finally:
        commProcess.terminate()
        commProcess.join()


if __name__ == '__main__':
    main()
