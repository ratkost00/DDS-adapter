import sys
from multiprocessing import Process, Queue
from multiprocessing.connection import Client, Listener
from array import array
from src.adapter import AdapterPublisher
from src.adapter import AdapterSubscriber


broadcastPublisher = AdapterPublisher.Writer("Broadcast", "broadcast")
broadcastSubscriber = AdapterSubscriber.Reader("Broadcast", "broadcast")

def initBroadcast() -> None:
    broadcastPublisher.run()
    broadcastSubscriber.run()

def server_fun(local_port, queue):
    # Set the address of the local node's server
    local_server_address = ('localhost', local_port)
    
    # Send fixed message
    with Listener(local_server_address, authkey=b'Lets work together') as listener:
        
        while True:
            with listener.accept() as conn:
                #print('connection accepted from', listener.last_accepted)
                msg = conn.recv()
                #print(msg)
                
                # Forward msg to local node's process
                queue.put(msg)
                
                # Exit if msg is 'exit'
                if msg == 'exit':
                    break

def sendMsg(remote_server_address, msg):
    with Client(remote_server_address, authkey=b'Lets work together') as conn:
        conn.send(msg)

def rcvMsg(queue):
    return queue.get()

def broadcastMsg(list_of_remote_server_address, msg):
    broadcastPublisher.write(msg)

def rcvMsgs(queue, no_of_messages_to_receive):
    msgs = []
    
    for i in range(no_of_messages_to_receive):
        msgs.append( rcvMsg(queue) )
    
    return msgs
