from Network import Network
from Simulator import Simulation

if __name__ == "__main__":

    n = Network()
    # n.read_network_xml('../Files/Configurations/Configuration.xml')
    # n.create_network()
    # n.write_network_xml('../Files/Networks/network.xml')
    n.read_network_xml('../Files/Inputs/Networks/NetworkSmall50.xml')
    n.read_schedule_xml('../Files/Inputs/Schedules/ScheduleSmall50.xml')
    s = Simulation(n)
    s.read_simulation_xml('../Files/Configurations/SimulationConfiguration.xml')
    s.simulate()
    print('Stop here to debug')
