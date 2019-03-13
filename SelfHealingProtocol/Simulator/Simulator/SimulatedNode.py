# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Simulation                                                                                                         *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 19/02/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that simulates the functioning of a node in the network                                                    *
 *  The node will contain all the information that the simulated node should posses at each step of the simulation.    *
 *  Nodes will execute the event that is given in the events queue and return the list of new events after it, all     *
 *  depending of the given scheduled network.                                                                          *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


from Event import FrameEvent, ExecutionEvent, InternalEvent
from typing import List, Union
from bisect import bisect_left


class SimulatedNode:
    """
    Class that models a simulated node in the network, including all the information they posses and they queue of
    events to simulate
    """

    # Init #

    def __init__(self):
        """
        Init of the simulated node data and status
        """
        # All events sorted by event time
        self.__event_queue: List[Union[FrameEvent, ExecutionEvent, InternalEvent]] = []
        self.__notified: List[int] = []     # List of SHP ids that the node already got notified with
        self.__found: List[int] = []        # List of SHP ids that the node already got notified to find the path

    # Functions #

    def add_event(self, event: Union[FrameEvent, ExecutionEvent, InternalEvent]) -> None:
        """
        Add a new event to the sorted event queue. It needs to be ordered, with the first event to happen as first
        :param event: event to add
        :return: nothing
        """
        # If the event is a notification or finding path frame and already was received, do not add the event
        if event.name is FrameEvent.FrameName.Notification and event.event_id in self.__notified:
            return
        if event.name is FrameEvent.FrameName.FindingPath and event.event_id in self.__found:
            return
        # If the event is a notification or finding path frame, set the node as receiving that node already
        if event.name is FrameEvent.FrameName.Notification:
            self.__notified.append(event.event_id)
        if event.name is FrameEvent.FrameName.FindingPath:
            self.__found.append(event.event_id)

        # Create a list of the times of all the events, then search the position of the new event and add it
        times = [e.time for e in self.__event_queue]
        position = bisect_left(times, event.time)
        self.__event_queue.insert(position, event)

    def get_next_event(self) -> Union[FrameEvent, ExecutionEvent, InternalEvent, None]:
        """
        Get the next event
        :return: next event to execute
        """
        if self.__event_queue:
            return self.__event_queue[0]
        else:
            return None

    def pop_next_event(self) -> Union[FrameEvent, ExecutionEvent, InternalEvent]:
        """
        Pop the next event
        :return: next event to execute
        """
        return self.__event_queue.pop(0)

    def add_found_event(self, event_id: int) -> None:
        """
        Auxiliary event that notifies that a node has found the path to the event
        :param event_id: event identifier
        :return: nothing
        """
        self.__found.append(event_id)
