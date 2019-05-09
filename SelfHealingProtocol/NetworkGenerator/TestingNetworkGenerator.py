import Network

if __name__ == "__main__":

    n = Network.Network()
    # n.read_network_xml('../Files/Configurations/Configuration.xml')
    # n.create_network()
    # n.write_network_xml('../Files/Networks/network.xml')
    n.read_network_xml('../Files/Inputs/Networks/NetworkLarge100.xml')
    n.read_schedule_xml('../Files/Inputs/Schedules/ScheduleLarge100.xml')
    n.calculate_max_memory_switches()
    print('Stop here to debug')
