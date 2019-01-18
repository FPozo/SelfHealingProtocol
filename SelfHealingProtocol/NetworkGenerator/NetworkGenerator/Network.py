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
import xml.etree.ElementTree as Xml
from xml.dom import minidom
import networkx
from enum import Enum
from typing import NamedTuple, List
from Node import Node
from Link import Link


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
        ns = 'ns'       # Nanoseconds
        us = 'us'       # Microseconds
        ms = 'ms'       # Milliseconds
        s = 's'         # Seconds

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

    # Getters #

    def __init__(self):
        """
        Init of the Network
        """
        self.__graph = networkx.OrderedDiGraph()    # Graph with the information of the topology in NetworkX
        self.__minimum_switch_time = 0              # Minimum processing time in the switch in ns
        self.__healing_protocol = None              # Self Healing Protocol values
        self.__topology_description = None          # Information with the topology description in a named tuple

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

    # Network Functions #

    def create_network(self) -> None:
        """
        Create the network when all the information is set. If the information is not set, but a configuration is given,
        it will create all the information needed.
        :return: nothing
        """
        self.__create_topology()

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

            self.__graph.add_node(node_description.nodeID, node=node_description.node)      # Add node to graph

            # Iterate for all the connection in the node
            for connection in node_description.connections:     # type: Network.TopologyDescription.NodeConnection

                # Check if the user defined multiple links with the same ID
                if connection.linkID in links:
                    raise ValueError('The link ID ' + str(connection.linkID) + ' has been defined multiple times')
                links.append(connection.linkID)

                self.__graph.add_edge(node_description.nodeID, connection.receiverID,
                                      link=connection.link, id=connection.linkID)

    # Input Functions #

    def read_network_configuration_xml(self, configuration_file: str) -> None:
        """
        Reads the parameters from the given configuration file and saves it into the internal memory of the class for
        other functions being able to create the network.
        :param configuration_file: name and relative path of the configuration file
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml = Xml.parse(configuration_file).getroot()

        # Position and read all different trees of the network configuration
        self.__read_general_information_xml(root_xml.find('GeneralInformation'))
        self.__topology_description = self.__read_topology_xml(root_xml.find('TopologyInformation'))

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
        for node_xml in topology_xml.findall('Node'):   # type: Xml.Element
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
