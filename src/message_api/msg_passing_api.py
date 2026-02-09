import sys
import time
from multiprocessing import Queue
from threading import Lock
from typing import Optional
from src.adapter import AdapterPublisher
from src.adapter import AdapterSubscriber
class CommunicationSingleton(type):
    _instances = {}
    _lock : Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls in cls._instances:
                return cls._instances[cls]
            try:
                instance = super().__call__(*args, **kwargs)
            except Exception:
                if cls in cls._instances:
                    del cls._instances[cls]
                raise
            cls._instances[cls] = instance
            return instance
    

class MessageListener(metaclass = CommunicationSingleton) :

    def __init__(self, msg_queue : Optional[Queue] = None, local_port : Optional[str] = None) -> None:
        print(msg_queue, local_port)
        if not hasattr(self, "_initialized"):
            if msg_queue is None or local_port is None:
                raise ValueError("First initialization requires queue and local port arguments")

        print("Creating object")
        self.queue : Queue[str] | None = msg_queue
        self.local_port : str | None = local_port
        self.broadcast_listener : AdapterSubscriber.Reader = AdapterSubscriber.Reader(topicName="Broadcast", topic="broadcast", queue=msg_queue)
        self.local_listener : AdapterSubscriber.Reader = AdapterSubscriber.Reader(topicName="LocalTopic", topic=f"peer/{local_port}", queue=msg_queue)
        self._initialized = True

class MessageWriter(metaclass = CommunicationSingleton) :
    def __init__(self) -> None:
        self.peers : dict[str, AdapterPublisher.Writer] = {}
        self.broadcast_publisher : AdapterPublisher.Writer = AdapterPublisher.Writer(topicName="Broadcast", topic="broadcast")

        self.broadcast_publisher.run()

    def add_writer(self, remote_port : str) :
        self.peers[remote_port] = AdapterPublisher.Writer(topicName=f"Topic{remote_port}", topic=f"peer/{remote_port}")


def server_fun(queue, local_port) -> None:
    try:
        listener : MessageListener = MessageListener(msg_queue=queue, local_port=local_port)
    except ValueError as e:
        print(f"\nRaised value error: {e}")

    while True:
        time.sleep(4)
        pass

def sendMsg(remote_server_address, msg):
    MessageWriter().peers[remote_server_address].write(message=msg)
    pass

def rcvMsg(queue):
    return queue.get()

# Argument list_of_remote_server_address is no longer needed
def broadcastMsg(list_of_remote_server_address, msg : str) -> None:
    MessageWriter().broadcast_publisher.write(message=msg)
    

def rcvMsgs(queue, no_of_messages_to_receive):
    msgs : list[str] = []    
    for i in range(no_of_messages_to_receive):
        msgs.append( rcvMsg(queue) )
    
    return msgs
