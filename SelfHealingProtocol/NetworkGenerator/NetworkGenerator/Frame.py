# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Frame Class                                                                                                        *
 *  NetworkGenerator                                                                                                   *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 21/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class for the frames in the network. A frame has only one node (end system) sender and one or multiple (also end   *
 *  systems) receivers. All frames must have a period in nanoseconds and a size in bytes. They may also have a         *
 *  deadline (also in nanoseconds).                                                                                    *
 *  A frame is possible to have and end-to-end delay from the sender to the receiver (different for any if needed).    *
 *  It is possible for a frame to need to start after an specific amount of time since the schedule started.           *
 *  Frames contain a path of links to arrive from the sender to the receiver, if it is none, it means it has not       *
 *  decided yet, and other entity (such as a network or a scheduler) will decide it later.                             *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from enum import Enum
from enforce import runtime_validation
from typing import List


@runtime_validation
class Frame:
    """
    Class that contains the information of a time-triggered frame
    """

    # Auxiliary Classes #

    class SizeUnit(Enum):
        """
        Size Unit class to to take different units
        """
        Byte = 'Byte'       # Bytes
        KByte = 'KByte'     # KiloBytes

        @staticmethod
        def convert_bytes(value: int, unit: str) -> int:
            """
            Convert the given value and unit to bytes
            :param value: value to convert
            :param unit: unit of the given value
            :return: value converted to bytes
            """
            if unit == Frame.SizeUnit.Byte.name:
                return value
            if unit == Frame.SizeUnit.Byte.name:
                return value * 1000
            raise TypeError('The unit is not recognized or supported')

    # Init #

    def __init__(self, sender_id: int, receivers_id: List[int], period: int, deadline: int = 0, size: int = 1000,
                 starting_time: int = 0, end_to_end: int = 0):
        """
        Init of the frame
        :param sender_id: id of the end system sender
        :param receivers_id: list of ids of all the end system receivers
        :param period: period of the frame in nanoseconds
        :param deadline: deadline of the frame in nanoseconds
        :param size: size of the frame in Bytes
        :param starting_time: starting time of the frame in nanoseconds
        :param end_to_end: end to end delay time of the frame in nanoseconds
        """
        self.sender_id = sender_id
        self.receivers_id = receivers_id
        self.period = period
        self.deadline = deadline
        self.size = size
        self.starting_time = starting_time
        self.end_to_end = end_to_end
        self.__paths = {}                       # Dictionary with paths from the sender to the receivers

    # Getters #

    @property
    def period(self) -> int:
        """
        Get the period of the frame in nanoseconds
        :return: period of the frame in nanoseconds
        """
        return self.__period

    @property
    def deadline(self) -> int:
        """
        Get the deadline of the frame in nanoseconds
        :return: deadline of the frame in nanoseconds
        """
        return self.__deadline

    @property
    def size(self) -> int:
        """
        Get the size of the frame in Bytes
        :return: size of the frame in Bytes
        """
        return self.__size

    @property
    def starting_time(self) -> int:
        """
        Get the starting time of the frame in nanoseconds
        :return: starting time of the frame in nanoseconds
        """
        return self.__starting_time

    @property
    def end_to_end(self) -> int:
        """
        Get the end to end time in nanoseconds. Time from sending the frame from the sender to the time all receivers
        have received the frame
        :return: end to end time in nanoseconds
        """
        return self.__end_to_end

    @property
    def sender_id(self) -> int:
        """
        Get the sender id of the frame
        :return: sender id of the frame
        """
        return self.__sender_id

    @property
    def receivers_id(self) -> List[int]:
        """
        Get the ids of all the receivers of the frame
        :return: ids of all the receivers of the frame
        """
        return self.__receivers_id

    def get_path(self, receiver: int) -> List[int]:
        """
        Get the path to a receiver id
        :param receiver: receiver id
        :return: list of links ids
        """
        if receiver not in self.receivers_id:
            raise ValueError('The given receiver is not defined in the list of receivers')
        if receiver not in self.__paths.keys():
            raise ValueError('The path to the receiver is not defined')
        return self.__paths[receiver]

    # Setters #

    @period.setter
    def period(self, value: int) -> None:
        """
        Set the period of the frame
        :param value: period of the frame in nanoseconds
        :return: nothing
        """
        if value <= 0:
            raise ValueError('The period must be positive')
        self.__period = value

    @deadline.setter
    def deadline(self, value: int) -> None:
        """
        Set the deadline of the frame in nanoseconds
        :param value: deadline of the frame in nanoseconds
        :return: nothing
        """
        if value < 0:
            raise ValueError('The deadline must be positive')
        if value > self.period:
            raise ValueError('The deadline must be less than the period')
        if value == 0:
            self.__deadline = self.period
        else:
            self.__deadline = value

    @size.setter
    def size(self, value: int) -> None:
        """
        Set the size of the frame in Bytes
        :param value: size of the frame in Bytes
        :return: nothing
        """
        if value <= 0:
            raise ValueError('The size of frame must be a positive number')
        self.__size = value

    @starting_time.setter
    def starting_time(self, value: int) -> None:
        """
        Set the starting time of the frame in nanoseconds
        :param value: starting time of the frame in nanoseconds
        :return: nothing
        """
        if value < 0:
            raise ValueError('The starting time of the frame must be a natural number')
        if value >= self.deadline:
            raise ValueError('The starting time of the frame cannot be larger than its deadline')
        self.__starting_time = value

    @end_to_end.setter
    def end_to_end(self, value: int) -> None:
        """
        Set the end to end delay time of the frame in nanoseconds
        :param value: end to end delay time of the frame in nanoseconds
        :return: nothing
        """
        if value < 0:
            raise ValueError('The end to end delay time of the frame must be a positive number')
        if value > self.deadline:
            raise ValueError('The end to end delay time of the frame cannot be larger than the deadline')
        if value == 0:
            self.__end_to_end = self.deadline
        else:
            self.__end_to_end = value

    @sender_id.setter
    def sender_id(self, value: int) -> None:
        """
        Set the sender id of the frame
        :param value: sender id of the frame
        :return: nothing
        """
        self.__sender_id = value

    @receivers_id.setter
    def receivers_id(self, value: List[int]) -> None:
        """
        Set the ids of all the receivers of the frame
        :param value: ids of all the receivers of the frame
        :return: nothing
        """
        if self.sender_id in value:
            raise ValueError('The receiver of the frame cannot be also the sender')
        self.__receivers_id = value

    def set_path(self, receiver: int, link_path: List[int]) -> None:
        """
        Set the path to a receiver id
        :param receiver: receiver id
        :param link_path: path with a list of links ids
        :return: nothing
        """
        if receiver not in self.receivers_id:
            raise ValueError('The given receiver is not defined in the list of receivers')
        self.__paths[receiver] = link_path
