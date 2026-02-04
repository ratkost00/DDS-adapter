"""
Adapter Publisher
"""
from threading import Condition
import time

import fastdds
from src.library.Adapter import *

DESCRIPTION = """Adapter Publisher example for Fast DDS python bindings"""
USAGE = ('python3 AdapterPublisher.py')

class WriterListener (fastdds.DataWriterListener) :
    def __init__(self, writer) :
        self._writer = writer
        super().__init__()


    def on_publication_matched(self, datawriter, info) :
        if (0 < info.current_count_change) :
            print ("Publisher matched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()
        else :
            print ("Publisher unmatched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader -= 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()


class Writer:

    def __init__(self, topicName : str, topic : str):
        self._matched_reader = 0
        self._cvDiscovery = Condition()
        self.index = 0

        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)

        self.topic_data_type = AdapterPubSubType()
        self.topic_data_type.set_name(topicName)
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic(topic, self.topic_data_type.get_name(), self.topic_qos)

        self.publisher_qos = fastdds.PublisherQos()
        self.participant.get_default_publisher_qos(self.publisher_qos)
        self.publisher = self.participant.create_publisher(self.publisher_qos)

        self.listener = WriterListener(self)
        self.writer_qos = fastdds.DataWriterQos()
        self.publisher.get_default_datawriter_qos(self.writer_qos)
        self.writer = self.publisher.create_datawriter(self.topic, self.writer_qos, self.listener)


    def write(self, message : str):
        data = Adapter()
        data.message(message)
        data.index(self.index)
        self.writer.write(data)
        print("Sending {message} : {index}".format(message=data.message(), index=data.index()))
        self.index = self.index + 1


    def wait_discovery(self) :
        self._cvDiscovery.acquire()
        print ("Writer is waiting discovery...")
        self._cvDiscovery.wait_for(lambda : self._matched_reader != 0)
        self._cvDiscovery.release()
        print("Writer discovery finished...")


    def run(self):
        self.wait_discovery()
        # for x in range(10) :
        #     time.sleep(1)
        #     self.write()
        # self.delete()


    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)


# if __name__ == '__main__':
#     print('Starting publisher.')
#     writer = Writer()
#     writer.run()
#     exit()