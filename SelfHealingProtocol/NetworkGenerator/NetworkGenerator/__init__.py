# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  NetworkGenerator                                                                                                   *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/12/18.                                                                             *
 *  Copyright © 2018 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package to create Deterministic Ethernet Networks                                                                  *
 *  This modulo creates networks using the NetworkX package and fill it with time-triggered traffic.                   *
 *  The traffic will be send from a sender to one or multiple receivers, and it can be specified a path in the network *
 *  or leave it open for others to implement. The traffic will contain a period, a deadline, an end to end delay and   *
 *  size.                                                                                                              *
 *  The package has an input and output interface with an specific XML file to feed with parameters and output         *
 *  another XML file with the constructed network information.                                                         *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """
