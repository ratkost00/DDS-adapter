"""
Adapter Subscriber
"""
import signal

import fastdds
from src.library.Adapter import *
from multiprocessing import Queue
from typing import Optional

DESCRIPTION = """Adapter Subscriber example for Fast DDS python bindings"""
USAGE = ('python3 AdapterSubscriber.py')

# To capture ctrl+C
def signal_handler(sig, frame):
    print('Interrupted!')

class ReaderListener(fastdds.DataReaderListener):


    def __init__(self, queue : Optional[Queue] = None) -> None:
        super().__init__()
        if queue is not None:
            self.queue : Queue[str] = queue


    def on_subscription_matched(self, reader, info) -> None:
        if (0 < info.current_count_change) :
            # print ("Subscriber matched publisher {}".format(info.last_publication_handle))
            pass
        else :
            # print ("Subscriber unmatched publisher {}".format(info.last_publication_handle))
            pass


    def on_data_available(self, reader) -> None:
        info = fastdds.SampleInfo()
        data = Adapter()
        reader.take_next_sample(data, info)
        # print("Received {message} : {index}".format(message=data.message(), index=data.index()))
        if self.queue is not None:
            self.queue.put(data.message())


class Reader:

    def __init__(self, topicName : str, topic : str, queue : Optional[Queue] = None):
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

        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)

        self.listener = ReaderListener(queue=queue)
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)


    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)


    def run(self):
        signal.signal(signal.SIGINT, signal_handler)
        print('Press Ctrl+C to stop')
        


# if __name__ == '__main__':
#     print('Creating subscriber.')
#     reader = Reader()
#     reader.run()
#     exit()