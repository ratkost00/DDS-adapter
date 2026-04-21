"""
Adapter Subscriber
"""
import logging
import signal
import threading

import fastdds
from src.library.Adapter import *
from multiprocessing import Queue
from typing import Optional

logger = logging.getLogger(__name__)


class ReaderListener(fastdds.DataReaderListener):

    def __init__(self, queue: Optional[Queue] = None) -> None:
        super().__init__()
        self.queue: Optional[Queue[str]] = queue

    def on_data_available(self, reader) -> None:
        info = fastdds.SampleInfo()
        data = Adapter()
        reader.take_next_sample(data, info)
        if not info.valid_data:
            return
        logger.debug("Received %s", data.message())
        if self.queue is not None:
            self.queue.put(data.message())


class Reader:

    def __init__(self, type_name: str, topic_name: str, queue: Optional[Queue] = None):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)
        if self.participant is None:
            raise RuntimeError("Failed to create DomainParticipant")

        self.topic_data_type = AdapterPubSubType()
        self.topic_data_type.set_name(type_name)
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic(topic_name, self.topic_data_type.get_name(), self.topic_qos)
        if self.topic is None:
            raise RuntimeError(f"Failed to create topic '{topic_name}'")

        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)
        if self.subscriber is None:
            raise RuntimeError("Failed to create Subscriber")

        self.listener = ReaderListener(queue=queue)
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)
        if self.reader is None:
            raise RuntimeError("Failed to create DataReader")

    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)

    def run(self):
        stop_event = threading.Event()

        def _handler(*_):
            stop_event.set()

        signal.signal(signal.SIGINT, _handler)
        logger.info("Subscriber running. Press Ctrl+C to stop.")
        stop_event.wait()
