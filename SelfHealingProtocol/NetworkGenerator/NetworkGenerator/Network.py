# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Network Class                                                                                                      *
 *  NetworkGenerator                                                                                                   *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/12/18.                                                                             *
 *  Copyright © 2018 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class with the information of the network and algorithms to create them. It uses the package NetworkX.             *
 *  Different number of frames and types of frames frames (single, broadcast, etc) and dependencies and attributes of  *
 *  the network are also created.                                                                                      *
 *  As the number of parameters is large, standard configuration of parameters are also available.                     *
 *  It includes input and output for the xml files.                                                                    *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from enforce import runtime_validation
from random import choice, shuffle, randint
from copy import copy
import xml.etree.ElementTree as Xml
from xml.dom import minidom
import networkx
from enum import Enum
from typing import NamedTuple, List, Tuple, Dict
from Node import Node
from Link import Link
from Frame import Frame


@runtime_validation
class Network:
    """
    Network class with the information of the whole network, frames and dependencies that contains.
    It includes algorithms to construct them by given generic parameters or full network information.
    Parameters can be read from a XML file and the resulting network is written in another XML file.
    """

    # Auxiliary Classes #

    class TimeUnit(Enum):
        """
        Time Unit class to to take different units
        """
        ns = 'ns'  # Nanoseconds
        us = 'us'  # Microseconds
        ms = 'ms'  # Milliseconds
        s = 's'  # Seconds

        @staticmethod
        def convert_ns(value: int, unit: str) -> int:
            """
            Convert the given value and unit to nanoseconds
            :param value: value to convert
            :param unit: unit of the given value
            :return: value converted to nanoseconds
            """
            if unit == Network.TimeUnit.ns.name:
                return value
            if unit == Network.TimeUnit.us.name:
                return value * 1000
            if unit == Network.TimeUnit.ms.name:
                return value * 1000000
            if unit == Network.TimeUnit.ns.name:
                return value * 1000000000
            raise TypeError('The unit is not recognized or supported')

    class SelfHealingProtocol:
        """
        Self-Healing Protocol class to save its information
        """

        def __init__(self, period: int, time: int) -> None:
            """
            Init the self healing protocol variables
            :param period: period of the protocol in ns
            :param time: time of the protocol in ns
            """
            self.time = time
            self.period = period

        # Getters #

        @property
        def time(self) -> int:
            """
            Get the time of the protocol
            :return: time of the protocol in ns
            """
            return self.__time

        @property
        def period(self) -> int:
            """
            Get the period of the protocol
            :return: period of the protocol in ns
            """
            return self.__period

        # Setters #

        @time.setter
        def time(self, value: int) -> None:
            """
            Set the time of the protocol
            :param value: time of the protocol in ns
            :return: nothing
            """
            # The value must be at least one
            if value < 1:
                raise ValueError('The time of the protocol should be a positive number')
            self.__time = value

        @period.setter
        def period(self, value: int) -> None:
            """
            Set the period of the protocol
            :param value: period of the protocol in ns
            :return: nothing
            """
            if value < 1:
                raise ValueError('The period of the protocol should be a positive number')
            if value < self.__time:
                raise ValueError('The period of the protocol must be larger than the time')
            self.__period = value

    class TopologyDescription:
        """
        Class that saves the topology description that can be used to create a network later on
        """

        # Named tuple of the topology description
        # Node ID, Node object, list of connections link IDs, list of Links objects
        class NodeConnection(NamedTuple):
            receiverID: int
            linkID: int
            link: Link

        class NodeDescription(NamedTuple):
            nodeID: int
            node: Node
            connections: List

        def __init__(self, value: List[NodeDescription]) -> None:
            """
            Init the topology to empty
            """
            self.description = value
            # self.__description = value       # Topology Description in a named tuple

        # Getters #

        @property
        def description(self) -> List[NodeDescription]:
            """
            Get the topology description
            :return: named tuple with the topology description
            """
            return self.__description

        # Setters #

        @description.setter
        def description(self, value: List[NodeDescription]) -> None:
            """
            Set the topology description
            :param value: topology description named tuple
            :return: nothing
            """
            self.__description = value

    # Named Tuples #

    class TrafficInformation(NamedTuple):
        num_frames: int
        num_single: int  # Number of frames with one receiver
        num_local: int  # Number of frames with that sends to all nodes with path 2 (or larger if not possible)
        num_multiple: int  # Number of frames with random multiple receivers
        num_broadcast: int  # Number of frames with all end systems as receivers

    class FrameDescription(NamedTuple):
        num_frames: int  # Number of frames with the current description
        period: int  # Period of the frame in nanoseconds
        deadline: int  # Deadline of the frame in nanoseconds
        size: int  # Size of the frame in Bytes
        starting_time: int  # Starting time or offset to start after the period in nanoseconds
        end_to_end: int  # Maximum time in nanoseconds from the transmission to the reception of the frame

    # Init #

    def __init__(self):
        """
        Init of the Network
        """
        self.__graph = networkx.OrderedDiGraph()  # Graph with the information of the topology in NetworkX
        self.__minimum_switch_time = 0  # Minimum processing time in the switch in ns
        self.__healing_protocol = None  # Self Healing Protocol values
        self.__topology_description = None  # Information with the topology description in a named tuple
        self.__num_frames = 0  # Number of frames in the network
        self.__traffic_information = None  # Traffic information to generate traffic
        self.__frame_description = []  # List of different frame descriptions
        self.__frames = {}  # List of frame objects

    # Getters #

    @property
    def minimum_switch_time(self) -> int:
        """
        Get the minimum switch time in ns
        :return: minimum switch time in ns
        """
        return self.__minimum_switch_time

    @property
    def healing_protocol(self) -> SelfHealingProtocol:
        """
        Get the self healing protocol information
        :return: self healing protocol information
        """
        return self.__healing_protocol

    @property
    def topology_description(self) -> TopologyDescription:
        """
        Get the topology description
        :return: topology description class
        """
        return self.__topology_description

    @property
    def num_frames(self) -> int:
        """
        Get the number of frames
        :return: number of frames
        """
        return self.__num_frames

    @property
    def traffic_information(self) -> TrafficInformation:
        """
        Get the traffic information
        :return: traffic information
        """
        return self.__traffic_information

    @property
    def frame_description(self) -> List[FrameDescription]:
        """
        Get the frame descriptions
        :return: list with all the frame descriptions
        """
        return self.__frame_description

    @property
    def frames(self) -> Dict[int, Frame]:
        return self.__frames

    # Setters #

    @minimum_switch_time.setter
    def minimum_switch_time(self, value: int) -> None:
        """
        Set the minimum switch time in ns
        :param value: minimum switch time in ns
        :return: nothing
        """
        # At least should be 0
        if value < 0:
            raise ValueError('The minimum switch time should be a positive number')
        self.__minimum_switch_time = value

    @healing_protocol.setter
    def healing_protocol(self, value: SelfHealingProtocol) -> None:
        """
        Set the self healing protocol class with its information
        :param value: self healing protocol class
        :return: nothing
        """
        self.__healing_protocol = value

    @topology_description.setter
    def topology_description(self, value: TopologyDescription) -> None:
        """
        Set the topology description
        :param value: topology description class
        :return: nothing
        """
        self.__topology_description = value

    @traffic_information.setter
    def traffic_information(self, value: TrafficInformation) -> None:
        """
        Set the traffic information
        :param value: named tuple with the number of frames information
        :return: nothing
        """
        if value.num_frames != (value.num_single + value.num_local + value.num_multiple + value.num_broadcast):
            raise ValueError('The number of all different frames should be the same as the defined number of frames')
        if value.num_frames < 0:
            raise ValueError('The number of frames should be positive')
        if value.num_single < 0:
            raise ValueError('The number of single frames should be positive')
        if value.num_local < 0:
            raise ValueError('The number of local frames should be positive')
        if value.num_multiple < 0:
            raise ValueError('The number of multiple frames should be positive')
        if value.num_broadcast < 0:
            raise ValueError('The number of broadcast frames should be positive')
        self.__num_frames = value.num_frames
        self.__traffic_information = value

    @frame_description.setter
    def frame_description(self, value: List[FrameDescription]) -> None:
        """
        Set the frame description
        :param value: list of frame descriptions
        :return: nothing
        """
        accumulated_frames = 0  # Accumulated frames to calculate the frames descriptions have enough
        # Check if all the information is correct
        for frame_description in value:
            if frame_description.num_frames <= 0:
                raise ValueError('The number of frames in the description should be positive')
            accumulated_frames += frame_description.num_frames
            if frame_description.period <= 0:
                raise ValueError('The period in the frame description should be positive')
            if frame_description.deadline < 0:
                raise ValueError('The deadline in the frame description should be positive')
            if frame_description.deadline > frame_description.period:
                raise ValueError('The deadline in the frame description should be less or equal than the period')
            if frame_description.size <= 0:
                raise ValueError('The size in the frame description should be positive')
            if frame_description.starting_time < 0:
                raise ValueError('The starting time in the frame description should be a natural number')
            if frame_description.starting_time >= frame_description.deadline:
                raise ValueError('The starting time in the frame description should be less than the deadline')
            if frame_description.end_to_end < 0:
                raise ValueError('The end to end time in the frame description should be a natural number')
            if frame_description.end_to_end >= frame_description.deadline:
                raise ValueError('The end to end time in the frame description should be less than the deadline')
        if accumulated_frames != self.num_frames:
            raise ValueError('The total number of frames in the frame description should be the same as the number '
                             'of frames in the network')
        self.__frame_description = value

    # Network Functions #

    def create_network(self) -> None:
        """
        Create the network when all the information is set. If the information is not set, but a configuration is given,
        it will create all the information needed.
        :return: nothing
        """
        self.__create_topology()
        if self.frame_description:  # If we have a frame description, generate the randomized frames
            self.__generate_frames()

    def __create_topology(self) -> None:
        """
        Given the topology stores, creates the networks nodes and links with the information.
        We use the NetworkX package to store the network information as it has support functionality for graphs.
        :return: nothing
        """
        # Auxiliary lists to check if any link or node has been defined twice
        nodes = []
        links = []

        # Iterate for all nodes
        for node_description in self.topology_description.description:

            # Check if the user defined multiple nodes with the same ID
            if node_description.nodeID in nodes:
                raise ValueError('The node ID ' + str(node_description.nodeID) + ' has been defined multiple times')
            nodes.append(node_description.nodeID)

            self.__graph.add_node(node_description.nodeID, node=node_description.node)  # Add node to graph

            # Iterate for all the connection in the node
            for connection in node_description.connections:  # type: Network.TopologyDescription.NodeConnection

                # Check if the connection is to itself (not allowed)
                if connection.receiverID == node_description.nodeID:
                    raise ValueError('The node ' + str(connection.receiverID) + ' has a connection to itself')

                # Check if the user defined multiple links with the same ID
                if connection.linkID in links:
                    raise ValueError('The link ID ' + str(connection.linkID) + ' has been defined multiple times')
                links.append(connection.linkID)

                self.__graph.add_edge(node_description.nodeID, connection.receiverID,
                                      link=connection.link, id=connection.linkID)

        # Check if all nodes where defined
        for node_id, node_data in self.__graph.nodes(data=True):
            if 'node' not in node_data:
                raise ValueError('The node ' + str(node_id) + ' was referenced but not defined in the topology')

    def __generate_frames(self) -> None:
        """
        Generate frames for the network given the traffic information and descriptions.
        First select the sender and number of receivers, and which ones. Then select which traffic type is it.
        :return: nothing
        """
        # Generate lists with senders and receivers,
        list_senders, list_receivers = self.__generate_sender_receivers()

        # shuffle them so they are randomized
        combined = list(zip(list_senders, list_receivers))
        shuffle(combined)
        list_senders, list_receivers = map(list, zip(*combined))

        # Generate the frames depending of the frame description and the obtained senders and receivers
        self.__generate_frames_by_description(list_senders, list_receivers)

        # Generate the paths of the frames given the user configuration
        self.__generate_frame_paths()

    def __generate_sender_receivers(self) -> Tuple[List[int], List[List[int]]]:
        """
        For the given traffic information, obtain the list of senders and the list of all receivers
        :return: list of senders ids and list of list of receivers ids
        """
        # For all the frames, first select the sender and receivers, and save them in lists
        list_sender: List[int] = []
        list_receivers: List[List[int]] = []

        # Fetch all the node IDs to accelerate searches
        available_nodes_id = []
        for node_id, node_data in self.__graph.nodes(data=True):
            if node_data['node'].node_type == Node.NodeType.EndSystem:
                available_nodes_id.append(node_id)

        # Select all the senders and receivers for the frames
        for frame_it in range(self.num_frames):
            # Only need the ID, the frame does not need the objects information
            list_sender.append(choice(available_nodes_id))

            # Remove the selected sender to not choose it as receiver
            possible_receivers: List[int] = copy(available_nodes_id)
            possible_receivers.remove(list_sender[-1])

            # Select the receiver for all the single receiver frames
            if frame_it < self.traffic_information.num_single:
                list_receivers.append([choice(possible_receivers)])

            # Select the receivers for all the broadcast frames
            elif frame_it < self.traffic_information.num_single + self.traffic_information.num_broadcast:
                list_receivers.append(copy(possible_receivers))

            # Select a random number of receivers for all the multiple frames
            elif frame_it < self.traffic_information.num_single + self.traffic_information.num_broadcast + \
                    self.traffic_information.num_multiple:
                num_receivers = randint(1, len(possible_receivers))  # Select the number of receivers
                shuffle(possible_receivers)  # Shuffle to make it more interesting
                list_receivers.append(possible_receivers[0:num_receivers])

            # Local, the receivers are all the nodes that have only one hop, if no receivers exist, increase the number
            # of hops until we find some end system
            else:
                # Get all switches (or access points) connected to the selected sender
                switches_id = []
                checked_switches_id = []  # List of switches already checked, no need to go back to them
                for _, receiverID, _ in self.__graph.out_edges(list_sender[-1], data=True):
                    node = self.__graph.nodes(data=True)[receiverID]['node']
                    if node.node_type in {Node.NodeType.Switch, Node.NodeType.AccessPoint}:
                        switches_id.append(receiverID)
                receivers_id = []

                # While we do not have receivers, keep increasing the depth
                while not receivers_id:
                    # Take the ids to to iterate and save them in the checking list and already checked list
                    to_check_switched_id = copy(switches_id)
                    checked_switches_id.extend(copy(switches_id))

                    # Check if there exist any end system connected to the list of switches
                    for switch_id in to_check_switched_id:
                        for _, receiverID, _ in self.__graph.out_edges(switch_id, data=True):
                            node = self.__graph.nodes(data=True)[receiverID]['node']

                            # If we find an end system, we can add it
                            if node.node_type == Node.NodeType.EndSystem and receiverID != list_sender[-1]:
                                receivers_id.append(receiverID)

                            # If we find a switch or access point that we do not check, save it too
                            elif node.node_type in {Node.NodeType.Switch, Node.NodeType.AccessPoint} and \
                                    receiverID != list_sender[-1] and receiverID not in checked_switches_id:
                                switches_id.append(receiverID)
                list_receivers.append(copy(receivers_id))

        return list_sender, list_receivers

    def __generate_frames_by_description(self, senders: List[int], receivers: List[List[int]]) -> None:
        """
        Given the frames descriptions and the list of senders and receivers, generate the frames and save them
        :param senders: list of senders id
        :param receivers: list of list of receivers id
        :return: nothing
        """
        frame_it = 0
        for frame_type in self.frame_description:
            for num_frame in range(frame_type.num_frames):
                self.add_frame(frame_it, Frame(senders[frame_it], receivers[frame_it], frame_type.period,
                                               frame_type.deadline, frame_type.size, frame_type.starting_time,
                                               frame_type.end_to_end))
                frame_it += 1

    def add_frame(self, frame_id: int, frame: Frame) -> None:
        """
        Add a frame to the network
        :param frame_id: frame identifier
        :param frame: frame object
        :return: nothing
        """
        if frame_id in self.frames.keys():
            raise ValueError('A frame with ID ' + str(frame_id) + ' was already specified')
        self.__frames[frame_id] = frame

    def __generate_frame_paths(self) -> None:
        """
        Generate and save all the frame paths given the user specifications. It first creates all paths and then
        allocate them to the frames
        :return: nothing
        """
        # (For now we only calculate shortest path)
        # To accelerate the process, save all the obtained paths, so we do not calculate paths twice
        paths = {}
        for frame in self.frames.values():
            sender = frame.sender_id
            for receiver in frame.receivers_id:
                # Try if the path is already defined, if not, find it, convert it to links and add it
                try:
                    link_path = paths[(sender, receiver)]
                except KeyError:
                    try:
                        # Get shortest path and convert it from list of nodes to list of links
                        node_path = networkx.shortest_path(self.__graph, sender, receiver)
                        link_path = []
                        for node_it in range(len(node_path) - 1):
                            link_data = self.__graph.get_edge_data(node_path[node_it], node_path[node_it + 1])
                            link_path.append(link_data['id'])
                        paths[(sender, receiver)] = link_path
                    except networkx.NetworkXNoPath:
                        raise ValueError('The network does not have a path from node ' + str(sender) + ' to node ' +
                                         str(receiver))
                # Save the obtained path into the frame
                frame.set_path(receiver, link_path)

    # Input Functions #

    def read_network_xml(self, configuration_file: str) -> None:
        """
        Reads the parameters from the given configuration file and saves it into the internal memory of the class for
        other functions being able to create the network.
        :param configuration_file: name and relative path of the configuration file
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml = Xml.parse(configuration_file).getroot()
        network_xml = root_xml.find('Network')
        # If the xml file is a network and not a configuration, change the pointer
        if network_xml is None:
            network_xml = root_xml

        # Position and read all different trees of the network configuration
        self.__read_general_information_xml(network_xml.find('GeneralInformation'))
        self.__topology_description = self.__read_topology_xml(network_xml.find('TopologyInformation'))
        self.__read_traffic(network_xml.find('TrafficDescription'))

    def __read_general_information_xml(self, general_information_xml: Xml.Element) -> None:
        """
        Read the general information of the network configuration xml file
        :param general_information_xml: pointer to the general information in the tree
        :return: nothing
        """
        self.minimum_switch_time = self.__read_switch_time_xml(general_information_xml.find('SwitchInformation'))
        self.healing_protocol = self.__read_healing_protocol_xml(general_information_xml.find('SelfHealingProtocol'))

    def __read_switch_time_xml(self, switch_information_xml: Xml.Element) -> int:
        """
        Read the switch information of the network configuration xml file
        :param switch_information_xml: pointer to the switch information
        :return: minimum switch time in ns
        """
        minimum_time_xml: Xml.Element = switch_information_xml.find('MinimumTime')
        return self.TimeUnit.convert_ns(int(minimum_time_xml.text), minimum_time_xml.attrib['unit'])

    def __read_healing_protocol_xml(self, protocol_xml: Xml.Element) -> SelfHealingProtocol:
        """
        Read the self healing protocol information from the configuration xml file and return it
        :param protocol_xml: pointer to the self healing protocol information
        :return: a filled self healing protocol class instance
        """
        # Get the protocol period and convert it to ns
        period_xml: Xml.Element = protocol_xml.find('Period')
        period = self.TimeUnit.convert_ns(int(period_xml.text), period_xml.attrib['unit'])
        # Get the protocol time and convert it to ns
        time_xml: Xml.Element = protocol_xml.find('Time')
        time = self.TimeUnit.convert_ns(int(time_xml.text), time_xml.attrib['unit'])
        return self.SelfHealingProtocol(period, time)

    def __read_topology_xml(self, topology_xml: Xml.Element) -> TopologyDescription:
        """
        Read the topology description of the network configuration file
        :param topology_xml: pointer to the topology description
        :return: class containing the topology description
        """
        # Read all the nodes and populate the topology
        network_description: List[Network.TopologyDescription.NodeDescription] = []
        for node_xml in topology_xml.findall('Node'):  # type: Xml.Element
            # Read node information
            sender_id = int(node_xml.find('NodeID').text)
            node = Node(node_xml.attrib['category'])
            node_connections: List[Network.TopologyDescription.NodeConnection] = []

            for connection_xml in node_xml.findall('Connection'):
                # Read the receiver id
                receiver_id = int(connection_xml.find('NodeID').text)
                # Read all the connection information
                link_xml: Xml.Element = connection_xml.find('Link')
                link_id = int(link_xml.find('LinkID').text)
                speed_xml: Xml.Element = link_xml.find('Speed')
                speed = Link.SpeedUnit.convert_mbs(int(speed_xml.text), speed_xml.attrib['unit'])
                link_type = link_xml.attrib['category']
                link = Link(speed, link_type)
                # Save in a named tuple for connections
                node_connections.append(self.TopologyDescription.NodeConnection(receiver_id, link_id, link))

            # Save the node information
            network_description.append(Network.TopologyDescription.NodeDescription(sender_id, node, node_connections))

        return self.TopologyDescription(network_description)

    def __read_traffic(self, traffic_xml: Xml.Element) -> None:
        """
        Read the traffic description in the network. It can be specified by "generate", which means that some values
        will be given to generate traffic randomly. Or by "specified", which has all the traffic already created, only
        needs to be read and stored
        :param traffic_xml: pointer to the traffic description
        :return: nothing
        """
        # Traffic description with information to generate frames
        if traffic_xml.attrib['method'] == 'generate':
            self.traffic_information = self.__read_traffic_information_xml(traffic_xml.find('TrafficInformation'))
            self.frame_description = self.__read_traffic_description_xml(traffic_xml.find('FrameDescription'))
        # Traffic description will all the frames already generated
        else:
            self.__read_specified_traffic_xml(traffic_xml)

    def __read_traffic_information_xml(self, traffic_information_xml: Xml.Element) -> TrafficInformation:
        """
        Read the basic traffic information of the network, the number of frames and the number of frames in different
        classes depending of their receivers
        :param traffic_information_xml: traffic information pointer
        :return: the traffic information in a named tuple
        """
        num_frames = int(traffic_information_xml.find('NumberFrames').text)
        num_single = int(traffic_information_xml.find('NumberSingle').text)
        num_local = int(traffic_information_xml.find('NumberLocal').text)
        num_multi = int(traffic_information_xml.find('NumberMulti').text)
        num_broadcast = int(traffic_information_xml.find('NumberBroadcast').text)
        return self.TrafficInformation(num_frames, num_single, num_local, num_multi, num_broadcast)

    def __read_traffic_description_xml(self, frame_description_xml: Xml.Element) -> List[FrameDescription]:
        """
        Read the frame description information of the network. Different frame description for different number of
        frames can be defined.
        :param frame_description_xml: pointer to the frame descriptions
        :return: list of all the different frame descriptions
        """
        frame_descriptions: List[Network.FrameDescription] = []
        for frame_type_xml in frame_description_xml.findall('FrameType'):  # type: Xml.Element
            num_frames = int(frame_type_xml.find('NumberFrames').text)

            period_xml: Xml.Element = frame_type_xml.find('Period')
            period = self.TimeUnit.convert_ns(int(period_xml.text), period_xml.attrib['unit'])

            deadline_xml: Xml.Element = frame_type_xml.find('Deadline')
            deadline = self.TimeUnit.convert_ns(int(deadline_xml.text), deadline_xml.attrib['unit'])

            size_xml: Xml.Element = frame_type_xml.find('Size')
            size = Frame.SizeUnit.convert_bytes(int(size_xml.text), size_xml.attrib['unit'])

            starting_time_xml: Xml.Element = frame_type_xml.find('StartingTime')
            starting_time = self.TimeUnit.convert_ns(int(starting_time_xml.text), starting_time_xml.attrib['unit'])

            end_to_end_xml: Xml.Element = frame_type_xml.find('EndToEnd')
            end_to_end = self.TimeUnit.convert_ns(int(end_to_end_xml.text), end_to_end_xml.attrib['unit'])

            frame_descriptions.append(Network.FrameDescription(num_frames, period, deadline, size, starting_time,
                                                               end_to_end))
        return frame_descriptions

    def __read_specified_traffic_xml(self, frame_description: Xml.Element) -> None:
        """
        Read the already specified frames and save them into the dictionary of frames, including the paths
        :param frame_description: pointer to the frame descriptions
        :return: nothing
        """
        # For all frames, read the information
        for frame_xml in frame_description.findall('Frame'):  # type: Xml.Element
            frame_id = int(frame_xml.find('FrameID').text)

            period_xml: Xml.Element = frame_xml.find('Period')
            period = self.TimeUnit.convert_ns(int(period_xml.text), period_xml.attrib['unit'])

            deadline_xml: Xml.Element = frame_xml.find('Deadline')
            deadline = self.TimeUnit.convert_ns(int(deadline_xml.text), deadline_xml.attrib['unit'])

            size_xml: Xml.Element = frame_xml.find('Size')
            size = Frame.SizeUnit.convert_bytes(int(size_xml.text), size_xml.attrib['unit'])

            starting_time_xml: Xml.Element = frame_xml.find('StartingTime')
            starting_time = self.TimeUnit.convert_ns(int(starting_time_xml.text), starting_time_xml.attrib['unit'])

            end_to_end_xml: Xml.Element = frame_xml.find('EndToEnd')
            end_to_end = self.TimeUnit.convert_ns(int(end_to_end_xml.text), end_to_end_xml.attrib['unit'])

            sender = int(frame_xml.find('SenderID').text)

            # Read all the paths for every receiver too
            paths = {}
            for receiver_xml in frame_xml.findall('Paths/Receiver'):  # type: Xml.Element
                receiver = int(receiver_xml.find('ReceiverID').text)
                link_path = list(map(int, receiver_xml.find('Path').text.split(';')))
                if receiver in paths.keys():
                    raise ValueError('The receiver ' + str(receiver) + ' was specified multiple times in frame' +
                                     str(frame_id))
                if receiver == sender:
                    raise ValueError('The node ' + str(sender) + ' was specified also as receiver in frame ' +
                                     str(frame_id))
                paths[receiver] = link_path

            # Save the frame
            self.add_frame(frame_id, Frame(sender, list(paths.keys()),
                                           period, deadline, size, starting_time, end_to_end))
            # Add also all the paths for each receiver
            for key, link_path in paths.items():
                self.frames[frame_id].set_path(key, link_path)
        print('hello')

    # Output Functions #

    def write_network_xml(self, network_filename: str) -> None:
        """
        Write all the information of the network class in an xml file.
        :param network_filename: name and relative path to save the network xml file
        :return: nothing
        """
        top_xml = Xml.Element('NetworkConfiguration')

        # Write all the different trees of the network configuration
        self.__write_general_information_xml(Xml.SubElement(top_xml, 'GeneralInformation'))
        self.__write_topology_xml(Xml.SubElement(top_xml, 'TopologyInformation'))
        traffic_xml: Xml.Element = Xml.SubElement(top_xml, 'TrafficDescription')
        traffic_xml.set('method', 'specified')
        self.__write_traffic_xml(traffic_xml)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(top_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        with open(network_filename, "w") as f:
            f.write(output_xml)

    def __write_general_information_xml(self, general_information_xml: Xml.Element) -> None:
        """
        Write the general information of the network xml file
        :param general_information_xml: pointer to the general information in the tree
        :return: nothing
        """
        self.__write_switch_information_xml(Xml.SubElement(general_information_xml, 'SwitchInformation'))
        self.__write_healing_protocol_xml(Xml.SubElement(general_information_xml, 'SelfHealingProtocol'))

    def __write_switch_information_xml(self, switch_information_xml: Xml.Element) -> None:
        """
        Write the switch information of the network configuration xml file
        :param switch_information_xml: pointer to the switch information
        :return: nothing
        """
        minimum_time_xml: Xml.Element = Xml.SubElement(switch_information_xml, 'MinimumTime')
        minimum_time_xml.text = str(self.minimum_switch_time)
        minimum_time_xml.set('unit', 'ns')

    def __write_healing_protocol_xml(self, protocol_xml: Xml.Element) -> None:
        """
        Write the self healing protocol information to the network xml file
        :param protocol_xml: pointer to the self healing protocol information
        :return: nothing
        """
        # Write the protocol period
        protocol_period_xml: Xml.Element = Xml.SubElement(protocol_xml, 'Period')
        protocol_period_xml.text = str(self.healing_protocol.period)
        protocol_period_xml.set('unit', 'ns')
        # Write the protocol time
        protocol_time_xml: Xml.Element = Xml.SubElement(protocol_xml, 'Time')
        protocol_time_xml.text = str(self.healing_protocol.time)
        protocol_time_xml.set('unit', 'ns')

    def __write_topology_xml(self, topology_xml: Xml.Element) -> None:
        """
        Write the topology description of the network configuration file
        :param topology_xml: pointer to the topology description
        :return: nothing
        """
        # For all nodes write its information and connections
        for nodeID, node_data in self.__graph.nodes(data=True):

            # Write node information
            node_xml = Xml.SubElement(topology_xml, 'Node')
            node_xml.set('category', node_data['node'].node_type.name)
            Xml.SubElement(node_xml, 'NodeID').text = str(nodeID)

            # For all connections that has the current node as source, write its information
            for _, receiverID, link_data in self.__graph.out_edges(nodeID, data=True):
                # Write connection information
                connection_xml = Xml.SubElement(node_xml, 'Connection')
                Xml.SubElement(connection_xml, 'NodeID').text = str(receiverID)
                link_xml: Xml.Element = Xml.SubElement(connection_xml, 'Link')
                link_xml.set('category', link_data['link'].link_type.name)
                Xml.SubElement(link_xml, 'LinkID').text = str(link_data['id'])
                speed_xml: Xml.Element = Xml.SubElement(link_xml, 'Speed')
                speed_xml.set('unit', 'MBs')
                speed_xml.text = str(link_data['link'].speed)

    def __write_traffic_xml(self, traffic_xml: Xml.Element) -> None:
        """
        Write the traffic description of the all already defined frames, including the paths
        :param traffic_xml: pointer to the traffic description
        :return: nothing
        """
        # For all the frames, write its information, including the paths
        for key, frame in self.frames.items():
            frame_xml = Xml.SubElement(traffic_xml, 'Frame')
            Xml.SubElement(frame_xml, 'FrameID').text = str(key)

            period_xml: Xml.Element = Xml.SubElement(frame_xml, 'Period')
            period_xml.text = str(frame.period)
            period_xml.set('unit', 'ns')

            deadline_xml: Xml.Element = Xml.SubElement(frame_xml, 'Deadline')
            deadline_xml.text = str(frame.deadline)
            deadline_xml.set('unit', 'ns')

            size_xml: Xml.Element = Xml.SubElement(frame_xml, 'Size')
            size_xml.text = str(frame.size)
            size_xml.set('unit', 'Byte')

            starting_xml: Xml.Element = Xml.SubElement(frame_xml, 'StartingTime')
            starting_xml.text = str(frame.starting_time)
            starting_xml.set('unit', 'ns')

            end_xml: Xml.Element = Xml.SubElement(frame_xml, 'EndToEnd')
            end_xml.text = str(frame.end_to_end)
            end_xml.set('unit', 'ns')

            Xml.SubElement(frame_xml, 'SenderID').text = str(frame.sender_id)

            # For each receiver, write its link path
            receivers_xml: Xml.Element = Xml.SubElement(frame_xml, 'Paths')
            for receiver in frame.receivers_id:
                receiver_xml: Xml.Element = Xml.SubElement(receivers_xml, 'Receiver')
                Xml.SubElement(receiver_xml, 'ReceiverID').text = str(receiver)
                link_path = frame.get_path(receiver)
                Xml.SubElement(receiver_xml, 'Path').text = ''.join(str(link) + ';' for link in link_path)[:-1]
