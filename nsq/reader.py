from .client import Client
from .response import Message
from .util import distribute
from . import logger


class Reader(Client):
    '''A client meant exclusively for reading'''
    def __init__(self, topic, channel, lookupd_http_addresses=None,
        nsqd_tcp_addresses=None, max_in_flight=200):
        self._channel = channel
        self._max_in_flight = max_in_flight
        Client.__init__(self, lookupd_http_addresses, nsqd_tcp_addresses, topic)

    def add(self, connection):
        '''Add this connection and manipulate its RDY state'''
        conn = Client.add(self, connection)
        if conn:
            conn.sub(self._topic, self._channel)
            conn.rdy(1)

    def distribute_ready(self):
        '''Distribute the ready state across all of the connections'''
        connections = [c for c in self.connections() if c.alive()]
        if len(connections) > self._max_in_flight:
            raise NotImplementedError(
                'Max in flight must be greater than number of connections')
        else:
            # Distribute the ready count evenly among the connections
            for count, conn in distribute(self._max_in_flight, connections):
                logger.info('Sending RDY %i to %s', count, conn)
                conn.rdy(count)

    def needs_distribute_ready(self):
        '''Determine whether or not we need to redistribute the ready state'''
        # Determine whether or not we need to redistribute the ready state. For
        # now, we'll just to the simple thing and say that if any of the
        # conections has a ready state of 0
        alive = [c for c in self.connections()]
        # It can happen that a connection receives more messages than we might
        # believe its RDY state to be. Consider the case where we send one RDY
        # status, messages are sent back but before we consume them, we send a
        # second RDY status. In this case, the RDY count might be decremented
        # below 0.
        if min([c.ready for c in alive]) <= 0:
            return True

    def close_connection(self, connection):
        '''A hook into when connections are closed'''
        Client.close_connection(self, connection)
        self.distribute_ready()

    def read(self):
        '''Read some number of messages'''
        found = Client.read(self)

        # Redistribute our ready state if necessary
        if self.needs_distribute_ready():
            self.distribute_ready()

        # Finally, return all the results we've read
        return found

    def __iter__(self):
        while True:
            for message in self.read():
                # A reader's only interested in actual messages
                if isinstance(message, Message):
                    # We'll probably add a hook in here to track the RDY states
                    # of our connections
                    yield message
