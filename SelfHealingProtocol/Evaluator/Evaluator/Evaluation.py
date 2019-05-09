# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Evaluation Class                                                                                                   *
 *  Evaluator                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 08/03/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that executes the evaluation algorithms to extract data from the networks, schedules and simulations         *
 *  For the given master configuration, creates multiple configurations, one for each execution, and calls the         *
 *  algorithms that execute them.                                                                                      *
 *  The outputs are always stored and can be chosen which types of outputs to extract.                                 *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


from enum import Enum
from typing import List
from os import mkdir, remove, linesep, listdir, path
from xml.dom import minidom
from Network import Network
from Simulator import Simulation
from itertools import combinations
from sklearn.svm import SVC  # , LinearSVC
from pickle import dump
from numpy import std, mean
from shutil import copy
from subprocess import run
import pandas
import xml.etree.ElementTree as Xml


class Evaluation:
    """
    Evaluation algorithm to extract information desired about the performance of the scheduling algorithms
    """

    # Auxiliary Classes
    class Algorithm(Enum):
        SingleSimulation = "SingleSimulation"
        ExhaustiveSimulation = "ExhaustiveSimulation"
        GenerateSchedule = "GenerateSchedule"

    # Init Function #

    # noinspection PyTypeChecker
    def __init__(self):
        """
        Init the variables of the evaluation class
        """
        self.__algorithm: Evaluation.Algorithm = None               # Algorithm to execute
        self.__name: str = None                                     # Name of the evaluation
        self.__add_database: bool = None                            # Add results to the machine learning database
        self.__time_classification: int = None                      # Time classification to decide learning class
        self.__generate_network: bool = None                        # Generate a network by the given configuration
        self.__configuration_file: str = None                       # Master configuration path and file name
        self.__network_file: str = None                             # Read network file
        self.__schedule_file: str = None                            # Read schedule file
        self.__depth_link: int = None                               # Number of consecutive link failures to evaluate
        self.__distance_failure: int = None                         # Distance between failures
        self.__network = Network()                                  # Network to generate the network file
        self.__simulator = Simulation(self.__network)               # Simulation of the execution of the network

        # Results from evaluations
        self.__success_rate: float = None                           # Success rate of the evaluation
        self.__no_path: float = None                                # Percentage of no path found
        self.__no_schedule: float = None                            # Percentage of no schedule found
        self.__avg_patch: float = None                              # Average patching time
        self.__std_patch: float = None                              # Standard deviation of patching time
        self.__avg_optimize: float = None                           # Average optimization time
        self.__std_optimize: float = None                           # Standard deviation of optimize time

    # Functions #

    def evaluate(self) -> None:
        """
        Given the evaluation parameters read on the master configuration file, execute the algorithms to extract the
        data
        :return: nothing
        """
        if self.__algorithm == Evaluation.Algorithm.SingleSimulation:
            self.__evaluate_single()
        elif self.__algorithm == Evaluation.Algorithm.ExhaustiveSimulation:
            self.__evaluate_exhaustive_links()
        elif self.__algorithm == Evaluation.Algorithm.GenerateSchedule:
            self.__generate_schedule()

    def __create_network(self, configuration_file: str) -> str:
        """
        Create the network to schedule
        :param configuration_file: path of the configuration file
        :return: the network file created
        """
        try:
            mkdir('../Files/Networks/' + self.__name)
        except FileExistsError:
            pass
        self.__network.read_network_xml(configuration_file)
        self.__network.create_network()
        network_file = '../Files/Networks/' + self.__name + '/Network.xml'
        self.__network.write_network_xml(network_file)
        return network_file

    def __create_schedule(self, configuration_file: str, network_file: str) -> str:
        """
        Create the schedule given the configuration and the network file
        :param configuration_file: configuration file with information about scheduling
        :param network_file: network file with the network to schedule
        :return: the schedule file created
        """
        try:
            mkdir('../Files/Schedules/' + self.__name)
        except FileExistsError:
            pass
        schedule_file = '../Files/Schedules/' + self.__name + '/Schedule.xml'
        run(['./../Files/Executables/Schedule', network_file, configuration_file, schedule_file])
        return schedule_file

    def __generate_schedule(self) -> None:
        """
        Generate a the network and schedule from the configuration
        :return: nothing
        """
        try:
            mkdir('../Files/Configurations/' + self.__name)
        except FileExistsError:
            pass
        root_xml: Xml.Element = Xml.parse(self.__configuration_file).getroot()

        # Copy the Network, Schedule and Simulation for the new single configuration file
        write_xml = Xml.Element('Configuration')

        network_xml = root_xml.find('Network')
        write_xml.append(network_xml)
        schedule_xml = root_xml.find('Schedule')
        write_xml.append(schedule_xml)

        # Create the network
        network_file = self.__create_network(self.__configuration_file)
        # Create the schedule
        self.__create_schedule(self.__configuration_file, network_file)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(write_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        configuration_file = '../Files/Configurations/' + self.__name + '/Configuration.xml'
        with open(configuration_file, "w") as f:
            f.write(output_xml)

    def __evaluate_single(self) -> None:
        """
        Evaluate a single instance simulation
        :return: nothing
        """
        # Create the configuration folder and file
        try:
            mkdir('../Files/Configurations/' + self.__name)
        except FileExistsError:
            pass
        root_xml: Xml.Element = Xml.parse(self.__configuration_file).getroot()

        # Copy the Network, Schedule and Simulation for the new single configuration file
        write_xml = Xml.Element('Configuration')

        if self.__generate_network:
            network_xml = root_xml.find('Network')
            write_xml.append(network_xml)
            schedule_xml = root_xml.find('Schedule')
            write_xml.append(schedule_xml)

            # Create the network
            network_file = self.__create_network(self.__configuration_file)
            # Create the schedule
            schedule_file = self.__create_schedule(self.__configuration_file, network_file)

        else:
            network_file = self.__network_file
            self.__network = Network()  # Read the network for needed information
            self.__network.read_network_xml(network_file)
            schedule_file = self.__schedule_file

        simulation_xml: Xml.Element = root_xml.find('Simulation')
        Xml.SubElement(simulation_xml, 'AddDatabase').text = '1' if self.__add_database else '0'
        write_xml.append(simulation_xml)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(write_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        configuration_file = '../Files/Configurations/' + self.__name + '/Configuration.xml'
        with open(configuration_file, "w") as f:
            f.write(output_xml)

        # Execute the simulation
        self.__network = Network()      # Reset the network
        self.__network.read_network_xml(network_file)
        self.__network.read_schedule_xml(schedule_file)
        self.__simulator = Simulation(self.__network)
        self.__simulator.read_simulation_xml(configuration_file)
        self.__simulator.simulate()

        self.__write_simulation_instance(0)

        # Create the master simulation file
        self.__write_master_simulation()

    def __evaluate_exhaustive_links(self) -> None:
        """
        Evaluate exhaustively all possible link failures in the network
        Given the parameters depth link from the configuration file, combinations of more than one link failure with
        a predefined distance will be evaluated
        :return:
        """
        # Create the configuration folder and file
        try:
            mkdir('../Files/Configurations/' + self.__name)
        except FileExistsError:
            pass
        root_xml: Xml.Element = Xml.parse(self.__configuration_file).getroot()

        # Copy the Network, Schedule and Simulation for the new single configuration file
        write_xml = Xml.Element('Configuration')

        if self.__generate_network:

            network_xml = root_xml.find('Network')
            write_xml.append(network_xml)
            schedule_xml = root_xml.find('Schedule')
            write_xml.append(schedule_xml)

            # Create the network
            network_file = self.__create_network(self.__configuration_file)

            # Create the schedule
            schedule_file = self.__create_schedule(self.__configuration_file, network_file)

        else:
            network_file = self.__network_file
            self.__network = Network()  # Read the network for needed information
            self.__network.read_network_xml(network_file)
            schedule_file = self.__schedule_file

        # Write the temporal configuration file to obtain the network and schedule
        output_xml = minidom.parseString(Xml.tostring(write_xml)).toprettyxml(encoding="UTF-8", indent="    ")
        output_xml = output_xml.decode("utf-8")
        configuration_file = '../Files/Configurations/' + self.__name + '/Configuration.xml'
        with open(configuration_file, "w") as f:
            f.write(output_xml)

        # Once the network and schedule files were obtained, remove the configuration file and prepare all the
        # configuration files for the simulations
        remove(configuration_file)
        link_ids = self.__network.get_link_ids()

        # Write the simulation xml part
        simulation_xml: Xml.Element = root_xml.find('Simulation')
        Xml.SubElement(simulation_xml, 'AddDatabase').text = '1' if self.__add_database else '0'
        simulation_xml.remove(simulation_xml.find('Events'))
        write_xml.append(simulation_xml)
        event_xml: Xml.Element = Xml.SubElement(simulation_xml, 'Events')

        # Get all the possible link combinations depending of the depth link
        it = 0
        link_combinations = list(combinations(link_ids, self.__depth_link))
        num_evaluations = len(link_combinations)
        successful_evaluation = 0
        for link_failures in link_combinations:

            print('Starting Evaluation ' + str(it + 1) + '/' + str(num_evaluations) + ' with successful = ' +
                  str(successful_evaluation))

            # Write all the link failures
            for failure_it, link_id in enumerate(link_failures):
                failure_xml: Xml.Element = Xml.SubElement(event_xml, 'Failure')
                failure_xml.set('component', 'Link')
                Xml.SubElement(failure_xml, 'ID').text = str(link_id)
                time_xml: Xml.Element = Xml.SubElement(failure_xml, 'Time')
                time_xml.text = str(self.__distance_failure * (failure_it + 1))
                time_xml.set('unit', 'ns')

            # Write the temporal configuration file to obtain the network and schedule
            output_xml = minidom.parseString(Xml.tostring(write_xml)).toprettyxml(encoding="UTF-8", indent="    ")
            output_xml = output_xml.decode("utf-8")
            output_xml = linesep.join([s for s in output_xml.splitlines() if s.strip()])
            configuration_file = '../Files/Configurations/' + self.__name + '/Configuration' + str(it) + '.xml'
            with open(configuration_file, "w") as f:
                f.write(output_xml)

            # Execute the simulation
            self.__network = Network()  # Reset the network
            self.__network.read_network_xml(network_file)
            self.__network.read_schedule_xml(schedule_file)
            self.__simulator = Simulation(self.__network)
            try:
                self.__simulator.read_simulation_xml(configuration_file)
                self.__simulator.simulate()
                successful_evaluation += 1
            except Simulation.NoPath:
                print('Failed at link because there is no path ' + str(link_failures))
                pass
            except Simulation.NoSchedule:
                print('Failed at link because there is no schedule found ' + str(link_failures))
                pass

            self.__write_simulation_instance(it)

            # Clean the failure tree before starting the next iteration
            for failure_xml in event_xml.findall('Failure'):
                event_xml.remove(failure_xml)
            it += 1

        # Create the master simulation file
        self.__write_master_simulation()

        print('Successfully repaired ' + str(successful_evaluation) + '/' + str(num_evaluations) + ' cases')

    def evaluate_outputs(self, simulation_folder: str) -> None:
        """
        For the given folder containing the simulations, extract interesting outputs such as success rate or
        average patching/optimization time
        :param simulation_folder: path to the simulation folder
        :return: nothing
        """
        # For all the simulation files
        list_success_rate: List[int] = []
        list_no_path: List[int] = []
        list_no_schedule: List[int] = []
        list_patch_time: List[int] = []
        list_optimize_time: List[int] = []

        for files in listdir(simulation_folder):
            root_xml: Xml.Element = Xml.parse(simulation_folder + '/' + files).getroot()

            # For all the failure instances
            healed = True
            for instance_xml in root_xml.findall('FailureInstance'):    # type: Xml.Element

                if instance_xml.find('NoTransmission').text == '0':

                    # It could not heal the link failure
                    if instance_xml.find('Healed').text == '0':
                        list_success_rate.append(0)
                        healed = False
                        if instance_xml.find('NoPath').text == '1':
                            list_no_path.append(1)
                        elif instance_xml.find('NoSchedule').text == '1':
                            list_no_schedule.append(1)
                        else:
                            raise ValueError('A simulation failed and we do not know the reason')

                    else:
                        list_patch_time.append(int(instance_xml.find('TimePatched').text))
                        list_optimize_time.append(int(instance_xml.find('TimeOptimized').text))

            # If nothing weird happened, then we heal the sequence of link failures
            if healed:
                list_success_rate.append(1)
                list_no_path.append(0)
                list_no_schedule.append(0)

        self.__success_rate = mean(list_success_rate)
        self.__no_path = mean(list_no_path)
        self.__no_schedule = mean(list_no_schedule)
        self.__avg_patch = mean(list_patch_time)
        self.__std_patch = std(list_patch_time)
        self.__avg_optimize = mean(list_optimize_time)
        self.__std_optimize = std(list_optimize_time)

        print('Success Rate => ' + str(self.__success_rate))
        print('No Path => ' + str(self.__no_path))
        print('No Schedule => ' + str(self.__no_schedule))
        print('Average Path Time => ' + str(self.__avg_patch))
        print('STD Path Time => ' + str(self.__std_patch))
        print('Average Optimize Time => ' + str(self.__avg_optimize))
        print('STD Optimize Time => ' + str(self.__std_optimize))

    # Machine Learning Functions #

    @staticmethod
    def learn() -> None:
        """
        Given the normalized database, learn it
        :return: nothing
        """
        bank_data = pandas.read_csv('../Files/Database/Database_normalized.csv')
        x = bank_data.drop(['Instance', 'Total Utilization', 'Total Offsets', 'Classification'], axis=1)
        y = bank_data['Classification']
        svc_classifier = SVC(kernel='linear')
        # svc_classifier = LinearSVC()
        svc_classifier.fit(x, y)
        dump(svc_classifier, open('../Files/Database/Skynet.svm', 'wb'))

    @staticmethod
    def save_to_vault() -> None:
        """
        Save obtained databases to vault
        :return: nothing
        """
        # Remove the vault files first
        for file in listdir('../Files/Database/VaultVersion/'):
            file_path = path.join('../Files/Database/VaultVersion/', file)
            remove(file_path)

        # Add the files if they exist
        if path.isfile('../Files/Database/Database_normalized.csv'):
            copy('../Files/Database/Database_normalized.csv', '../Files/Database/VaultVersion/Database_normalized.csv')
        if path.isfile('../Files/Database/Database.csv'):
            copy('../Files/Database/Database.csv', '../Files/Database/VaultVersion/Database.csv')
        if path.isfile('../Files/Database/Skynet.svm'):
            copy('../Files/Database/Skynet.svm', '../Files/Database/VaultVersion/Skynet.svm')

    # Input Functions #

    def read_evaluation_xml(self, configuration_file: str) -> None:
        """
        Read the evaluation of the configuration file
        :param configuration_file: name and path of the configuration file
        :return: nothing
        """
        # Open the xml file and get the root
        root_xml = Xml.parse(configuration_file).getroot()
        evaluation_xml: Xml.Element = root_xml.find('Evaluation')
        self.__configuration_file = configuration_file

        # Read the name of the evaluation and add the timestamp
        self.__name = evaluation_xml.find('Name').text

        # Read the input of the evaluation and save it
        self.__read_input_evaluation_xml(evaluation_xml.find('Input'))

        # Read the output of the evaluation and save it
        self.__read_output_evaluation_xml(evaluation_xml.find('Output'))

    def __read_input_evaluation_xml(self, input_xml: Xml.Element) -> None:
        """
        Read the input variables of the evaluation
        :param input_xml: pointer to the xml tree to the evaluation input
        :return: nothing
        """
        self.__algorithm = Evaluation.Algorithm[input_xml.attrib['algorithm']]
        self.__generate_network = True if int(input_xml.find('GenerateNetwork').text) == 1 else False
        if not self.__generate_network:
            self.__network_file = '../Files/Inputs/Networks/' + input_xml.find('NetworkFile').text
            self.__schedule_file = '../Files/Inputs/Schedules/' + input_xml.find('ScheduleFile').text
        if self.__algorithm is Evaluation.Algorithm.ExhaustiveSimulation:
            self.__depth_link = int(input_xml.find('LinkDepth').text)
            distance_xml: Xml.Element = input_xml.find('DistanceFailure')
            self.__distance_failure = Network.TimeUnit.convert_ns(int(distance_xml.text), distance_xml.attrib['unit'])

    def __read_output_evaluation_xml(self, output_xml: Xml.Element) -> None:
        """
        Read the output variables of the evaluation
        :param output_xml: pointer to the xml tree to the evaluation output
        :return:
        """
        self.__add_database = True if int(output_xml.find('AddDatabase').text) == 1 else False
        time_xml: Xml.Element = output_xml.find('TimeClassification')
        self.__time_classification = Network.TimeUnit.convert_ns(int(time_xml.text), time_xml.attrib['unit'])

    # Output Functions #

    def normalize_database(self) -> None:
        """
        Normalize the database as merging all the values with the same input and averaging the outputs
        :return: nothing
        """
        data_read = pandas.read_csv('../Files/Database/Database.csv')
        output = {'Instance': [], 'Broken Link Utilization': [], 'Path Utilization': [], 'Total Utilization': [],
                  'Broken Link Offsets': [], 'Path Offsets': [], 'Total Offsets': [], 'Successful': [],
                  'Patching Time': [], 'Optimization Time': [], 'Classification': []}
        data_output = pandas.DataFrame(output)
        for _, data_row in data_read.iterrows():
            found = False
            for _, data_written in data_output.iterrows():
                if data_row['Broken Link Utilization'] == data_written['Broken Link Utilization'] and \
                        data_row['Path Utilization'] == data_written['Path Utilization'] and \
                        data_row['Broken Link Offsets'] == data_written['Broken Link Offsets'] and \
                        data_row['Path Offsets'] == data_written['Path Offsets']:

                    # Normalize the times
                    instances = data_written['Instance']
                    data_written['Patching Time'] = int((data_written['Patching Time'] * instances) / (instances + 1))
                    data_written['Patching Time'] += int(data_row['Patching Time'] / (instances + 1))
                    data_written['Optimization Time'] = int((data_written['Optimization Time'] * instances)
                                                            / (instances + 1))
                    data_written['Optimization Time'] += int(data_row['Optimization Time'] / (instances + 1))
                    data_written['Instance'] += 1
                    if data_written['Optimization Time'] > self.__time_classification:
                        data_written['Classification'] = 2
                    else:
                        data_written['Classification'] = 1
                    found = True
                    break
            if not found:
                data_output = data_output.append(data_row)

        with open('../Files/Database/Database_normalized.csv', 'w') as database_file:
            data_output.to_csv(database_file, index=False)

    def __write_simulation_instance(self, instance: int) -> None:
        """
        Write the simulation instance
        :param instance: number of instance
        :return: nothing
        """
        try:
            mkdir('../Files/Simulations/' + self.__name)
        except FileExistsError:
            pass

        simulation_folder = '../Files/Simulations/' + self.__name + '/SimulationInstances/'

        try:
            mkdir(simulation_folder)
        except FileExistsError:
            pass

        simulation_file = simulation_folder + 'SimulationInstance' + str(instance) + '.xml'
        self.__simulator.write_simulation_instance_xml(simulation_file)

    def __write_master_simulation(self) -> None:
        """
        Write the master simulation information
        :return: nothing
        """
        try:
            mkdir('../Files/Simulations/' + self.__name)
        except FileExistsError:
            pass
        simulation_file = '../Files/Simulations/' + self.__name + '/MasterSimulation.xml'
        self.__simulator.write_simulation_master_xml(simulation_file)
