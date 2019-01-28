/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Network.h                                                                                                          *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 28/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that contains the information of the network.                                                              *
 *  A network has the information of all the frames saved in an array                                                  *
 *  Additions of new relations between frames are supposed to be added here, while the behavior is on the schedule,    *
 *  as done with the period and deadlines between others.                                                              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */


#ifndef Network_h
#define Network_h

#include <stdio.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/xpath.h>
#include <libxml/xmlstring.h>
#include <libxml/globals.h>
#include <libxml/xmlwriter.h>

#endif /* Network_h */

                                                    /* STRUCT DEFINITIONS */

                                                    /* CODE DEFINITIONS */

/**
 Read the information of the network in the xml file and saves its information into the internal variables
 
 @param network_file name and path of the network xml file
 @return 0 if correct, -1 otherwise
 */
int read_network_xml(char *network_file);
