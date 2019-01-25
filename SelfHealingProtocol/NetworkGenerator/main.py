import Network

if __name__ == "__main__":

    n = Network.Network()
    n.read_network_xml('../Files/Configurations/Configuration.xml')
    n.create_network()
    n.write_network_xml('../Files/Networks/network.xml')
    print('Stop here to debug')
