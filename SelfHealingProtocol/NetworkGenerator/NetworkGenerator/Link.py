# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Link Class                                                                                                         *
 *  NetworkGenerator                                                                                                   *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 14/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class for the links in the network. It contains the speed and the type (wired or wireless) of the link             *
 *                                                                                                                     *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from enum import Enum
from enforce import runtime_validation
from typing import Union


@runtime_validation
class Link:
    """
    Class that contains the information fo the link (speed and type)
    """

    # Auxiliary Classes #

    class SpeedUnit(Enum):
        """
        Time Unit class to to take different units
        """
        KBs = 'KBs'         # Kilobytes per second
        MBs = 'MBs'         # Megabytes per second
        GBs = 'GBs'         # Gigabytes per second

        @staticmethod
        def convert_mbs(value: int, unit: str) -> int:
            """
            Convert the given value and unit to nanoseconds
            :param value: value to convert
            :param unit: unit of the given value
            :return: value converted to nanoseconds
            """
            if unit == Link.SpeedUnit.KBs.name:
                return value * 1000
            if unit == Link.SpeedUnit.MBs.name:
                return value
            if unit == Link.SpeedUnit.GBs.name:
                return value * 1000
            raise TypeError('The unit is not recognized or supported')

    class LinkType(Enum):
        """
        Class to define the possible link types
        """
        Wired = 'Wired'
        Wireless = 'Wireless'

    def __init__(self, speed: int = 100, link_type: Union[LinkType, str] = LinkType.Wired):
        """
        Initialization of the link, if no values are given we suppose a standard wired link with speed of 100 MB/s
        :param speed: speed of the link in MB/s
        :param link_type: Type of the link
        """
        self.speed = speed
        self.link_type = link_type

    # Getters #

    @property
    def speed(self) -> int:
        """
        Get the speed of the link in MB/s
        :return: speed of the link in MB/s
        """
        return self.__speed

    @property
    def link_type(self) -> LinkType:
        """
        Get the link type
        :return: link type
        """
        return self.__link_type

    # Setters #

    @speed.setter
    def speed(self, value: int) -> None:
        """
        Set the speed of the link in MB/s
        :param value: speed of the link in MB/s
        :return: nothing
        """
        if value <= 0:
            raise ValueError('The speed of the link should be a natural number')
        self.__speed = value

    @link_type.setter
    def link_type(self, value: Union[LinkType, str]) -> None:
        """
        Set the link type
        :param value: link type
        :return: nothing
        """
        if type(value) is str:
            self.__link_type = Link.LinkType[value]
        else:
            self.__link_type = value
