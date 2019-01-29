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
#include <string.h>
#include "Node.h"
#include "Link.h"
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/xpath.h>
#include <libxml/xmlstring.h>
#include <libxml/globals.h>
#include <libxml/xmlwriter.h>

#endif /* Network_h */

                                                    /* STRUCT DEFINITIONS */
/**
 Structure with the information of how the switches behave in the network
 */
typedef struct Switch_Information {
    long long int min_time;             // Minimum time for the switch to process the frame
}Switch_Information;

/**
 Structure with the information of the Self-Healing Protocol and its bandwidth reservation
 */
typedef struct SelfHealing_Protocol {
    long long int period;       // Period of the protocol bandwidth reservation
    long long int time;         // Time of the protocol bandwidth reservation
}SelfHealing_Protocol;

/**
 Structure with the information of the connection from one node to another node
 */
typedef struct Connection_Topology {
    int node_id;                            // ID of the node
    // Node *node_pt;                          // Pointer to the node (we not used for now, implement if needed)
    int link_id;                            // ID of the link
    Link *link_pt;                          // Pointer to the link
}Connection_Topology;

/**
 Structure with the information of a node in the topology and all its outgoing connections
 */
typedef struct Node_Topology {
    int node_id;                            // ID of the node
    Node *node_pt;                          // Pointer to the node
    Connection_Topology *connections_pt;    // List of connections of the node
}Node_Topology;

                                                    /* CODE DEFINITIONS */

/* Getters */

/**
 Get the switch minimum time in ns

 @return switch minimum time in ns
 */
long long int get_switch_min_time(void);

/**
 Get a pointer to the Self-Healing Protocol structure

 @return pointer to the Self_Healing Protocol structure
 */
SelfHealing_Protocol * get_healing_protocol(void);

/* Setters */

/**
 Set the switch information
 
 @param min_time minimum processing time of the switch
 @return 0 if added correctly, -1 otherwise
 */
int set_switch_information(long long int min_time);

/**
 Set the information fo the Self-Healing Protocol, 0 in both period and time means that it is not active

 @param period period of the protocol in nanoseconds
 @param time time of the protocol in nanoseconds
 @return -1 if something went wrong
 */
int set_healing_protocol(long long int period, long long int time);

/* Input Functions */

/**
 Read the information of the network in the xml file and saves its information into the internal variables
 
 @param network_file name and path of the network xml file
 @return 0 if correct, -1 otherwise
 */
int read_network_xml(char *network_file);
