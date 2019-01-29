/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Network.c                                                                                                          *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 28/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Desription in Network.h                                                                                            *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */


#include "Network.h"

                                                /* VARIABLES */

Switch_Information switch_info;     // Information of the behaviour of switches
SelfHealing_Protocol healing_prot;  // Information of the self-healing protocol characteristics

                                            /* AUXILIAR FUNCTIONS */

/**
 Convert the given value to nanoseconds

 @param value value to convert
 @param type type of unit given
 @return value converted to nanoseconds, -1 if the type is not recognized
 */
long long int convert_to_ns(long long int value, char* type) {
    
    if (strcmp(type, "ns") == 0) {
        return value;
    }
    if (strcmp(type, "us") == 0) {
        return value * 1000;
    }
    if (strcmp(type, "ms") == 0) {
        return value * 1000000;
    }
    if (strcmp(type, "s") == 0) {
        return value * 1000000000;
    }
    fprintf(stderr, "The given type is not recognized\n");
    return -1;
}

/**
 Given the top xml of the tree and the path, get the time converted to ns

 @param top_xml pointer to the top of the tree
 @param path path where to find the value
 @return the value read converted to nanoseconds
 */
long long int get_time_value(xmlDoc *top_xml, char* path) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value, *value2;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    
    long long int time;
    
    // Search for the minimum switch processing time and save it
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        printf("The Switch Minimum Time is not defined\n");
        return -1;
    }
    value = xmlNodeListGetString(top_xml, result->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    value2 = xmlGetProp(result->nodesetval->nodeTab[0], (xmlChar*) "unit");
    
    // Convert the read value into nanoseconds and save
    time = atoll((const char*) value);
    time = convert_to_ns(time, (char*) value2);
    
    // Free xml objects
    xmlFree(value);
    xmlFree(value2);
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    
    return time;
    
}

/**
 Read the switch information and save its into memory

 @param top_xml pointer to the top of the network xml file
 @return 0 if all information was saved correctly, -1 otherwise
 */
int read_switch_xml(xmlDoc *top_xml) {

    char* path = "/NetworkConfiguration/GeneralInformation/SwitchInformation/MinimumTime";
    long long int switch_time = get_time_value(top_xml, path);
    set_switch_information(switch_time);
    
    return 0;
}

/**
 Read the Self-Healing Protocol information of the network and add it to the structure.
 If there is no data, set protocol as 0.
 
 @param top_xml pointer to the top of the tree
 @return 0 if all information was saved correctly, -1 otherwise
 */
int read_healing_protocol_xml(xmlDoc *top_xml) {
    
    char* path_period = "/NetworkConfiguration/GeneralInformation/SelfHealingProtocol/Period";
    long long int period = get_time_value(top_xml, path_period);
    
    // If the data was not found or set incorrectly, assume there is no self-healing protocol
    if (period == -1) {
        set_healing_protocol(0, 0);
        return 0;
    }
    
    char* path_time = "/NetworkConfiguration/GeneralInformation/SelfHealingProtocol/Time";
    long long int time = get_time_value(top_xml, path_time);
    
    set_healing_protocol(period, time);
    
    return 0;
}

/**
 Read the general information of the network and add its into the Network variables

 @param top_xml pointer to general information tree
 @return 0 if all information was saved correctly, -1 otherwise
 */
int read_general_information_xml(xmlDoc *top_xml) {
    
    if (read_switch_xml(top_xml) == -1) {
        fprintf(stderr, "Error while reading the switch information\n");
        return -1;
    }
    
    if (read_healing_protocol_xml(top_xml) == -1) {
        fprintf(stderr, "Error while reading the Self-Healing Protocol information\n");
        return -1;
    }
    
    return 0;
}



                                                /* FUNCTIONS */

/* Getters */

/**
 Get the switch minimum time in ns
 */
long long int get_switch_min_time(void) {
    
    return switch_info.min_time;
}

/**
 Get a pointer to the Self-Healing Protocol structure
 */
SelfHealing_Protocol * get_healing_protocol(void) {
    
    return &healing_prot;
}

/* Setters */

/**
 Set the switch information in nanoseconds
 */
int set_switch_information(long long int min_time) {
    
    if (min_time < 0) {
        fprintf(stderr, "The switch minimum time should be a natural number");
        return -1;
    }
    
    switch_info.min_time = min_time;
    return 0;
}

/**
 Set the information fo the Self-Healing Protocol, 0 in both period and time means that it is not active
 */
int set_healing_protocol(long long int period, long long int time) {
    
    if (period == 0) {
        healing_prot.period = 0;
        healing_prot.time = 0;
    } else if (period < 0 || time <= 0) {
        fprintf(stderr, "The values in the Self-Healing Protocol should be natural\n");
        return -1;
    } else {
        healing_prot.period = period;
        healing_prot.time = time;
    }
    return 0;
}

/* Input Functions */

/**
 Reads the given network xml file and parse everything into the network variables.
 It starts reading the general information of the network.
 Then continues with the important information from the network components description (links and its speeds).
 It ends with the information of each frame including its individual paths.
 */
int read_network_xml(char *network_file) {
    
    xmlDoc *top_xml;        // Variable that contains the xml document top tree
    
    // Open the xml file if it exists
    top_xml = xmlReadFile(network_file, NULL, 0);
    if (top_xml == NULL) {
        fprintf(stderr, "The given xml file does not exist\n");
        return -1;
    }
    
    // Read the general information of the network
    if (read_general_information_xml(top_xml) == -1) {
        fprintf(stderr, "The general information of the network could not be read\n");
        return -1;
    }
    
    printf("It is working for now\n");
    return 0;
}
