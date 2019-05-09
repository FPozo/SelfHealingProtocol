# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Node Class                                                                                                         *
 *  NetworkGenerator                                                                                                   *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 14/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class for the nodes in the network. Basic class that only defines node type (switch, end system or access point).  *
 *  It may be interesting to add new information such as memory of switches or more types for future work              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


from enum import Enum
from typing import Union, List, Tuple, Dict
from operator import itemgetter
from itertools import chain


class Node:
    """
    Class with the information of a node in the network
    """

    class NodeType(Enum):
        """
        Class to define different node types
        """
        Switch = 'Switch'
        EndSystem = 'EndSystem'
        AccessPoint = 'AccessPoint'

    def __init__(self, value_type: Union[NodeType, str]):
        """
        Init the class with the type of node
        :param value_type: node type
        """
        self.node_type = value_type
        self.__inc_transmissions: List[Tuple[int, int]] = []        # The tuple is the time and the size of transmission
        self.__out_transmissions: Dict[int, List[Tuple[int, int]]] = {}  # The Dict is for out links
        self.__max_memory: int = 0

    @property
    def max_memory(self) -> int:
        """
        Get the max memory needed for the node
        :return: nothing
        """
        return self.__max_memory

    @property
    def node_type(self) -> NodeType:
        """
        Get the node type
        :return: node type
        """
        return self.__node_type

    @node_type.setter
    def node_type(self, value: Union[NodeType, str]):
        """
        Set the node type
        :param value: node type
        :return: nothing
        """
        if type(value) is str:
            self.__node_type = Node.NodeType[value]
        else:
            self.__node_type = value

    def add_inc_transmission(self, transmission: Tuple[int, int]) -> None:
        """
        Add an incoming transmission
        :param transmission: incoming transmission with time when it arrive and size
        :return: nothing
        """
        self.__inc_transmissions.append(transmission)

    def add_out_transmission(self, transmission: Tuple[int, int], link_id: int) -> None:
        """
        Add an out transmission
        :param transmission: incoming transmission with time when it arrive and size
        :param link_id: link where is going out
        :return: nothing
        """
        if link_id not in self.__out_transmissions.keys():
            self.__out_transmissions[link_id] = [transmission]
        else:
            self.__out_transmissions[link_id].append(transmission)

    def sort_transmissions(self) -> None:
        """
        Sort the transmissions
        :return: nothing
        """
        self.__inc_transmissions.sort(key=itemgetter(0))
        for transmissions in self.__out_transmissions.values():
            transmissions.sort(key=itemgetter(0))

    def calculate_max_memory(self) -> int:
        """
        Calculate the max memory needed for the node
        :return: the max memory needed
        """
        # Create temporal lists to easily manipulate
        inc_list = list(self.__inc_transmissions)
        out_list = list(chain.from_iterable(self.__out_transmissions.values()))
        out_list.sort(key=itemgetter(0))
        memory = 0

        # Only check while there are incoming transmissions, as after that memory will always decrease
        while inc_list:
            # Check if a transmission is incoming or out
            if inc_list[0][0] < out_list[0][0]:
                memory += inc_list[0][1]
                inc_list.pop(0)
            else:
                memory -= out_list[0][1]
                out_list.pop(0)

            if memory > self.__max_memory:
                self.__max_memory = memory
        return self.__max_memory
