import logging
import threading
from multiprocessing import Queue
from threading import Lock
from typing import Optional

from src.adapter import AdapterPublisher
from src.adapter import AdapterSubscriber

logger = logging.getLogger(__name__)


class CommunicationSingleton(type):
    _instances: dict = {}
    _lock: Lock = Lock()

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


class MessageListener(metaclass=CommunicationSingleton):

    def __init__(self, msg_queue: Optional[Queue] = None, local_port: Optional[str] = None) -> None:
        if hasattr(self, "_initialized"):
            return
        if msg_queue is None or local_port is None:
            raise ValueError("First initialization requires queue and local port arguments")
        self.queue: Queue[str] | None = msg_queue
        self.local_port: str | None = local_port
        self.broadcast_listener: AdapterSubscriber.Reader = AdapterSubscriber.Reader(
            type_name="Broadcast", topic_name="broadcast", queue=msg_queue
        )
        self.local_listener: AdapterSubscriber.Reader = AdapterSubscriber.Reader(
            type_name="LocalTopic", topic_name=f"peer/{local_port}", queue=msg_queue
        )
        self._initialized = True


class MessageWriter(metaclass=CommunicationSingleton):

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self.peers: dict[str, AdapterPublisher.Writer] = {}
        self.broadcast_publisher: AdapterPublisher.Writer = AdapterPublisher.Writer(
            type_name="Broadcast", topic_name="broadcast"
        )
        self._initialized = True

    def wait_for_peers(self) -> None:
        self.broadcast_publisher.wait_discovery()

    def add_writer(self, remote_port: str) -> None:
        self.peers[remote_port] = AdapterPublisher.Writer(
            type_name=f"Topic{remote_port}", topic_name=f"peer/{remote_port}"
        )


def server_fun(queue: Queue, local_port: str) -> None:
    try:
        MessageListener(msg_queue=queue, local_port=local_port)
    except ValueError as e:
        logger.error("Failed to initialize MessageListener: %s", e)
        return
    threading.Event().wait()


def sendMsg(remote_server_address: str, msg: str) -> None:
    MessageWriter().peers[remote_server_address].write(message=msg)


def rcvMsg(queue: Queue) -> str:
    return queue.get()


def broadcastMsg(msg: str) -> None:
    MessageWriter().broadcast_publisher.write(message=msg)


def rcvMsgs(queue: Queue, no_of_messages_to_receive: int) -> list[str]:
    msgs: list[str] = []
    for _ in range(no_of_messages_to_receive):
        msgs.append(rcvMsg(queue))
    return msgs
