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

from enum import Enum
from typing import NamedTuple, Dict, List, Tuple, Union
from Network import Network
from Link import Link
from operator import attrgetter, itemgetter
from SimulatedNode import SimulatedNode
from math import ceil, log2, floor
from Event import InternalEvent, FrameEvent, ExecutionEvent
from xml.dom import minidom
from subprocess import run
from os import remove
from os.path import isfile
import xml.etree.ElementTree as Xml
import pandas


class Simulation:
    """
    Simulates events that happen to a scheduled network and how it reacts, providing outputs
    """

    # Exceptions #

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

    # Auxiliary Classes #

    class Algorithm(Enum):
        ISHP = 'ISHP'

    # Named Tuples #

    class EventsStarters(NamedTuple):
        class Component(Enum):
            Link = 'Link'
            Node = 'Node'

        component_type: Component  # Type of component
        component_ID: int  # ID of the component
        time: int  # Time when the event happens (or is detected)

    # Constants #

    __MAX_SIMULATION_TIME = 999999999999999999999999999999999

    # Sizes
    __SIZE_CODE_LINK = 5
    __SIZE_CODE_FRAME = 3
    __SIZE_CODE_TRANS = 32
    __SIZE_CODE_FRAME_ID = 4
    __SIZE_CODE_INST = 4

    # Init #

    def __init__(self, network: Network):
        """
        Init of the simulator
        :param network: given scheduled network to simulate
        """
        self.__algorithm = None  # Algorithm to execute in the simulation
        self.__add_database: bool = False  # Add information of the simulation to the database
        self.__time_classification: int = 100000000  # Maximum time we can tolerate
        self.__network = network  # Network being simulated
        self.__protocol = self.__network.healing_protocol  # Bandwidth reservation protocol
        self.__events: List[Simulation.EventsStarters] = []  # Sorted list of events to simulate
        self.__nodes: Dict[int, SimulatedNode] = {}  # Simulated nodes by node id
        self.__link_usage: Dict[int, List[Tuple[str, int, int]]] = {}  # Dictionary of transmission usage for testing
        self.__high_switches: Dict[int, List[int]] = {}  # High-performance switches and who belongs to it
        self.__belong_high: Dict[int, int] = {}  # Node belonging to the high-performance switch
        # Path from the high-performance switch to each of its belonging nodes and the other way around
        self.__path_high: Dict[Tuple[int, int], Tuple[List[int], List[int]]] = {}

        # Information related to a failure instance
        self.__leader: Dict[int, int] = {}  # High-performance switch that will re-schedule all
        self.__activator: Dict[int, int] = {}  # Node that found the failure
        self.__new_path: Dict[int, List[int]] = {}  # New path for the broken link in nodes
        self.__new_path_links: Dict[int, List[int]] = {}  # New path for the broken link in links

        # Information for the database
        self.__utilization_broken_link: Dict[int, float] = {}  # Utilization of the broken link
        self.__utilization_new_path: Dict[int, Dict[int, float]] = {}  # Utilization of the new path
        self.__offsets_broken_link: Dict[int, int] = {}  # Number of offsets in the broken link
        self.__offsets_new_path: Dict[int, Dict[int, int]] = {}  # Number of offsets in the new path
        self.__successful_heal: Dict[int, bool] = {}  # Could the broken link be repaired
        self.__patching_time: Dict[int, Dict[int, int]] = {}  # Time to patch the broken link
        self.__optimize_time: Dict[int, Dict[int, int]] = {}  # Time to optimize the broken link

        # Information for the results
        self.__time_started: Dict[int, int] = {}  # Time when the failure was detected
        self.__time_patched: Dict[int, int] = {}  # Time from the link error to have the patch running
        self.__time_optimized: Dict[int, int] = {}  # Same but for the optimization
        self.__no_path: Dict[int, bool] = {}  # Failed because no path
        self.__no_schedule: Dict[int, bool] = {}  # Failure because no schedule
        self.__no_transmission: Dict[int, bool] = {}    # There were no transmissions in the link

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
        if self.__algorithm is self.Algorithm.ISHP:
            for event in self.__events:

                if event.component_type != self.EventsStarters.Component.Link:
                    raise ValueError('The SHP can only repair links')

                self.__time_started[event.component_ID] = event.time
                receiver_id = self.__network.get_receiver_id_link(event.component_ID)
                self.__nodes[receiver_id].add_event(InternalEvent(event.component_ID, 'LinkFailure', event.time))

    def __simulate_execution_event(self, event: ExecutionEvent, node_id: int) -> None:
        """
        Check which execution event is and simulate it
        :param event: event to simulate
        :param node_id: node id of the event to simulate
        :return: nothing
        """
        if event.name is ExecutionEvent.ExecutionName.Patch:

            # For all links in the new path, create the patching file and execute it
            size_schedule = []
            for link_it, link_id in enumerate(self.__new_path_links[event.event_id]):
                size_schedule.append(0)
                link = self.__network.get_link(link_id)

                patch_file = '../Files/Outputs/Patch_' + str(event.event_id) + '_' + str(link_id) + '.xml'
                patched_file = '../Files/Outputs/PatchedSchedule_' + str(event.event_id) + '_' + str(link_id) + '.xml'
                execution_file = '../Files/Outputs/Execution.xml'

                transmission_ranges: Dict[int, List[List[int]]] = {}

                for frame_id, frame, offset in self.__network.get_offsets_by_link(event.event_id):
                    if frame_id == 1 and link_id == 14:
                        print('hello')

                    transmission_ranges[frame_id] = self.__network.get_atr(frame, offset, event.event_id,
                                                                           self.__new_path_links[event.event_id],
                                                                           link_id)

                    size_schedule[link_it] += self.__SIZE_CODE_FRAME_ID
                    bit_trans = self.__SIZE_CODE_INST + self.__SIZE_CODE_TRANS
                    size_schedule[link_it] += bit_trans * len(transmission_ranges[frame_id])

                self.__write_patch_xml(patch_file, link, link_id, transmission_ranges)
                run(['./../Files/Executables/Patch', patch_file, patched_file, execution_file])

                self.__read_execution_time_xml(execution_file)
                self.__patching_time[event.event_id][link_id] = self.__execution_time
                remove(patch_file)
                remove(execution_file)

                if isfile(patched_file):
                    pass
                    remove(patched_file)

            # We assume parallel patching execution
            time_patch = max(self.__patching_time[event.event_id].values()) + event.time
            for node_it, patch_node_id in enumerate(self.__new_path[event.event_id][1:]):
                size = self.__SIZE_CODE_FRAME_ID + size_schedule[node_it]
                path = self.__path_high[(self.__leader[event.event_id], patch_node_id)][0]
                self.__nodes[node_id].add_event(FrameEvent(event.event_id, 'DistributeSchedulePatch', time_patch,
                                                           size, path))

            self.__nodes[node_id].add_event(ExecutionEvent(event.event_id, 'Optimize', time_patch))

        elif event.name is ExecutionEvent.ExecutionName.Optimize:

            size_schedule = []
            # For all links in the new path, create the optimization file and execute it
            for link_it, link_id in enumerate(self.__new_path_links[event.event_id]):
                size_schedule.append(0)
                link = self.__network.get_link(link_id)

                optimize_file = '../Files/Outputs/Optimize_' + str(event.event_id) + '_' + str(link_id) + '.xml'
                optimized_file = '../Files/Outputs/OptimizedSchedule_' + str(event.event_id) + '_' + str(link_id) \
                                 + '.xml'
                execution_file = '../Files/Outputs/Execution.xml'

                transmission_ranges: Dict[int, List[List[int]]] = {}

                for frame_id, frame, offset in self.__network.get_offsets_by_link(event.event_id):
                    transmission_ranges[frame_id] = self.__network.get_atr(frame, offset, event.event_id,
                                                                           self.__new_path_links[event.event_id],
                                                                           link_id)

                    size_schedule[link_it] += self.__SIZE_CODE_FRAME_ID
                    bit_trans = self.__SIZE_CODE_INST + self.__SIZE_CODE_TRANS
                    size_schedule[link_it] += bit_trans * len(transmission_ranges[frame_id])

                self.__write_optimize_xml(optimize_file, link, link_id, transmission_ranges)
                run(['./../Files/Executables/Optimize', optimize_file, optimized_file, execution_file])

                self.__read_execution_time_xml(execution_file)
                self.__optimize_time[event.event_id][link_id] = self.__execution_time
                remove(optimize_file)
                remove(execution_file)

                if isfile(optimized_file):
                    self.__read_patched_schedule_xml(optimized_file, event.event_id)
                    remove(optimized_file)

                else:
                    self.__no_schedule[event.event_id] = True
                    raise self.NoSchedule('Optimization step failed, no schedule found')

            # We assume parallel patching execution
            time_optimize = max(self.__optimize_time[event.event_id].values()) + event.time
            for node_it, patch_node_id in enumerate(self.__new_path[event.event_id][1:]):
                size = self.__SIZE_CODE_FRAME_ID + size_schedule[node_it]
                path = self.__path_high[(self.__leader[event.event_id], patch_node_id)][0]
                self.__nodes[node_id].add_event(FrameEvent(event.event_id, 'DistributeScheduleOptimize', time_optimize,
                                                           size, path))

            # Update the paths
            for frame_id, frame in self.__network.frames.items():
                for receiver_id in frame.receivers_id:
                    path: List[int] = list(frame.get_path(receiver_id))
                    if event.event_id in path:
                        path.remove(event.event_id)

                        # Add the new path
                        not_loop_path = frame.get_path(receiver_id)
                        index_link = not_loop_path.index(event.event_id)
                        not_loop_path.remove(event.event_id)
                        not_loop_path[index_link:index_link] = self.__new_path_links[event.event_id]

                        # Remove the loop if there exists one
                        receivers_paths = [self.__network.get_receiver_id_link(link) for link in path]
                        for new_link_path in self.__new_path_links[event.event_id]:
                            if self.__network.get_receiver_id_link(new_link_path) in receivers_paths:

                                # Case when the receivers are the same
                                index = receivers_paths.index(self.__network.get_receiver_id_link(new_link_path))
                                link_loop = path[index]
                                first_index = not_loop_path.index(new_link_path)
                                last_index = not_loop_path.index(link_loop)
                                for _ in range(first_index, last_index):
                                    not_loop_path.pop(first_index + 1)

                                # Special case when the new link path and the link loop are the same
                                # Remove all the links in between the two repeated links
                                if new_link_path == link_loop:
                                    not_loop_path.pop(first_index)
                                    last_index = not_loop_path.index(link_loop)
                                    for _ in range(first_index, last_index):
                                        not_loop_path.pop(first_index)

                                break

            # Remove unused offsets once the network has been repaired
            for frame in self.__network.frames.values():
                frame.remove_unused_offsets()

            # Check if everything was done properly and update database and utilization
            self.__network.check_schedule()
            self.__write_database(event.event_id)
            self.__network.update_utilization()

        else:
            raise ValueError('Execution Event not recognized')

    def __simulate_frame_event(self, event: FrameEvent, node_id: int) -> None:
        """
        Check which frame event is and simulate it
        :param event: event to simulate
        :param node_id: node id of the event to simulate
        :return: nothing
        """
        if event.name in [FrameEvent.FrameName.NotificationHS, FrameEvent.FrameName.DistributeSchedulePatch,
                          FrameEvent.FrameName.DistributeScheduleOptimize]:
            self.__simulate_single_frame(event, node_id)

    def __simulate_single_frame(self, event: FrameEvent, node_id: int) -> None:
        """
        Simulates a frame event that is being transmitted over the network
        :param event: event to simulate
        :param node_id: node that receives the frame event
        :return: nothing
        """
        if event.name is FrameEvent.FrameName.NotificationHS:
            if event.last_node(node_id):  # If it has arrived to its destination
                self.__nodes[node_id].add_event(ExecutionEvent(event.event_id, 'Patch', event.time))
                return
            else:  # If not, continue transmitting the frame
                index_path = event.path.index(node_id)
                receiver_id = event.path[index_path + 1]
                processing_time = 0
                size = event.size

        elif event.name is FrameEvent.FrameName.DistributeSchedulePatch:
            if event.last_node(node_id):

                # Calculate the time when we update the schedule and save it
                time_update = event.time - (event.time % self.__network.healing_protocol.period)
                time_update += self.__network.healing_protocol.period
                time_patch = time_update - self.__time_started[event.event_id]

                if event.event_id in self.__time_patched.keys():
                    self.__time_patched[event.event_id] = max(self.__time_patched[event.event_id], time_patch)
                else:
                    self.__time_patched[event.event_id] = time_patch

                return
            else:
                index_path = event.path.index(node_id)
                receiver_id = event.path[index_path + 1]
                size = event.size
                processing_time = 0

        elif event.name is FrameEvent.FrameName.DistributeScheduleOptimize:
            if event.last_node(node_id):

                # Calculate the time when we update the schedule and save it
                time_update = event.time - (event.time % self.__network.healing_protocol.period)
                time_update += self.__network.healing_protocol.period
                time_optimize = time_update - self.__time_started[event.event_id]

                if event.event_id in self.__time_optimized.keys():
                    self.__time_optimized[event.event_id] = max(self.__time_optimized[event.event_id], time_optimize)
                else:
                    self.__time_optimized[event.event_id] = time_optimize

                return
            else:
                index_path = event.path.index(node_id)
                receiver_id = event.path[index_path + 1]
                size = event.size
                processing_time = 0

        else:
            raise ValueError('We do not support the given frame event')

        # Calculate timings when the event can be sent
        link, link_id = self.__network.get_link_data(node_id, receiver_id)
        time_event = self.__find_time_event(event.time, size, event.name, link, link_id, processing_time)

        # Add the event
        self.__nodes[receiver_id].add_event(FrameEvent(event.event_id, event.name, time_event, size, event.path))

    def __simulate_internal_event(self, event: InternalEvent) -> None:
        """
        Simulates an internal event, such as a component failure
        :param event: event to simulate
        :return: nothing
        """
        if event.name is InternalEvent.InternalName.LinkFailure:

            print('Starting repairing Link ' + str(event.event_id))

            # Sender and receivers of the broken link
            sender_id = self.__network.get_sender_id_link(event.event_id)
            receiver_id = self.__network.get_receiver_id_link(event.event_id)
            high_switch = self.__belong_high[receiver_id]

            self.__network.remove_link(event.event_id)  # Remove the link from the network

            if self.__network.get_num_offsets(event.event_id) == 0:  # Nothing to do if there are no transmissions
                self.__no_transmission[event.event_id] = True
                return

            try:
                self.__new_path[event.event_id] = self.__network.get_shortest_path_no_end_systems(sender_id,
                                                                                                  receiver_id)
            except ValueError:
                self.__no_path[event.event_id] = True
                raise Simulation.NoPath('The link failure cannot be repaired as there is no path to connect')

            # Update the path to the high performance switch in the affected systems
            try:
                for high_switch_id in self.__high_switches.keys():

                    # for node_id in self.__high_switches[high_switch_id]:
                    #    path_switch = self.__network.get_shortest_path_no_end_systems(high_switch_id, node_id)
                    #    path_node = self.__network.get_shortest_path_no_end_systems(node_id, high_switch_id)
                    #    self.__path_high[(high_switch_id, node_id)] = (path_switch, path_node)

                    # for node_id in self.__high_switches.keys():
                    #    path_switch = self.__network.get_shortest_path_no_end_systems(high_switch_id, node_id)
                    #    path_node = self.__network.get_shortest_path_no_end_systems(node_id, high_switch_id)
                    #    self.__path_high[(high_switch_id, node_id)] = (path_switch, path_node)

                    for node_id in self.__network.nodes_id:
                        path_switch = self.__network.get_shortest_path_no_end_systems(high_switch_id, node_id)
                        path_node = self.__network.get_shortest_path_no_end_systems(node_id, high_switch_id)
                        self.__path_high[(high_switch_id, node_id)] = (path_switch, path_node)
            except ValueError:
                self.__no_path[event.event_id] = True
                raise Simulation.NoPath('No path to connect to the high-performance switch')

            # Collect information needed to simulate the whole process
            self.__leader[event.event_id] = high_switch
            self.__activator[event.event_id] = receiver_id

            # Convert some of the needed paths from node ids to link ids
            self.__new_path_links[event.event_id] = self.__network.path_nodes_to_links(self.__new_path[event.event_id])

            # Start the event to notify the high-performance switch
            size = self.__SIZE_CODE_FRAME
            size += self.__SIZE_CODE_LINK * (len(self.__path_high[(high_switch, receiver_id)][1]) - 1)
            path = self.__path_high[(high_switch, receiver_id)][1]  # Path from the receiver to its high switch
            self.__nodes[receiver_id].add_event(FrameEvent(event.event_id, 'NotificationHS', event.time, size, path))

            # Save the utilization and number of offsets in the database
            self.__save_utilization_database(event.event_id)
            self.__save_num_offsets_database(event.event_id)

        else:
            raise ValueError('Internal Event not recognized')

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

        time_data = int(size * 1000 / 8 / link.speed)  # Time to transmit the data
        starting = time  # Time when the event starts

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
            time_event -= (floor((time_event % self.__protocol.period) /
                                 self.__protocol.time) - 1) * self.__protocol.time

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

        self.__link_usage[link_id].sort(key=itemgetter(1))  # Sort for a more easy pretty printing
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
        self.__optimize_time[broken_link_id] = {}

        # Add utilization
        try:
            self.__utilization_broken_link[broken_link_id] = self.__network.link_utilization[broken_link_id]
        except KeyError:
            self.__utilization_broken_link[broken_link_id] = 0.0
        self.__utilization_new_path[broken_link_id] = {}
        for link_id in self.__new_path_links[broken_link_id]:
            try:
                link_ut = self.__network.link_utilization[link_id]
            except KeyError:
                link_ut = 0.0
            self.__utilization_new_path[broken_link_id][link_id] = link_ut

    def __save_num_offsets_database(self, broken_link_id: int) -> None:
        """
        Save the number of offsets in the broken link and the new path for the database
        :param broken_link_id: broken link identifier
        :return: nothing
        """
        self.__offsets_broken_link[broken_link_id] = self.__network.get_num_offsets(broken_link_id)
        self.__offsets_new_path[broken_link_id] = {}
        for link_id in self.__new_path_links[broken_link_id]:
            self.__offsets_new_path[broken_link_id][link_id] = self.__network.get_num_offsets(link_id)

    # Simulate Functions #

    def simulate(self) -> None:
        """
        Given the simulated nodes and its events, simulate all the executions
        :return: nothing
        """
        event, node_id = self.__select_next_event()
        # While there are events to simulate, keep simulating
        while event is not None:
            if type(event) is InternalEvent:
                self.__simulate_internal_event(event)

            elif type(event) is FrameEvent:
                self.__simulate_frame_event(event, node_id)

            elif type(event) is ExecutionEvent:
                self.__simulate_execution_event(event, node_id)

            else:
                raise ValueError('Event not recognized')

            event, node_id = self.__select_next_event()

        # Test everything done was correct and there are no collisions in the schedule or the protocol bandwidth
        self.__test_link_usage()
        self.__network.check_schedule()

        # Write the simulation instance

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
                Xml.SubElement(frame_xml, 'Deadline').text = str(int(frame.deadline /
                                                                     self.__network.time_slot_size))
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

    def __write_patch_traffic_xml(self, traffic: Xml.Element, link: Link, link_id: int,
                                  ranges: Dict[int, List[List[int]]]) -> None:
        """
        Write the traffic to patch with the available ranges
        :param traffic: pointer to the traffic xml tree
        :param link: link where the new traffic is transmitted
        :param link_id: link to patch
        :param ranges: dictionary with all the frame ids to add and its transmission ranges
        :return: nothing
        """
        already_frame_id: List[int] = []
        for frame_id, _, _ in self.__network.get_offsets_by_link(link_id):
            already_frame_id.append(frame_id)

        # For all the transmission in the broken link, create their available ranges in the link
        for frame_id, transmission_ranges in ranges.items():

            if frame_id in already_frame_id:
                # print('Take care of this case, a frame that needs to be patched is already fixed')
                pass

            frame = self.__network.frames[frame_id]

            time_transmission = int((frame.size * 1000 / link.speed) / self.__network.time_slot_size)

            if link_id not in frame.offsets.keys():

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
                for instance in range(len(transmission_ranges)):
                    Xml.SubElement(offset_xml, 'TimeSlots').text = str(time_transmission)
                    instance_xml: Xml.Element = Xml.SubElement(offset_xml, 'Instance')
                    Xml.SubElement(instance_xml, 'NumInstance').text = str(instance)
                    Xml.SubElement(instance_xml, 'MinTransmission').text = str(transmission_ranges[instance][0])
                    Xml.SubElement(instance_xml, 'MaxTransmission').text = str(transmission_ranges[instance][1])

    def __write_patch_xml(self, patch_file: str, link: Link, link_id: int, ranges: Dict[int, List[List[int]]]) -> None:
        """
        For the given file, write the patch xml file for the scheduler to solve
        :param patch_file: file and path of the patch file
        :param link: information of the link to patch
        :param link_id: link to patch
        :param ranges: dictionary with all the frame ids to add and its transmission ranges
        :return: nothing
        """
        top_xml = Xml.Element('Patch')

        # Write the general information, the fix traffic and the traffic to patch
        self.__write_patch_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'), link, link_id)
        self.__write_patch_fixed_traffic_xml(Xml.SubElement(top_xml, 'FixedTraffic'), link_id)
        self.__write_patch_traffic_xml(Xml.SubElement(top_xml, 'Traffic'), link, link_id, ranges)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(patch_file, "w") as f:
            f.write(output_xml)

    def __write_optimize_xml(self, patch_file: str, link: Link, link_id: int,
                             ranges: Dict[int, List[List[int]]]) -> None:
        """
        For the given file, write the optimize xml file for the scheduler to solve
        :param patch_file: file and path of the patch file
        :param link: information of the link to patch
        :param link_id: link to patch
        :param ranges: dictionary with all the frame ids to add and its transmission ranges
        :return: nothing
        """
        top_xml = Xml.Element('Optimize')

        # Write the general information, the fix traffic and the traffic to patch
        self.__write_patch_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'), link, link_id)
        self.__write_patch_fixed_traffic_xml(Xml.SubElement(top_xml, 'FixedTraffic'), link_id)
        self.__write_patch_traffic_xml(Xml.SubElement(top_xml, 'Traffic'), link, link_id, ranges)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(patch_file, "w") as f:
            f.write(output_xml)

    def write_simulation_instance_xml(self, simulation_file: str) -> None:
        """
        Write interesting information of a simulation instance
        :param simulation_file: path and name of the simulation instance
        :return: nothing
        """
        top_xml = Xml.Element('SimulationInformation')

        # For all the failures
        for it, link_id in enumerate(self.__time_started.keys()):
            failure_xml = Xml.SubElement(top_xml, 'FailureInstance')
            Xml.SubElement(failure_xml, 'Instance').text = str(it)
            Xml.SubElement(failure_xml, 'Link').text = str(link_id)

            # No transmissions, the SHP does not get activated
            if link_id in self.__no_transmission.keys():
                Xml.SubElement(failure_xml, 'NoTransmission').text = '1'
            else:
                Xml.SubElement(failure_xml, 'NoTransmission').text = '0'
                Xml.SubElement(failure_xml, 'TimeDetected').text = str(self.__time_started[link_id])
                try:
                    Xml.SubElement(failure_xml, 'Healed').text = '1' if self.__successful_heal[link_id] else '0'
                except KeyError:
                    Xml.SubElement(failure_xml, 'Healed').text = '0'
                try:
                    Xml.SubElement(failure_xml, 'NoPath').text = '1' if self.__no_path[link_id] else '0'
                except KeyError:
                    Xml.SubElement(failure_xml, 'NoPath').text = '0'
                try:
                    Xml.SubElement(failure_xml, 'NoSchedule').text = '1' if self.__no_schedule[link_id] else '0'
                except KeyError:
                    Xml.SubElement(failure_xml, 'NoSchedule').text = '0'
                if link_id in self.__successful_heal.keys():
                    try:
                        Xml.SubElement(failure_xml, 'TimePatched').text = str(self.__time_patched[link_id])
                    except KeyError:
                        Xml.SubElement(failure_xml, 'TimePatched').text = '0'
                    try:
                        Xml.SubElement(failure_xml, 'TimeOptimized').text = str(self.__time_optimized[link_id])
                    except KeyError:
                        Xml.SubElement(failure_xml, 'TimeOptimized').text = '0'

        # Write the temporal configuration file to obtain the network and schedule
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(simulation_file, "w") as f:
            f.write(output_xml)

    def write_simulation_master_xml(self, simulation_file: str) -> None:
        """
        Write simulation files with interesting information.
        Master simulation file has information valid for all the simulations
        :param simulation_file: path and name of the simulation folder and name
        :return: nothing
        """
        top_xml = Xml.Element('SimulationInformation')

        # Write the utilization information
        utilization_xml: Xml.Element = Xml.SubElement(top_xml, 'Utilization')
        Xml.SubElement(utilization_xml, 'Overall').text = str(self.__network.utilization)
        for link_id, utilization in self.__network.link_utilization.items():
            link_utilization_xml: Xml.Element = Xml.SubElement(utilization_xml, 'LinkUtilization')
            Xml.SubElement(link_utilization_xml, 'LinkID').text = str(link_id)
            Xml.SubElement(link_utilization_xml, 'Utilization').text = str(utilization)

        # Write the temporal configuration file to obtain the network and schedule
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(simulation_file, "w") as f:
            f.write(output_xml)

    def __write_database(self, link_id: int) -> None:
        """
        Write into the csv database for learning purposes
        :param link_id: id of the data to write
        :return: nothing
        """
        # Only do it if add database is true
        if self.__add_database:

            # Convert the outputs into a pandas data frame
            output = {'Instance': [], 'Broken Link Utilization': [], 'Path Utilization': [], 'Total Utilization': [],
                      'Broken Link Offsets': [], 'Path Offsets': [], 'Total Offsets': [], 'Successful': [],
                      'Patching Time': [], 'Optimization Time': [], 'Classification': []}

            for path_link_id, utilization_path in self.__utilization_new_path[link_id].items():
                output['Instance'].append(1)
                output['Broken Link Utilization'].append(self.__utilization_broken_link[link_id])
                output['Path Utilization'].append(utilization_path)
                output['Total Utilization'].append(utilization_path + self.__utilization_broken_link[link_id])
                output['Broken Link Offsets'].append(self.__offsets_broken_link[link_id])
                output['Path Offsets'].append(self.__offsets_new_path[link_id][path_link_id])
                output['Total Offsets'].append(self.__offsets_broken_link[link_id] +
                                               self.__offsets_new_path[link_id][path_link_id])
                output['Successful'].append(self.__successful_heal[link_id])
                if self.__successful_heal[link_id]:
                    output['Patching Time'].append(self.__patching_time[link_id][path_link_id])
                    output['Optimization Time'].append(self.__optimize_time[link_id][path_link_id])
                    out = 2 if self.__optimize_time[link_id][path_link_id] > self.__time_classification else 1
                    output['Classification'].append(out)
                else:
                    output['Patching Time'].append(self.__patching_time[link_id][path_link_id])
                    output['Optimization Time'].append(self.__optimize_time[link_id][path_link_id])
                    output['Classification'].append(0)

            data = pandas.DataFrame(output)

            # Add header if the database file is not created
            if isfile('../Files/Database/Database.csv'):
                with open('../Files/Database/Database.csv', 'a') as database_file:
                    data.to_csv(database_file, header=False, index=False)
            else:
                with open('../Files/Database/Database.csv', 'w') as database_file:
                    data.to_csv(database_file, index=False)

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
        self.__add_database = True if simulation_xml.find('AddDatabase').text == '1' else False
        self.__read_events_xml(simulation_xml.find('Events'))

        self.__prepare_simulation()

    def __read_special_nodes(self, special_nodes_xml: Xml.Element) -> None:
        """
        Read the special nodes information and save it
        :param special_nodes_xml: pointer to the special nodes information xml tree
        :return: nothing
        """
        # For all high performance switches, add them and all the nodes that belong to him
        for high_switch_xml in special_nodes_xml.findall('HighPerformanceSwitch'):  # type: Xml.Element
            high_switch_id = int(high_switch_xml.find('NodeID').text)
            self.__high_switches[high_switch_id] = []

            # Add the high switch too
            self.__high_switches[high_switch_id].append(high_switch_id)
            self.__belong_high[high_switch_id] = high_switch_id

            # For all the nodes that belong to the performance node, init the data
            member_nodes_xml: Xml.Element = high_switch_xml.find('MemberNodes')
            for node_xml in member_nodes_xml.findall('NodeID'):     # type: Xml.Element
                node_id = int(node_xml.text)
                self.__high_switches[high_switch_id].append(node_id)
                self.__belong_high[node_id] = high_switch_id

    def __read_general_information_xml(self, general_info_xml: Xml.Element) -> None:
        """
        Read the general information of the simulation
        :param general_info_xml: pointer to the general information xml tree
        :return: nothing
        """
        self.__algorithm: Simulation.Algorithm = self.Algorithm[general_info_xml.find('Algorithm').text]
        if self.__algorithm.ISHP:
            self.__read_special_nodes(general_info_xml.find('SpecialNodes'))
        try:
            self.__time_classification = int(general_info_xml.find('TimeClassification').text)
        except AttributeError:
            self.__add_database = False

    def __read_events_xml(self, events_xml: Xml.Element) -> None:
        """
        Read the events to simulate
        :param events_xml: pointer to the events information xml tree
        :return: nothing
        """
        # For all events, save it into the event simulator
        for failure_xml in events_xml.findall('Failure'):  # type: Xml.Element
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
        for frame_xml in root_xml.findall('TrafficInformation/Frame'):  # type: Xml.Element
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
