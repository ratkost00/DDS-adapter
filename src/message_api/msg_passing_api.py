import sys
from multiprocessing import Process, Queue
from threading import Lock
from typing import Optional
from multiprocessing.connection import Client, Listener
from array import array
from src.adapter import AdapterPublisher
from src.adapter import AdapterSubscriber

# Make communication wrapper class
# Wrapper class should handle communication initialization and message queueing
# Local functions are used for communication handling (already wrappers)
# Once finished this singleton shall be placed in separate module
###############################################################################
class CommunicationSingleton(type):
    _instances = {}
    _lock : Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class CommunicationHandler(metaclass = CommunicationSingleton) :
    
    def __init__(self, msgQueue : Optional[Queue] = None) -> None:
        self.queue : Queue[str] | None = msgQueue
        self.peers : dict[str, AdapterPublisher.Writer] | None = None
        self.localSubscriber : AdapterSubscriber.Reader | None = None
        self.broadcastPublisher : AdapterPublisher.Writer = AdapterPublisher.Writer(topicName="Broadcast", topic="broadcast")
        self.broadcastSubscriber : AdapterSubscriber.Reader = AdapterSubscriber.Reader(topicName="Broadcast", topic="broadcast", queue=msgQueue)

        self.broadcastPublisher.run()
        # self.broadcastSubscriber.run()

    def initQueue(self, msgQueue : Queue):
        self.queue = msgQueue

    def initLocalListener(self, localTopic : str) -> None:
        self.localSubscriber = AdapterSubscriber.Reader(topicName="LocalTopic", topic=localTopic)
###############################################################################

def getCommunicationHandlerInstance() -> CommunicationHandler:
    return CommunicationHandler()

def server_fun(childConn, queue, instance_topic) -> None:
    commHandler = CommunicationHandler(msgQueue=queue)
    commHandler.initLocalListener(localTopic=instance_topic)

def sendMsg(remote_server_address, msg):
    with Client(remote_server_address, authkey=b'Lets work together') as conn:
        conn.send(msg)

def rcvMsg(queue):
    return queue.get()

def rcvAllMsgs(queue):
    msgs = []
    for i in range(queue.qsize()):
        msgs.append(queue.get())
    return msgs

# Argument list_of_remote_server_address is no longer needed
def broadcastMsg(list_of_remote_server_address, msg : str) -> None:
    # broadcastPublisher.write(msg)
    handler : CommunicationHandler = getCommunicationHandlerInstance()
    handler.broadcastPublisher.write(message=msg)

def rcvMsgs(queue, no_of_messages_to_receive):
    msgs = []
    
    for i in range(no_of_messages_to_receive):
        msgs.append( rcvMsg(queue) )
    
    return msgs
