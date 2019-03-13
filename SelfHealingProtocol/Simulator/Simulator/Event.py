# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Simulation                                                                                                         *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 19/02/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that defined events that happen in a simulation                                                            *
 *  An event can be a frame event or an action event happening in a node.                                              *
 *  The event will contain the information of what the event is supposed to perform.                                   *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


from enum import Enum
from typing import Union


class Event:
    """
    Event that happens at a node in the simulated network
    """

    # Init #

    def __init__(self, event_id: int, time: int) -> None:
        """
        Init the event
        :param event_id: event id
        :param time: time of the event
        """
        self.event_id = event_id
        self.time = time

    # Getters #

    @property
    def time(self) -> int:
        """
        Get the time of the event
        :return: time of the event in ns
        """
        return self.__time

    @property
    def event_id(self) -> int:
        """
        Get the event id
        :return: event id
        """
        return self.__event_id

    # Setters #

    @time.setter
    def time(self, time: int) -> None:
        """
        Set the time of the event
        :param time: time of the event in ns
        :return: nothing
        """
        if time < 0:
            raise ValueError('The time should be a positive number')

        self.__time = time

    @event_id.setter
    def event_id(self, event_id: int) -> None:
        """
        Set the event id
        :param event_id: event id
        :return: nothing
        """
        if event_id < 0:
            raise ValueError('The even id should be positive')

        self.__event_id = event_id


class FrameEvent(Event):
    """
    Event that is a frame transmission
    """

    class FrameName(Enum):
        """
        Enumeration of all the frame event names supported
        """
        Notification = 'Notification'
        FindingPath = 'FindingPath'
        NotifyPath = 'NotifyPath'
        Membership = 'Membership'
        Patch = 'Patch'
        UpdatePatch = 'UpdatePatch'
        Optimization = 'Optimization'
        UpdateOptimization = 'UpdateOptimization'
        Schedule = 'Schedule'

    # Init #

    def __init__(self, event_id: int, name: Union[str, FrameName], time: int, size: int):
        """
        Init the frame event
        :param event_id: event id
        :param name: name of the frame
        :param time: time of the event
        :param size: size of the frame
        """
        super().__init__(event_id, time)
        self.size = size
        self.name = name

    # Getters #

    @property
    def size(self) -> int:
        """
        Get the size of the frame event
        :return: size of the frame in Bytes
        """
        return self.__size

    @property
    def name(self) -> FrameName:
        """
        Get the name of the frame event
        :return: name of the frame event
        """
        return self.__name

    # Setters #

    @size.setter
    def size(self, size: int) -> None:
        """
        Set the size of the frame event
        :param size: size of the frame in Bytes
        :return: nothing
        """
        if size < 0:
            raise ValueError('The size of the frame should be positive')

        self.__size = size

    @name.setter
    def name(self, name: Union[str, FrameName]):
        """
        Set the name of the frame event
        :param name: name of the frame event either in str or the enum class
        :return: nothing
        """
        if type(name) is self.FrameName:
            self.__name = name
        else:
            self.__name = self.FrameName[name]


class ExecutionEvent(Event):
    """
    Event that is an action execution in the simulated network
    """

    class ExecutionName(Enum):
        """
        Enumeration of the name of the execution event
        """
        Patch = 'Patch'
        Optimize = 'Optimize'

    # Init #

    def __init__(self, event_id: int, name: Union[str, ExecutionName], time: int) -> None:
        """
        Init the execution event
        :param event_id: event id
        :param time: time when the event is executed
        :param name: name of the execution event
        """
        super().__init__(event_id, time)
        self.name = name

    # Getters #

    @property
    def name(self) -> ExecutionName:
        """
        Get the execution event name
        :return: execution event name
        """
        return self.__name

    # Setters #

    @name.setter
    def name(self, name: Union[str, ExecutionName]) -> None:
        """
        Set the execution event name
        :param name: execution event name
        :return: nothing
        """
        if type(name) is self.ExecutionName:
            self.__name = name
        else:
            self.__name = self.ExecutionName[name]


class InternalEvent(Event):
    """
    Event that is internal for the simulator, such as a link failure
    """

    class InternalName(Enum):
        """
        Enumeration of the name of the internal event
        """
        LinkFailure = 'LinkFailure'

    # Init #

    def __init__(self, event_id: int, name: Union[str, InternalName], time: int) -> None:
        """
        Init the execution event
        :param event_id: event id
        :param time: time when the event is executed
        :param name: name of the execution event
        """
        super().__init__(event_id, time)
        self.name = name

    # Getters #

    @property
    def name(self) -> InternalName:
        """
        Get the execution event name
        :return: execution event name
        """
        return self.__name

    # Setters #

    @name.setter
    def name(self, name: Union[str, InternalName]) -> None:
        """
        Set the execution event name
        :param name: execution event name
        :return: nothing
        """
        if type(name) is self.InternalName:
            self.__name = name
        else:
            self.__name = self.InternalName[name]
