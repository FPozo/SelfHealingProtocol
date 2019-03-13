# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Simulation                                                                                                         *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 19/02/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that simulates executions of Deterministic Ethernet Networks                                               *
 *  This modulo given a list of events, will simulate the execution of such events, and provide outputs of how the     *
 *  simulation went, including timing for the event, if after the event the network keep working properly and such     *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


from Network import Network
from Link import Link
from typing import NamedTuple, List, Dict, Union, Tuple
from operator import attrgetter, itemgetter
from enum import Enum
from SimulatedNode import SimulatedNode
from Event import FrameEvent, ExecutionEvent, InternalEvent
from xml.dom import minidom
from os import remove
from os.path import isfile
from subprocess import run
from math import log2, ceil
import pandas
import xml.etree.ElementTree as Xml


class Simulation:
    """
    Simulates events that happen to a scheduled network and how it reacts, providing outputs
    """

    # Exceptions
    class NoPath(Exception):
        """
        There exist no path to connect the sender and receiver
        """
        pass

    class NoSchedule(Exception):
        """
        There does not exist a valid schedule when repairing
        """
        pass

    # Constants #

    __MAX_SIMULATION_TIME = 999999999999999999999999999999999

    # Sizes
    __SIZE_CODE_LINK = 5
    __SIZE_CODE_FRAME = 3
    __SIZE_CODE_TRANS = 32
    __SIZE_CODE_FRAME_ID = 4
    __SIZE_CODE_INST = 4

    # Processing times
    __NOTIFICATION_PROC_TIME = 0
    __FINDING_PATH_PROC_TIME = 0
    __NOTIFY_PATH_PROC_TIME = 0
    __MEMBERSHIP_PROC_TIME = 0
    __PATCH_PROC_TIME = 0
    __OPTIMIZE_PROC_TIME = 0
    __UPDATE_PROC_TIME = 0
    __SCHEDULE_PROC_TIME = 0

    # Auxiliary Classes #

    class Algorithm(Enum):
        SHP = 'SHP'

    # Named Tuples #

    class EventsStarters(NamedTuple):

        class Component(Enum):
            Link = 'Link'
            Node = 'Node'

        component_type: Component       # Type of component
        component_ID: int               # ID of the component
        time: int                       # Time when the event happens (or is detected)

    # Init #

    def __init__(self, network: Network):
        """
        Init of the simulator
        :param network: given scheduled network to simulate
        """
        self.__algorithm = None             # Algorithm to execute in the simulation
        self.__add_database: bool = None    # Add information of the simulation to the database
        self.__network = network
        self.__events: List[Simulation.EventsStarters] = []         # Sorted list of events to simulate
        self.__nodes: Dict[int, SimulatedNode] = {}                 # Dictionary of the simulated nodes by node id
        self.__link_usage: Dict[int, List[Tuple[str, int, int]]] = {}    # Dictionary of transmission usage for testing
        self.__protocol = self.__network.healing_protocol           # Bandwidth reservation protocol
        self.__leader: Dict[int, int] = {}                          # Dictionary of leaders for the protocol activation
        self.__activator: Dict[int, int] = {}                       # Dictionary with the activator of the protocol
        self.__path_leader: Dict[int, List[int]] = {}       # Dictionary with path from activator to leader by nodes
        self.__path_activator: Dict[int, List[int]] = {}    # Dictionary with path from leader to activator by nodes
        self.__path_member: Dict[int, List[int]] = {}       # Dictionary with path from member to leader by nodes
        self.__patching_status: Dict[int, int] = {}         # Dictionary with patching received by the leader
        self.__optimization_status: Dict[int, int] = {}     # Dictionary with optimization received by the leader
        self.__execution_time = 0                           # Execution time of the last execution event
        self.__size_core_frame: Dict[int, int] = {}         # Core size in bits of the base of a SHP frame
        self.__size_member_frame: Dict[int, int] = {}       # Core size in bits of the schedule that is transmitted

        # Information for the database
        self.__utilization_broken_link: Dict[int, float] = {}            # Utilization of the broken link
        self.__utilization_new_path: Dict[int, Dict[int, float]] = {}    # Utilization of the new path
        self.__offsets_broken_link: Dict[int, int] = {}             # Number of offsets in the broken link
        self.__offsets_new_path: Dict[int, Dict[int, int]] = {}     # Number of offsets in the new path
        self.__successful_heal: Dict[int, bool] = {}                # Could the broken link be repaired
        self.__patching_time: Dict[int, Dict[int, int]] = {}             # Time to patch the broken link
        self.__optimization_L1_time: Dict[int, Dict[int, int]] = {}      # Time to optimize the broken link
        self.__optimization_L2_time: Dict[int, Dict[int, int]] = {}      # Time to optimize with level 2 the broken link

        # Init all the simulated nodes
        for node_id in self.__network.nodes_id:
            self.__nodes[node_id] = SimulatedNode()

    # Auxiliary Functions #

    def __prepare_simulation(self) -> None:
        """
        Prepare the simulation by adding all the simulation configuration read in the xml file to the events to
        simulate
        :return: nothing
        """

        # Init the size of the codes
        self.__SIZE_CODE_FRAME = ceil(log2(self.__network.num_frames))
        self.__SIZE_CODE_LINK = ceil(log2(self.__network.num_links))
        self.__SIZE_CODE_TRANS = ceil(log2(self.__network.hyper_period))

        # If we are repairing a link
        if self.__algorithm is self.Algorithm.SHP:
            for event in self.__events:

                if event.component_type != self.EventsStarters.Component.Link:
                    raise ValueError('The SHP can only repair links')

                receiver_id = self.__network.get_receiver_id_link(event.component_ID)
                self.__nodes[receiver_id].add_event(InternalEvent(event.component_ID, 'LinkFailure', event.time))

    def __select_next_event(self) -> Tuple[Union[FrameEvent, ExecutionEvent, InternalEvent, None], int]:
        """
        For all the events stacked in the simulated nodes, select the next one happening
        :return: the event to simulate and the node id
        """
        return_node_id = -1
        min_time = self.__MAX_SIMULATION_TIME

        # For all the simulated nodes, get the next event and check which one on the whole network is next
        for node_id, node in self.__nodes.items():
            event = node.get_next_event()
            if event is not None:
                if event.time < min_time:
                    min_time = event.time
                    return_node_id = node_id

        # Get the next event and pop it from the queue
        if return_node_id == -1:
            return None, -1
        else:
            return self.__nodes[return_node_id].pop_next_event(), return_node_id

    def __simulate_frame_event(self, event: FrameEvent, node_id: int) -> None:
        """
        Check which frame event is and simulate it
        :param event: event to simulate
        :param node_id: node id of the event to simulate
        :return: nothing
        """
        if event.name in [FrameEvent.FrameName.Notification, FrameEvent.FrameName.FindingPath]:
            self.__simulate_broadcast_frame(event, node_id)
        elif event.name in [FrameEvent.FrameName.NotifyPath, FrameEvent.FrameName.Membership,
                            FrameEvent.FrameName.Patch, FrameEvent.FrameName.UpdatePatch,
                            FrameEvent.FrameName.Optimization, FrameEvent.FrameName.UpdateOptimization,
                            FrameEvent.FrameName.Schedule]:
            self.__simulate_single_frame(event, node_id)

    def __simulate_internal_event(self, event: InternalEvent) -> None:
        """
        Simulate an internal such as a component failure
        :param event: event to simulate
        :return: nothing
        """
        if event.name is InternalEvent.InternalName.LinkFailure:
            receiver_id = self.__network.get_receiver_id_link(event.event_id)
            self.__activator[event.event_id] = receiver_id
            sender_id = self.__network.get_sender_id_link(event.event_id)
            self.__leader[event.event_id] = sender_id
            self.__network.remove_link(event.event_id)

            if self.__network.get_num_offsets(event.event_id) == 0:     # Nothing to do if there are no transmissions
                return

            # Create the paths to communicate between leader and member nodes
            try:
                self.__path_activator[event.event_id] = self.__network.get_shortest_path(sender_id, receiver_id)
            except ValueError:
                self.__successful_heal[event.event_id] = False
                raise Simulation.NoPath('The link failure cannot be repaired as there is no path to connect')
            try:
                self.__path_leader[event.event_id] = self.__network.get_shortest_path(receiver_id, sender_id)
                self.__successful_heal[event.event_id] = False
            except ValueError:
                raise Simulation.NoPath('The link failure cannot be repaired as there is no path to connect')
            # We remove the first node of every path to avoid duplicates
            self.__path_member[event.event_id] = list(self.__path_activator[event.event_id][1:])
            self.__path_member[event.event_id].extend(list(self.__path_leader[event.event_id][1:]))

            self.__nodes[receiver_id].add_event(FrameEvent(event.event_id, 'Notification', event.time,
                                                           self.__SIZE_CODE_LINK + self.__SIZE_CODE_FRAME))

            # Save the utilization
            self.__save_utilization_database(event.event_id)

            # Save the number of offsets
            self.__save_num_offsets_database(event.event_id)

        else:
            raise ValueError('Internal Event not recognized')

    def __simulate_execution_event(self, event: ExecutionEvent, node_id: int) -> None:
        """
        Check which execution event is and simulate it
        :param event: event to simulate
        :param node_id: node id of the event to simulate
        :return: nothing
        """
        if event.name is ExecutionEvent.ExecutionName.Patch:
            index_receiver = self.__path_activator[event.event_id].index(node_id) + 1
            link, link_id = self.__network.get_link_data(node_id, self.__path_activator[event.event_id][index_receiver])

            patch_file = '../Files/Outputs/Patch_' + str(event.event_id) + '_' + str(node_id) + '.xml'
            patched_file = '../Files/Outputs/PatchedSchedule_' + str(event.event_id) + '_' + str(node_id) + '.xml'
            execution_file = '../Files/Outputs/Execution.xml'

            self.__write_patch_xml(patch_file, link, link_id, node_id, event.event_id)
            run(['./../Files/Executables/Patch', patch_file, patched_file, execution_file])
            remove(patch_file)

            self.__read_execution_time_xml(execution_file)
            self.__patching_time[event.event_id][link_id] = self.__execution_time
            remove(execution_file)

            if isfile(patched_file):

                self.__read_patched_schedule_xml(patched_file, event.event_id)
                remove(patched_file)

                # Send the Patch frame and start the optimization
                self.__nodes[node_id].add_event(FrameEvent(event.event_id, FrameEvent.FrameName.Schedule, event.time +
                                                           self.__execution_time + self.__SCHEDULE_PROC_TIME, 0))

                self.__nodes[node_id].add_event(FrameEvent(event.event_id, FrameEvent.FrameName.Patch,
                                                           event.time + self.__execution_time + self.__PATCH_PROC_TIME,
                                                           self.__size_core_frame[event.event_id] + 1))

            self.__nodes[node_id].add_event(ExecutionEvent(event.event_id, ExecutionEvent.ExecutionName.Optimize,
                                                           event.time + self.__execution_time))

        elif event.name is ExecutionEvent.ExecutionName.Optimize:
            index_receiver = self.__path_activator[event.event_id].index(node_id) + 1
            link, link_id = self.__network.get_link_data(node_id, self.__path_activator[event.event_id][index_receiver])

            optimize_file = '../Files/Outputs/Optimize_' + str(event.event_id) + '_' + str(node_id) + '.xml'
            optimized_file = '../Files/Outputs/OptimizedSchedule_' + str(event.event_id) + '_' + str(node_id) + '.xml'
            execution_file = '../Files/Outputs/Execution.xml'

            self.__write_optimize_xml(optimize_file, link, link_id, node_id, event.event_id)
            run(['./../files/Executables/Optimize', optimize_file, optimized_file, execution_file])
            remove(optimize_file)

            self.__read_execution_time_xml(execution_file)
            self.__optimization_L1_time[event.event_id][link_id] = self.__execution_time
            remove(execution_file)

            # If the optimize was successful, read the optimized schedule, otherwise try optimize L2
            if isfile(optimized_file):
                self.__read_patched_schedule_xml(optimized_file, event.event_id)
                remove(optimized_file)

            else:
                self.__write_optimize_l2_xml(optimize_file, link, link_id, node_id, event.event_id)
                run(['./../files/Executables/Optimize', optimize_file, optimized_file, execution_file])
                remove(optimize_file)

                # Add the execution time of the failed attempt at optimization level 1
                before_exec_time = self.__execution_time
                self.__read_execution_time_xml(execution_file)
                self.__optimization_L2_time[event.event_id][link_id] = self.__execution_time
                self.__execution_time += before_exec_time
                remove(execution_file)

                if not isfile(optimized_file):
                    self.__successful_heal[event.event_id] = False
                    raise Simulation.NoSchedule('Error Repairing the link ' + str(event.event_id))

                self.__read_patched_schedule_xml(optimized_file, event.event_id)
                remove(optimized_file)

            self.__nodes[node_id].add_event(FrameEvent(event.event_id, FrameEvent.FrameName.Schedule, event.time +
                                                       self.__execution_time + self.__SCHEDULE_PROC_TIME, 0))

            self.__nodes[node_id].add_event(FrameEvent(event.event_id, FrameEvent.FrameName.Optimization,
                                                       event.time + self.__execution_time + self.__OPTIMIZE_PROC_TIME,
                                                       self.__size_core_frame[event.event_id] + 1))

        else:
            raise ValueError('Execution Event not recognized')

    def __simulate_single_frame(self, event: FrameEvent, node_id: int) -> None:

        # If the frame is a notify path, follow the path activator to leader
        if event.name is FrameEvent.FrameName.NotifyPath:
            # If the frame is still on its way
            index_path = self.__path_leader[event.event_id].index(node_id)
            if index_path + 1 < len(self.__path_leader[event.event_id]):
                receiver_id = self.__path_leader[event.event_id][index_path + 1]
                processing_time = self.__FINDING_PATH_PROC_TIME
                size = event.size
            else:
                self.__size_core_frame[event.event_id] = event.size
                # The frame has arrived its destination, so it starts a membership frame
                # We need to calculate the size of the membership message as the number of frames in the affected link
                num_frames = len([frame_id for frame_id, _, _ in self.__network.get_offsets_by_link(event.event_id)])
                size = event.size + (num_frames * 2 * self.__SIZE_CODE_FRAME_ID * self.__SIZE_CODE_INST)
                self.__size_member_frame[event.event_id] = size

                self.__nodes[node_id].add_event(FrameEvent(event.event_id, FrameEvent.FrameName.Membership,
                                                           event.time + self.__MEMBERSHIP_PROC_TIME, size))
                return

        elif event.name is FrameEvent.FrameName.Membership:

            # If the frame is still on its way
            index_path = self.__path_activator[event.event_id].index(node_id)
            if index_path + 1 < len(self.__path_activator[event.event_id]):
                receiver_id = self.__path_activator[event.event_id][index_path + 1]
                processing_time = self.__MEMBERSHIP_PROC_TIME
                size = event.size

                # The solving does not have to be called for the activator node as it doesnt need to patch any link
                self.__nodes[node_id].add_event(ExecutionEvent(event.event_id, ExecutionEvent.ExecutionName.Patch,
                                                               event.time + processing_time))

            else:  # The frame has arrived its destination
                return

        elif event.name is FrameEvent.FrameName.Patch:
            # Finds the last index path
            index_path = [it for it, i in enumerate(self.__path_member[event.event_id]) if i == node_id][-1]
            if index_path + 1 < len(self.__path_member[event.event_id]):
                receiver_id = self.__path_member[event.event_id][index_path + 1]
                processing_time = self.__PATCH_PROC_TIME
                size = event.size
            else:
                self.__check_patching_status(event.event_id, event.time)
                return

        elif event.name is FrameEvent.FrameName.UpdatePatch:
            index_path = self.__path_activator[event.event_id].index(node_id)
            if index_path + 1 < len(self.__path_activator[event.event_id]):
                receiver_id = self.__path_activator[event.event_id][index_path + 1]
                processing_time = self.__UPDATE_PROC_TIME
                size = event.size
            else:
                return

        elif event.name is FrameEvent.FrameName.Optimization:
            # Finds the last index path
            index_path = [it for it, i in enumerate(self.__path_member[event.event_id]) if i == node_id][-1]
            if index_path + 1 < len(self.__path_member[event.event_id]):
                receiver_id = self.__path_member[event.event_id][index_path + 1]
                processing_time = self.__OPTIMIZE_PROC_TIME
                size = event.size
            else:
                self.__check_optimization_status(event.event_id, event.time)
                return

        elif event.name is FrameEvent.FrameName.UpdateOptimization:
            index_path = self.__path_activator[event.event_id].index(node_id)
            if index_path + 1 < len(self.__path_activator[event.event_id]):
                receiver_id = self.__path_activator[event.event_id][index_path + 1]
                processing_time = self.__UPDATE_PROC_TIME
                size = event.size
            else:
                return

        elif event.name is FrameEvent.FrameName.Schedule:
            if event.size == 0:
                index_path = self.__path_activator[event.event_id].index(node_id)
                receiver_id = self.__path_activator[event.event_id][index_path + 1]
                processing_time = self.__UPDATE_PROC_TIME
                size = self.__SIZE_CODE_LINK + self.__SIZE_CODE_FRAME + self.__size_member_frame[event.event_id]
            else:
                return

        else:
            raise ValueError('We do not support the given frame event')

        link, link_id = self.__network.get_link_data(node_id, receiver_id)
        time_event = self.__find_time_event(event.time, size, event.name, link, link_id, processing_time)

        # Add the event
        self.__nodes[receiver_id].add_event(FrameEvent(event.event_id, event.name, time_event, size))

    def __simulate_broadcast_frame(self, event: FrameEvent, node_id: int) -> None:
        """
        Simulate all the broadcast frame events, it also activates the new events if a node receives the broadcast
        frame that it is intended to itself
        :param event: event to simulate
        :param node_id: node id of the event to simulate
        :return: nothing
        """
        # If the node activator receives a finding path frame for him, stop the finding path process and send a
        # notify path with a single frame with already known path
        if event.name is FrameEvent.FrameName.FindingPath and node_id == self.__activator[event.event_id]:
            process_time = self.__NOTIFY_PATH_PROC_TIME
            name = FrameEvent.FrameName.NotifyPath
            size = self.__SIZE_CODE_LINK + event.size
            self.__nodes[node_id].add_event(FrameEvent(event.event_id, name, event.time + process_time, size))
            return

        # If the node receives a notification frame for him and has to start the finding path process
        elif event.name is FrameEvent.FrameName.Notification and node_id == self.__leader[event.event_id]:
            process_time = self.__FINDING_PATH_PROC_TIME
            size = self.__SIZE_CODE_LINK + event.size
            name = FrameEvent.FrameName.FindingPath
            self.__nodes[node_id].add_found_event(event.event_id)

        # If the node receives a finding path frame that has to broadcast
        elif event.name is FrameEvent.FrameName.FindingPath:
            process_time = self.__FINDING_PATH_PROC_TIME
            size = self.__SIZE_CODE_LINK + event.size
            name = event.name

        # If the node receives a notification frame that has to broadcast
        elif event.name is FrameEvent.FrameName.Notification:
            process_time = self.__NOTIFICATION_PROC_TIME
            size = self.__SIZE_CODE_LINK + event.size
            name = event.name

        else:
            raise ValueError('We do not support the given frame event')

        # The node receives the notification frame and has to broadcast the frame
        receivers_id = self.__network.get_neighbors_ids_by_node(node_id)
        for receiver_id in receivers_id:

            link, link_id = self.__network.get_link_data(node_id, receiver_id)
            time_event = self.__find_time_event(event.time, size, name, link, link_id, process_time)

            # Add the event
            self.__nodes[receiver_id].add_event(FrameEvent(event.event_id, name, time_event, size))

    def __check_patching_status(self, event_id: int, time: int) -> None:
        """
        After a patching frame has been received, check if all the patch were received to start the update step
        :param event_id: event identifier
        :param time: time to check status
        :return: nothing
        """
        # Update the number of patched received by the leader
        if event_id not in self.__patching_status.keys():
            self.__patching_status[event_id] = 1
        else:
            self.__patching_status[event_id] += 1

        # Check if all patching status were received, if it was, start the update event
        # Also, update the paths of all the frames affected
        if self.__patching_status[event_id] == (len(self.__path_activator[event_id]) - 1):
            # Calculate the path to activator from nodes identifiers to link identifiers
            new_path = []
            for node_it in range(len(self.__path_activator[event_id]) - 1):
                new_path.append(self.__network.get_link_data(self.__path_activator[event_id][node_it],
                                                             self.__path_activator[event_id][node_it + 1])[1])

            for frame in self.__network.frames.values():
                frame.exchange_path(event_id, new_path)

            self.__nodes[self.__leader[event_id]].add_event(FrameEvent(event_id, FrameEvent.FrameName.UpdatePatch,
                                                                       time + self.__UPDATE_PROC_TIME,
                                                                       self.__size_core_frame[event_id] +
                                                                       self.__SIZE_CODE_TRANS))

    def __check_optimization_status(self, event_id: int, time: int) -> None:
        """
        After a optimization frame has been received, check if all the patch were received to start the update step
        :param event_id: event identifier
        :param time: time to check status
        :return: nothing
        """
        # Update the number of patched received by the leader
        if event_id not in self.__optimization_status.keys():
            self.__optimization_status[event_id] = 1
        else:
            self.__optimization_status[event_id] += 1

        # Check if all optimization status were received, if it was, start the update event
        if self.__optimization_status[event_id] == (len(self.__path_activator[event_id]) - 1):
            self.__network.update_utilization()     # We also update the utilization of the network
            self.__nodes[self.__leader[event_id]].add_event(FrameEvent(event_id,
                                                                       FrameEvent.FrameName.UpdateOptimization,
                                                                       time + self.__UPDATE_PROC_TIME,
                                                                       self.__size_core_frame[event_id] +
                                                                       self.__SIZE_CODE_TRANS))

    def __find_time_event(self, time: int, size: int, name: FrameEvent.FrameName, link: Link, link_id: int,
                          process_time: int) -> int:
        """
        Find the time of the next event and adds the transmission to the list usage
        :param time: time of the event
        :param size: size of the event
        :param name: name of the event
        :param link: link data where the transmission happens
        :param link_id: link id
        :param process_time: process time of the receiver node
        :return: the time when the receiver node can send the next event
        """

        time_data = int(size * 1000 / 8 / link.speed)     # Time to transmit the data
        starting = time                                   # Time when the event starts

        # If the frame starts outside the reservation window
        if starting % self.__protocol.period > self.__protocol.time:
            starting += self.__protocol.period - (starting % self.__protocol.period)

        # If the starting time collides, add it after the collision
        if link_id in self.__link_usage.keys():
            for interval in self.__link_usage[link_id]:
                # If it collides, move the starting time, do not take into account if the interval is broken in the mid
                if (interval[2] % self.__protocol.period) != self.__protocol.time:
                    if interval[1] <= starting < interval[2]:
                        starting = interval[2]
                else:
                    # If it tries to send after the bandwidth reservation, we start search on the next window
                    if interval[1] <= starting < interval[2]:
                        starting += self.__protocol.period - (starting % self.__protocol.period)
                # If it is later, we do not need to move the starting time
                if interval[1] > starting:
                    break

        # While the frame ends outside the reservation window, divide it
        while (starting + time_data) % self.__protocol.period > self.__protocol.time:
            time_event = (starting + time_data) - ((starting + time_data) % self.__protocol.time)

            # If we still did not transmit all the date, add to the link usage
            if starting != time_event:
                if link_id in self.__link_usage.keys():
                    self.__link_usage[link_id].append((name.name, starting, time_event))
                else:
                    self.__link_usage[link_id] = [(name.name, starting, time_event)]

            # Update the time to transmit the remaining data and the new start time
            time_data -= time_event - starting
            starting += self.__protocol.period - (starting % self.__protocol.period)

        # Add the link usage of the last transmission window
        if link_id in self.__link_usage.keys():
            self.__link_usage[link_id].append((name.name, starting, starting + time_data))
        else:
            self.__link_usage[link_id] = [(name.name, starting, starting + time_data)]

        self.__link_usage[link_id].sort(key=itemgetter(1))      # Sort for a more easy pretty printing
        return starting + time_data + process_time

    def __test_link_usage(self) -> None:
        """
        Test if any transmission in the link usage collides
        :return: nothing
        """
        for link_list in self.__link_usage.values():
            for index, range1 in enumerate(link_list):

                # If the transmission is outside the range of the bandwidth reservation
                if (range1[1] % self.__protocol.period) > self.__protocol.time or \
                        (range1[2] % self.__protocol.period) > self.__protocol.time or \
                        (range1[2] - range1[1] > self.__protocol.time):
                    raise ValueError('Transmission at link usages outside allowed bandwidth')

                # If it collides with other transmission ranges
                for range2 in link_list[:index]:
                    if range1[1] < range2[2] and range2[1] < range1[2]:
                        raise ValueError('Transmission at link usages collide')

    def __save_utilization_database(self, broken_link_id: int) -> None:
        """
        Save the utilization of the broken link and the new path for the database
        :param broken_link_id: broken link identifier
        :return: nothing
        """

        # We also init the execution time outputs
        self.__successful_heal[broken_link_id] = True
        self.__patching_time[broken_link_id] = {}
        self.__optimization_L1_time[broken_link_id] = {}
        self.__optimization_L2_time[broken_link_id] = {}

        try:
            self.__utilization_broken_link[broken_link_id] = self.__network.link_utilization[broken_link_id]
        except KeyError:
            self.__utilization_broken_link[broken_link_id] = 0.0
        self.__utilization_new_path[broken_link_id] = {}
        for index_path, _ in enumerate(self.__path_activator[broken_link_id][:-1]):
            sender_id = self.__path_activator[broken_link_id][index_path]
            receiver_id = self.__path_activator[broken_link_id][index_path + 1]
            _, link_id = self.__network.get_link_data(sender_id, receiver_id)
            try:
                link_ut = self.__network.link_utilization[link_id]
            except KeyError:
                link_ut = 0.0
            self.__utilization_new_path[broken_link_id][link_id] = link_ut

            self.__patching_time[broken_link_id][link_id] = 0
            self.__optimization_L1_time[broken_link_id][link_id] = 0
            self.__optimization_L2_time[broken_link_id][link_id] = 0

    def __save_num_offsets_database(self, broken_link_id: int) -> None:
        """
        Save the number of offsets in the broken link and the new path for the database
        :param broken_link_id: broken link identifier
        :return: nothing
        """
        self.__offsets_broken_link[broken_link_id] = self.__network.get_num_offsets(broken_link_id)
        self.__offsets_new_path[broken_link_id] = {}
        for index_path, _ in enumerate(self.__path_activator[broken_link_id][:-1]):
            sender_id = self.__path_activator[broken_link_id][index_path]
            receiver_id = self.__path_activator[broken_link_id][index_path + 1]
            _, link_id = self.__network.get_link_data(sender_id, receiver_id)
            self.__offsets_new_path[broken_link_id][link_id] = self.__network.get_num_offsets(link_id)

    # Simulation Functions #

    def simulate(self) -> None:
        """
        Given the simulated nodes and its events, simulate all the executions
        :return: nothing
        """
        event, node_id = self.__select_next_event()
        # While there are events to simulate, keep simulating
        while event is not None:
            if type(event) is FrameEvent:
                self.__simulate_frame_event(event, node_id)

            elif type(event) is ExecutionEvent:
                self.__simulate_execution_event(event, node_id)

            elif type(event) is InternalEvent:
                self.__simulate_internal_event(event)

            event, node_id = self.__select_next_event()
        self.__test_link_usage()
        self.__network.check_schedule()
        self.__write_database()

    # Input Functions #

    def read_simulation_xml(self, configuration_file: str) -> None:
        """
        Read the simulation configuration to execute
        :param configuration_file: name and path of the xml configuration file
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml = Xml.parse(configuration_file).getroot()
        simulation_xml: Xml.Element = root_xml.find('Simulation')

        # Read the data and save it
        self.__read_general_information_xml(simulation_xml.find('GeneralInformation'))
        self.__read_events_xml(simulation_xml.find('Events'))

        self.__prepare_simulation()

    def __read_general_information_xml(self, general_info_xml: Xml.Element) -> None:
        """
        Read the general information of the simulation
        :param general_info_xml: pointer to the general information xml tree
        :return: nothing
        """
        self.__algorithm = self.Algorithm[general_info_xml.find('Algorithm').text]
        self.__add_database = True if general_info_xml.find('AddDatabase').text == '1' else False

    def __read_events_xml(self, events_xml: Xml.Element) -> None:
        """
        Read the events to simulate
        :param events_xml: pointer to the events information xml tree
        :return: nothing
        """
        # For all events, save it into the event simulator
        for failure_xml in events_xml.findall('Failure'):   # type: Xml.Element
            component_type = self.EventsStarters.Component[failure_xml.attrib['component']]
            component_id = int(failure_xml.find('ID').text)
            time_xml: Xml.Element = failure_xml.find('Time')
            event_time = Network.TimeUnit.convert_ns(int(time_xml.text), time_xml.attrib['unit'])

            self.__events.append(self.EventsStarters(component_type, component_id, event_time))

        # Sort the events queue by time
        self.__events = sorted(self.__events, key=attrgetter('time'))

    def __read_patched_schedule_xml(self, patched_file: str, broken_link: int) -> None:
        """
        Read and save the patched schedule
        :param patched_file: file and path of the patched file
        :param broken_link: broken link identifier
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml: Xml.Element = Xml.parse(patched_file).getroot()

        # Read the link identifier of the path
        patched_link = int(root_xml.find('GeneralInformation/LinkID').text)

        # Read all the transmissions of all the patched frames and save them into the frame
        frames = self.__network.frames
        for frame_xml in root_xml.findall('TrafficInformation/Frame'):    # type: Xml.Element
            frame_id = int(frame_xml.find('FrameID').text)

            frames[frame_id].add_offset(patched_link)
            frames[frame_id].prepare_link_offset(patched_link, frames[frame_id].offsets[broken_link].num_instances, 0)

            for instance, instance_xml in enumerate(frame_xml.findall('Instance')):
                transmission_time = int(instance_xml.find('TransmissionTime').text) * self.__network.time_slot_size
                ending_time = int(instance_xml.find('EndingTime').text) * self.__network.time_slot_size

                frames[frame_id].set_offset_transmission_time(patched_link, instance, 0, transmission_time)
                frames[frame_id].set_offset_ending_time(patched_link, instance, 0, ending_time)

    def __read_execution_time_xml(self, execution_file: str) -> None:
        """
        Read the execution of the last algorithm called
        :param execution_file: path and name of the execution file
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml: Xml.Element = Xml.parse(execution_file).getroot()

        self.__execution_time = int(root_xml.find('Timing/ExecutionTime').text)

    # Output Functions #

    def __write_patch_general_information_xml(self, general_info: Xml.Element, link: Link, link_id: int) -> None:
        """
        Write the general information of the patch
        :param general_info: general information pointer to the tree
        :param link: link information
        :param link_id: link to patch
        :return: nothing
        """
        protocol = self.__network.healing_protocol
        Xml.SubElement(general_info, 'LinkID').text = str(link_id)
        Xml.SubElement(general_info, 'LinkSpeed').text = str(link.speed)
        Xml.SubElement(general_info, 'ProtocolPeriod').text = str(int(protocol.period / self.__network.time_slot_size))
        Xml.SubElement(general_info, 'ProtocolTime').text = str(int(protocol.time / self.__network.time_slot_size))
        Xml.SubElement(general_info, 'HyperPeriod').text = str(int(self.__network.hyper_period /
                                                                   self.__network.time_slot_size))

    def __write_patch_fixed_traffic_xml(self, fixed_traffic: Xml.Element, link_id: int) -> None:
        """
        Write in the xml file the fixed frames transmissions that cannot be changed while patching
        :param fixed_traffic: pointer to the fixed traffic
        :param link_id: link to extract fixed transmissions
        :return: nothing
        """

        # For all the transmission in the given link, write their information
        for frame_id, frame, offset in self.__network.get_offsets_by_link(link_id):

            # Ignore if the offset received is not in the list of paths, as we understand that we eliminated it
            links_all_paths = [link_path for receiver_id in frame.receivers_id for link_path in
                               frame.get_path(receiver_id)]
            if link_id in links_all_paths:

                frame_xml: Xml.Element = Xml.SubElement(fixed_traffic, 'Frame')
                Xml.SubElement(frame_xml, 'FrameID').text = str(frame_id)
                Xml.SubElement(frame_xml, 'Period').text = str(int(frame.period / self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'Deadline').text = str(int(frame.deadline / self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'Size').text = str(frame.size)
                Xml.SubElement(frame_xml, 'StartingTime').text = str(int(frame.starting_time /
                                                                         self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'EndToEndDelay').text = str(int(frame.end_to_end /
                                                                          self.__network.time_slot_size))
                offset_xml: Xml.Element = Xml.SubElement(frame_xml, 'Offset')
                for instance in range(offset.num_instances):
                    instance_xml: Xml.Element = Xml.SubElement(offset_xml, 'Instance')
                    Xml.SubElement(instance_xml, 'NumInstance').text = str(instance)
                    Xml.SubElement(instance_xml, 'TransmissionTime').text = \
                        str(int(offset.get_transmission_time(instance, 0) / self.__network.time_slot_size))
                    Xml.SubElement(instance_xml, 'EndingTime').text = str(int(offset.get_ending_time(instance, 0) /
                                                                              self.__network.time_slot_size))

    def __write_patch_traffic_xml(self, traffic: Xml.Element, broken_link_id: int, node_id: int) -> None:
        """
        Write the traffic to patch with the available ranges
        :param traffic: pointer to the traffic xml tree
        :param broken_link_id: broken link identifier
        :param node_id: node that has to patch identifier
        :return: nothing
        """

        # For all the transmission in the broken link, create their available ranges in the link
        for frame_id, frame, offset in self.__network.get_offsets_by_link(broken_link_id):

            # Obtain the available transmission range and divide it depending on the position of the link
            last_link_path = self.__network.get_link_data(self.__path_activator[broken_link_id][-2],
                                                          self.__path_activator[broken_link_id][-1])[1]
            transmission_range = self.__network.get_available_transmission_range(frame, offset, broken_link_id,
                                                                                 last_link_path)
            position_path = self.__path_activator[broken_link_id].index(node_id)
            for current_range in transmission_range:
                transmission_length = current_range[1] - current_range[0]
                current_range[1] = int((position_path + 1) * (transmission_length /
                                       len(self.__path_activator[broken_link_id]) - 1) + current_range[0] - 1)
                current_range[0] = int(position_path * (transmission_length /
                                                        len(self.__path_activator[broken_link_id])) + current_range[0])
                # Take into account the switch time for the different hops in the path
                current_range[0] += self.__network.minimum_switch_time

            # Get the speed of the link of the new link transmission to calculate the time to transmit
            link, _ = self.__network.get_link_data(node_id, self.__path_activator[broken_link_id][position_path + 1])
            time_transmission = int((frame.size * 1000 / link.speed) / self.__network.time_slot_size)

            frame_xml: Xml.Element = Xml.SubElement(traffic, 'Frame')
            Xml.SubElement(frame_xml, 'FrameID').text = str(frame_id)
            Xml.SubElement(frame_xml, 'Period').text = str(int(frame.period / self.__network.time_slot_size))
            Xml.SubElement(frame_xml, 'Deadline').text = str(int(frame.deadline / self.__network.time_slot_size))
            Xml.SubElement(frame_xml, 'Size').text = str(frame.size)
            Xml.SubElement(frame_xml, 'StartingTime').text = str(int(frame.starting_time /
                                                                     self.__network.time_slot_size))
            Xml.SubElement(frame_xml, 'EndToEndDelay').text = str(int(frame.end_to_end / self.__network.time_slot_size))
            offset_xml: Xml.Element = Xml.SubElement(frame_xml, 'Offset')
            for instance in range(offset.num_instances):
                Xml.SubElement(offset_xml, 'TimeSlots').text = str(time_transmission)
                instance_xml: Xml.Element = Xml.SubElement(offset_xml, 'Instance')
                Xml.SubElement(instance_xml, 'NumInstance').text = str(instance)
                Xml.SubElement(instance_xml, 'MinTransmission').text = str(transmission_range[instance][0])
                Xml.SubElement(instance_xml, 'MaxTransmission').text = str(transmission_range[instance][1])

    def __write_reallocated_traffic_xml(self, traffic: Xml.Element, broken_link_id: int, node_id: int):
        """
        Write the traffic to reallocate to try to get a better solution with the available ranges
        :param traffic: pointer to the traffic xml tree
        :param broken_link_id: broken link identifier
        :param node_id: node that has to patch identifier
        :return: nothing
        """

        # For all the transmission in the broken link, create their available ranges in the link
        position_path = self.__path_activator[broken_link_id].index(node_id)
        link, link_id = self.__network.get_link_data(node_id, self.__path_activator[broken_link_id][position_path + 1])
        frame_id_affected = [frame_id for frame_id, _, _ in self.__network.get_offsets_by_link(broken_link_id)]
        for frame_id, frame, offset in self.__network.get_offsets_by_link(link_id):

            if frame_id not in frame_id_affected:

                # Remember that for reallocated traffic we do not change the path, so the new path is the same link
                transmission_range = self.__network.get_available_transmission_range(frame, offset, link_id, link_id)
                time_transmission = int((frame.size * 1000 / link.speed) / self.__network.time_slot_size)

                frame_xml: Xml.Element = Xml.SubElement(traffic, 'Frame')
                Xml.SubElement(frame_xml, 'FrameID').text = str(frame_id)
                Xml.SubElement(frame_xml, 'Period').text = str(int(frame.period / self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'Deadline').text = str(int(frame.deadline / self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'Size').text = str(frame.size)
                Xml.SubElement(frame_xml, 'StartingTime').text = str(int(frame.starting_time /
                                                                         self.__network.time_slot_size))
                Xml.SubElement(frame_xml, 'EndToEndDelay').text = str(int(frame.end_to_end /
                                                                          self.__network.time_slot_size))
                offset_xml: Xml.Element = Xml.SubElement(frame_xml, 'Offset')
                for instance in range(offset.num_instances):
                    Xml.SubElement(offset_xml, 'TimeSlots').text = str(time_transmission)
                    instance_xml: Xml.Element = Xml.SubElement(offset_xml, 'Instance')
                    Xml.SubElement(instance_xml, 'NumInstance').text = str(instance)
                    Xml.SubElement(instance_xml, 'MinTransmission').text = str(transmission_range[instance][0])
                    Xml.SubElement(instance_xml, 'MaxTransmission').text = str(transmission_range[instance][1])

    def __write_patch_xml(self, patch_file: str, link: Link, link_id: int, node_id: int, broken_link: int) -> None:
        """
        For the given file, write the patch xml file for the scheduler to solve
        :param patch_file: file and path of the patch file
        :param link: information of the link to patch
        :param link_id: link to patch
        :param node_id: node solving the path
        :param broken_link link identifier of the broken link id
        :return: nothing
        """
        top_xml = Xml.Element('Patch')

        # Write the general information, the fix traffic and the traffic to patch
        self.__write_patch_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'), link, link_id)
        self.__write_patch_fixed_traffic_xml(Xml.SubElement(top_xml, 'FixedTraffic'), link_id)
        self.__write_patch_traffic_xml(Xml.SubElement(top_xml, 'Traffic'), broken_link, node_id)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(patch_file, "w") as f:
            f.write(output_xml)

    def __write_optimize_xml(self, optimize_file: str, link: Link, link_id: int, node_id: int,
                             broken_link: int) -> None:
        """
        For the given file, write the patch xml file for the scheduler to solve
        :param optimize_file: file and path of the patch file
        :param link: information of the link to patch
        :param link_id: link to patch
        :param node_id: node solving the path
        :param broken_link link identifier of the broken link id
        :return: nothing
        """
        top_xml = Xml.Element('Optimize')

        # Write the general information, the fix traffic and the traffic to patch
        self.__write_patch_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'), link, link_id)
        self.__write_patch_fixed_traffic_xml(Xml.SubElement(top_xml, 'FixedTraffic'), link_id)
        self.__write_patch_traffic_xml(Xml.SubElement(top_xml, 'Traffic'), broken_link, node_id)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(optimize_file, "w") as f:
            f.write(output_xml)

    def __write_optimize_l2_xml(self, optimize_file: str, link: Link, link_id: int, node_id: int,
                                broken_link: int) -> None:
        """
        For the given file, write the patch xml file for the scheduler to solve
        :param optimize_file: file and path of the patch file
        :param link: information of the link to patch
        :param link_id: link to patch
        :param node_id: node solving the path
        :param broken_link link identifier of the broken link id
        :return: nothing
        """
        top_xml = Xml.Element('Optimize')

        # Write the general information, the fix traffic and the traffic to patch
        self.__write_patch_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'), link, link_id)
        Xml.SubElement(top_xml, 'FixedTraffic')
        traffic_xml = Xml.SubElement(top_xml, 'Traffic')
        self.__write_reallocated_traffic_xml(traffic_xml, broken_link, node_id)
        self.__write_patch_traffic_xml(traffic_xml, broken_link, node_id)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(optimize_file, "w") as f:
            f.write(output_xml)

    def __write_database(self) -> None:
        """
        Write into the csv database for learning purposes
        :return: nothing
        """
        # Only do it if add database is true
        if self.__add_database:

            # Convert the outputs into a pandas data frame
            output = {'Instance': [], 'Broken Link Utilization': [], 'Path Utilization': [], 'Broken Link Offsets': [],
                      'Path Offsets': [], 'Successful': [], 'Patching Time': [], 'Optimization L1 Time': [],
                      'Optimization L2 Time': []}

            for link_id, utilization in self.__utilization_broken_link.items():
                for path_link_id, utilization_path in self.__utilization_new_path[link_id].items():

                    output['Instance'].append(1)
                    output['Broken Link Utilization'].append(utilization)
                    output['Path Utilization'].append(utilization_path)
                    output['Broken Link Offsets'].append(self.__offsets_broken_link[link_id])
                    output['Path Offsets'].append(self.__offsets_new_path[link_id][path_link_id])
                    output['Successful'].append(self.__successful_heal[link_id])
                    output['Patching Time'].append(self.__patching_time[link_id][path_link_id])
                    output['Optimization L1 Time'].append(self.__optimization_L1_time[link_id][path_link_id])
                    output['Optimization L2 Time'].append(self.__optimization_L2_time[link_id][path_link_id])

            data = pandas.DataFrame(output)

            # Add header if the database file is not created
            if isfile('../Files/Database/Database.csv'):
                with open('../Files/Database/Database.csv', 'a') as database_file:
                    data.to_csv(database_file, header=False, index=False)
            else:
                with open('../Files/Database/Database.csv', 'w') as database_file:
                    data.to_csv(database_file, index=False)
