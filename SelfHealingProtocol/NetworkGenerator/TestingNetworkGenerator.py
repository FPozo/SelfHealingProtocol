import Network

if __name__ == "__main__":

    n = Network.Network()
    # n.read_network_xml('../Files/Configurations/Configuration.xml')
    # n.create_network()
    # n.write_network_xml('../Files/Networks/network.xml')
    n.read_network_xml('../Files/Networks/network.xml')
    n.read_schedule_xml('../Files/Schedules/schedule.xml')
    print('Stop here to debug')