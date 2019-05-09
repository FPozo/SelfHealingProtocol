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
from typing import List, Dict, Union


class Offset:
    """
    Class that contains the time transmissions of a frame in a link
    """

    # Init #

    def __init__(self):
        """
        Init of the Offset
        """
        self.__num_instances = 0
        self.__num_replicas = 0
        self.__transmission_times: List[List[int]] = []
        self.__ending_times: List[List[int]] = []

    # Getters #

    @property
    def num_instances(self) -> int:
        """
        Get the number of instances
        :return: number of instances
        """
        return self.__num_instances

    # Functions #

    def prepare_offset(self, num_instances: int, num_replicas: int) -> None:
        """
        Prepare the offset to be populated given the number of instances and replicas
        :param num_instances: number of instances
        :param num_replicas: number of replicas
        :return: nothing
        """
        if num_instances <= 0:
            raise ValueError('The number of instances should be a positive number')
        if num_replicas < 0:
            raise ValueError('The number of replicas should be a natural number')

        self.__num_instances = num_instances
        self.__num_replicas = num_replicas
        # Prepare the matrices with the transmission times, only do it if is not prepared already
        if not self.__transmission_times:
            for _ in range(num_instances):
                self.__transmission_times.append([])
                self.__ending_times.append([])
                for _ in range(num_replicas + 1):
                    self.__transmission_times[-1].append(-1)
                    self.__ending_times[-1].append(-1)

    def get_transmission_time(self, instance: int, replica: int) -> int:
        """
        Get the transmission time of the given instance and replica
        :param instance: instance index
        :param replica: replica index
        :return: transmission time
        """
        if instance < 0 or instance >= self.__num_instances:
            raise ValueError('The given instance is outside the range')
        if replica < 0 or replica > self.__num_replicas:
            raise ValueError('The given replica is outside the range')

        return self.__transmission_times[instance][replica]

    def set_transmission_time(self, instance: int, replica: int, time: int) -> None:
        """
        Set the transmission time of the given instance and replica
        :param instance: instance index
        :param replica: replica index
        :param time: transmission time
        :return: nothing
        """
        if instance < 0 or instance >= self.__num_instances:
            raise ValueError('The given instance is outside the range')
        if replica < 0 or replica > self.__num_replicas:
            raise ValueError('The given replica is outside the range')
        if self.__transmission_times[instance][replica] != -1 and self.__transmission_times[instance][replica] != time:
            raise ValueError('The given transmission time was already initialized and it does not match')

        self.__transmission_times[instance][replica] = time

    def get_ending_time(self, instance: int, replica: int) -> int:
        """
        Get the ending time of the given instance and replica
        :param instance: instance index
        :param replica: replica index
        :return: ending time
        """
        if instance < 0 or instance >= self.__num_instances:
            raise ValueError('The given instance is outside the range')
        if replica < 0 or replica > self.__num_replicas:
            raise ValueError('The given replica is outside the range')

        return self.__ending_times[instance][replica]

    def set_ending_time(self, instance: int, replica: int, time: int) -> None:
        """
        Set the ending time of the given instance and replica
        :param instance: instance index
        :param replica: replica index
        :param time: ending time
        :return: nothing
        """
        if instance < 0 or instance >= self.__num_instances:
            raise ValueError('The given instance is outside the range')
        if replica < 0 or replica > self.__num_replicas:
            raise ValueError('The given replica is outside the range')
        if self.__ending_times[instance][replica] != -1 and self.__ending_times[instance][replica] != time:
            raise ValueError('The given ending time was already initialized and it does not match')

        self.__ending_times[instance][replica] = time


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
        self.__paths: Dict[int, List[int]] = {}      # Dictionary with paths from the sender to the receivers
        self.__offsets: Dict[int, Offset] = {}       # Dictionary with the offsets with the link id as the key

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

    @property
    def offsets(self) -> Dict[int, Offset]:
        """
        Get the offsets
        :return: Dictionary with the offsets
        """
        return self.__offsets

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

    def get_offset_by_link(self, link_id: int) -> Union[None, Offset]:
        """
        Get the offset of the frame if exists for the given link id
        :param link_id: link identifier
        :return: offset if the frame has a transmission in the given link, none otherwise
        """
        if link_id in self.__offsets.keys():
            return self.__offsets[link_id]
        else:
            return None

    def link_in_path(self, link_id: int) -> bool:
        """
        Return if the link is in a path
        :param link_id: link identifier
        :return: true if is in a path, false otherwise
        """
        for path in self.__paths.values():
            if link_id in path:
                return True
        return False

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
        # Init the offset for all the different links of the frame
        for link in link_path:
            if link not in self.__offsets.keys():
                self.__offsets[link] = Offset()

    def exchange_path(self, link: int, new_path: List[int]) -> None:
        """
        For the given link, exchange the transmission with the new path, also updates the offsets dictionary
        :param link: link identifier to delete
        :param new_path: new path to update
        :return: nothing
        """
        # Check all paths if the given link appears to replace
        for receiver_id, path in self.__paths.items():
            # If the link is in the path, remove it and replace it for the given new path
            if link in path:
                index_link = path.index(link)
                path.remove(link)
                path[index_link:index_link] = new_path

    def remove_unused_offsets(self) -> None:
        """
        Remove the offsets that are not being used in any frame path
        :return: nothing
        """
        link_ids_to_remove = []
        for link_id, offset in self.__offsets.items():

            found_link = False
            for receiver_id, path in self.__paths.items():
                if link_id in path:
                    found_link = True
                    break
            # It it was found, do nothing, start searching the next link
            if not found_link:
                link_ids_to_remove.append(link_id)

        # The offsets cannot be removed during the loop iteration, so we save them and remove them later
        for link_id in link_ids_to_remove:
            del self.__offsets[link_id]

    def add_offset(self, link_id: int) -> None:
        """
        Add a new offset for the given link identifiers
        :param link_id: link identifiers
        :return: nothing
        """
        self.offsets[link_id] = Offset()

    def prepare_link_offset(self, link_id: int, num_instances: int, num_replicas: int) -> None:
        """
        Prepare the offset of the given link to receive transmission times
        :param link_id: link identifier
        :param num_instances: number of instances in the offset
        :param num_replicas: number of replicas in the offset
        :return: nothing
        """
        if link_id not in self.__offsets.keys():
            raise ValueError('The frames does not have an offset for the given link id')
        self.__offsets[link_id].prepare_offset(num_instances, num_replicas)

    def set_offset_transmission_time(self, link_id: int, instance: int, replica: int, time: int) -> None:
        """
        Set the transmission time for the given offset link
        :param link_id: link identifier
        :param instance: instance index
        :param replica: replica index
        :param time: transmission time
        :return: nothing
        """
        if link_id not in self.__offsets.keys():
            raise ValueError('The frames does not have an offset for the given link id')
        self.__offsets[link_id].set_transmission_time(instance, replica, time)

    def set_offset_ending_time(self, link_id: int, instance: int, replica: int, time: int) -> None:
        """
        Set the ending time for the given offset link
        :param link_id: link identifier
        :param instance: instance index
        :param replica: replica index
        :param time: ending time
        :return: nothing
        """
        if link_id not in self.__offsets.keys():
            raise ValueError('The frames does not have an offset for the given link id')
        self.__offsets[link_id].set_ending_time(instance, replica, time)
