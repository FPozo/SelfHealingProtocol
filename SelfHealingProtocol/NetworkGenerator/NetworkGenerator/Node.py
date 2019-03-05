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
from typing import Union


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
