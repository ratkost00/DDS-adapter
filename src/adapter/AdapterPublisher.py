"""
Adapter Publisher
"""
import logging
from threading import Condition

import fastdds
from src.library.Adapter import *

logger = logging.getLogger(__name__)


class WriterListener(fastdds.DataWriterListener):
    def __init__(self, writer):
        self._writer = writer
        super().__init__()

    def on_publication_matched(self, writer, info):
        with self._writer._cvDiscovery:
            if 0 < info.current_count_change:
                self._writer._matched_reader += 1
            else:
                self._writer._matched_reader -= 1
            self._writer._cvDiscovery.notify()


class Writer:

    def __init__(self, type_name: str, topic_name: str):
        self._matched_reader = 0
        self._cvDiscovery = Condition()
        self.index = 0

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

        self.publisher_qos = fastdds.PublisherQos()
        self.participant.get_default_publisher_qos(self.publisher_qos)
        self.publisher = self.participant.create_publisher(self.publisher_qos)
        if self.publisher is None:
            raise RuntimeError("Failed to create Publisher")

        self.listener = WriterListener(self)
        self.writer_qos = fastdds.DataWriterQos()
        self.publisher.get_default_datawriter_qos(self.writer_qos)
        self.writer = self.publisher.create_datawriter(self.topic, self.writer_qos, self.listener)
        if self.writer is None:
            raise RuntimeError("Failed to create DataWriter")

    def write(self, message: str):
        data = Adapter()
        data.message(message)
        data.index(self.index)
        self.writer.write(data)
        self.index += 1

    def wait_discovery(self):
        with self._cvDiscovery:
            logger.info("Writer waiting for discovery...")
            self._cvDiscovery.wait_for(lambda: self._matched_reader != 0)
        logger.info("Writer discovery finished")

    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)
