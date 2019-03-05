import Network
import Simulation

if __name__ == "__main__":

    n = Network.Network()
    # n.read_network_xml('../Files/Configurations/Configuration.xml')
    # n.create_network()
    # n.write_network_xml('../Files/Networks/network.xml')
    n.read_network_xml('../Files/Networks/network.xml')
    n.read_schedule_xml('../Files/Schedules/schedule.xml')
    s = Simulation.Simulation(n)
    s.read_simulation_xml('../Files/Configurations/Configuration.xml')
    s.simulate()
    print('Stop here to debug')

