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
int number_nodes;                   // Number of nodes in the network
Node_Topology *topology;            // Topology of the network saved as a list of all nodes and their connections
Traffic traffic;                    // Struct that contains all the traffic in the network
int number_links;                   // Number of links in the network
int higher_link_id = 0;             // Higher read link id, used for the offset hash accelerator (hopefully not large)
int higher_frame_id = 0;            // Higher read frame id, used for frame hash accelerator (hopefully not large)

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
    fprintf(stderr, "The given timing type is not recognized\n");
    return -1;
}

/**
 Convert the given value to MBs depending of the type

 @param value given value
 @param type string with the type of the given value
 @return given value converted to MB/s
 */
int convert_to_mbs(int value, char* type) {
    
    if (strcmp(type, "MBs") == 0) {
        return value;
    }
    if (strcmp(type, "KBs") == 0) {
        return value / 1000;
    }
    if (strcmp(type, "GBs") == 0) {
        return value * 1000;
    }
    fprintf(stderr, "The given speed type is not recognized\n");
    return -1;
}

/**
 Convert the given value and type to Byte

 @param value given value
 @param type given type
 @return value converted to Byte
 */
int convert_to_byte(int value, char* type) {
    
    if (strcmp(type, "Byte") == 0) {
        return value;
    }
    if (strcmp(type, "KByte") == 0) {
        return value * 1000;
    }
    if (strcmp(type, "MByte") == 0) {
        return value * 1000000;
    }
    fprintf(stderr, "The type was not recognized to convert to Bytes\n");
    return -1;
}

/**
 Search if a given node id was defined in the topology

 @param id node id
 @return 0 if defined, -1 otherwise
 */
int is_node_id_defined(int id) {
    
    // Search in all nodes
    for (int i = 0; i < number_nodes; i++) {
        if (topology[i].node_id == id) {
            return 0;
        }
    }
    
    return -1;
}

/**
 Given the top xml of the tree and the path, get the time converted to ns

 @param top_xml pointer to the top of the tree
 @param path path where to find the value
 @return the value read converted to nanoseconds
 */
long long int get_time_value_xml(xmlDoc *top_xml, char* path) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value, *value2;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    
    long long int time;
    
    // Search for the value
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
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
 Get the time value of a given path in an ocurrence

 @param top_xml pointer to the top of the tree
 @param path path to find the ocurrence
 @param num number of the ocurrence
 @param subpath path inside the ocurrence
 @return time value in nanoseconds
 */
long long int get_occur_time_value_xml(xmlDoc *top_xml, char* path, int num, char* subpath) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value, *value2;
    xmlXPathContextPtr context, context_value;
    xmlXPathObjectPtr result, result_value;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeNr == 0) {
        fprintf(stderr, "The searched value is not defined\n");
        return -1;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return -1;
    }
    
    // Set new context to the given num and search for the value
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    if (result_value->nodesetval->nodeNr == 0) {
        return -1;
    }
    value = xmlNodeListGetString(top_xml, result_value->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    value2 = xmlGetProp(result_value->nodesetval->nodeTab[0], (xmlChar*) "unit");
    
    // Convert the read value into nanoseconds and save
    long long int time = atoll((const char*) value);
    time = convert_to_ns(time, (char*) value2);
    
    // Free xml objects
    xmlFree(value);
    xmlFree(value2);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    
    return time;
}

int get_occur_size_value_xml(xmlDoc *top_xml, char* path, int num, char* subpath) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value, *value2;
    xmlXPathContextPtr context, context_value;
    xmlXPathObjectPtr result, result_value;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeNr == 0) {
        fprintf(stderr, "The searched value is not defined\n");
        return -1;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return -1;
    }
    
    // Set new context to the given num and search for the value
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    if (result_value->nodesetval->nodeNr == 0) {
        return -1;
    }
    value = xmlNodeListGetString(top_xml, result_value->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    value2 = xmlGetProp(result_value->nodesetval->nodeTab[0], (xmlChar*) "unit");
    
    // Convert the read value into nanoseconds and save
    int size = atoi((const char*) value);
    size = convert_to_byte(size, (char*) value2);
    
    // Free xml objects
    xmlFree(value);
    xmlFree(value2);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    
    return size;
}

/**
 For the given tree and path, return the number of occurrences as a findall search

 @param top_xml pointer to the top of the tree
 @param path path where to search
 @return number of occurrences
 */
int get_occurences_xml(xmlDoc *top_xml, char* path) {
    
    // Init xml variables needed to search information in the file
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    
    // Search for number of occurences
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        return 0;
    }
    int num = result->nodesetval->nodeNr;
    
    // Free xml objects
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    
    return num;
}

/**
 For the given tree, and paths, find the number of occurences of the subpath inside the path

 @param top_xml pointer to the top of the tree
 @param path path where to search the first occurrence
 @param num number of the ocurrence
 @param subpath where to search inside the ocurrence
 @return number of ocurreces found in the subpath
 */
int get_ocurrences_in_ocurrences_xml(xmlDoc *top_xml, char* path, int num, char* subpath) {
    
    // Init xml variables needed to search information in the file
    xmlXPathContextPtr context, context_value;
    xmlXPathObjectPtr result, result_value;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return 0;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return 0;
    }
    
    // Set new context to the given num and search for the next subpath
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    
    int num_occur = result_value->nodesetval->nodeNr;
    
    // Free xml objects
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    
    return num_occur;
}

/**
 Get the name of the given property for a given id of the occurent of the path

 @param top_xml pointer to the top of the tree
 @param path path to search
 @path num id number of the occurence
 @param property name of the property to search
 @return the name of the occurrence, NULL if something went wrong
 */
char *get_property_occur_xml(xmlDoc *top_xml, char *path, int num, char* property) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    char *return_value;
    
    // Search for the value
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return NULL;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return NULL;
    }
    
    // Search for the property
    value = xmlGetProp(result->nodesetval->nodeTab[num], (xmlChar*) property);
    return_value = (char*) xmlStrdup(value);
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    
    return return_value;
}

/**
 Get the value of the subpath search for the given occurrence

 @param top_xml pointer to the top of the tree
 @param path path of the occurrence
 @param num number of the occurrence
 @param subpath path to search inside the occurrence
 @return value found, -1 if failed
 */
char *get_occur_value_xml(xmlDoc *top_xml, char *path, int num, char* subpath) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context, context_value;
    xmlXPathObjectPtr result, result_value;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return NULL;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return NULL;
    }
    
    // Set new context to the given num and search for the value
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    value = xmlNodeListGetString(top_xml, result_value->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    char *return_value = (char*) xmlStrdup(value);
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    
    return return_value;
}

/**
 Get the property in an occurrence inside an ocurrence with a given final path

 @param top_xml pointer to the top of the tree
 @param path first ocurrence path
 @param num number of the ocurrence
 @param subpath second ecurrence path
 @param subnum number of the second ocurrence
 @param find_path path to find
 @param property property to find
 @return value of the found property
 */
char *get_prop_occur_in_occur_xml(xmlDoc *top_xml, char *path, int num, char *subpath, int subnum, char *find_path,
                                char *property) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context, context_value, context_final;
    xmlXPathObjectPtr result, result_value, result_final;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return NULL;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return NULL;
    }
    
    // Set new context to the given num and search for the next subpath
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    if (result_value->nodesetval->nodeNr < subnum) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return 0;
    }
    
    // Set the final context and catch the value
    context_final = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result_value->nodesetval->nodeTab[subnum], context_final);
    result_final = xmlXPathEvalExpression((xmlChar *) find_path, context_final);
    value = xmlGetProp(result_final->nodesetval->nodeTab[0], (xmlChar*) property);
    char *return_value = (char*) xmlStrdup(value);      // Copy the string as we free it later on
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeObject(result_final);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    xmlXPathFreeContext(context_final);
    
    return return_value;
}

/**
 Find the value from an ocurrence path inside another occurence path

 @param top_xml pointer to the top of the tree
 @param path first ocurrence path
 @param num number in the ocurrence
 @param subpath second ocurrence path
 @param subnum number in the second ocurrence
 @param find_path path of the value to search
 @return value found
 */
char *get_ocurr_in_ocurr_value_xml(xmlDoc *top_xml, char *path, int num, char *subpath, int subnum, char* find_path) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context, context_value, context_final;
    xmlXPathObjectPtr result, result_value, result_final;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return NULL;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return NULL;
    }
    
    // Set new context to the given num and search for the next subpath
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    if (result_value->nodesetval->nodeNr < subnum) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return NULL;
    }
    
    // Set the final context and catch the value
    context_final = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result_value->nodesetval->nodeTab[subnum], context_final);
    result_final = xmlXPathEvalExpression((xmlChar *) find_path, context_final);
    value = xmlNodeListGetString(top_xml, result_final->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    char* return_value = (char*) xmlStrdup(value);
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeObject(result_final);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    xmlXPathFreeContext(context_final);
    
    return return_value;
}

/**
 Find the speed value from an ocurrence path inside another occurence path and return it in MB/s
 
 @param top_xml pointer to the top of the tree
 @param path first ocurrence path
 @param num number in the ocurrence
 @param subpath second ocurrence path
 @param subnum number in the second ocurrence
 @param find_path path of the value to search
 @return speed value found converted to MB/s
 */
int get_occur_in_ocurr_speed_value_xml(xmlDoc *top_xml, char *path, int num, char *subpath, int subnum,
                                       char* find_path) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value, *value2;
    xmlXPathContextPtr context, context_value, context_final;
    xmlXPathObjectPtr result, result_value, result_final;
    
    // Search for the num occurrence
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value is not defined\n");
        return 0;
    }
    if (result->nodesetval->nodeNr < num) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return 0;
    }
    
    // Set new context to the given num and search for the next subpath
    context_value = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result->nodesetval->nodeTab[num], context_value);
    result_value = xmlXPathEvalExpression((xmlChar*) subpath, context_value);
    if (result_value->nodesetval->nodeNr < subnum) {
        fprintf(stderr, "The searched path does not have as many occurences as searched\n");
        return 0;
    }
    
    // Set the final context and catch the value
    context_final = xmlXPathNewContext(top_xml);
    xmlXPathSetContextNode(result_value->nodesetval->nodeTab[subnum], context_final);
    result_final = xmlXPathEvalExpression((xmlChar *) find_path, context_final);
    value = xmlNodeListGetString(top_xml, result_final->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    value2 = xmlGetProp(result_final->nodesetval->nodeTab[0], (xmlChar*) "unit");
    int speed = atoi((const char*) value);
    speed = convert_to_mbs(speed, (char*) value2);
    
    // Free xml objects
    xmlFree(value);
    xmlFree(value2);
    xmlXPathFreeObject(result);
    xmlXPathFreeObject(result_value);
    xmlXPathFreeObject(result_final);
    xmlXPathFreeContext(context);
    xmlXPathFreeContext(context_value);
    xmlXPathFreeContext(context_final);
    
    return speed;
}

/**
 Read the switch information and save its into memory

 @param top_xml pointer to the top of the network xml file
 @return 0 if all information was saved correctly, -1 otherwise
 */
int read_switch_xml(xmlDoc *top_xml) {

    char* path = "/NetworkConfiguration/GeneralInformation/SwitchInformation/MinimumTime";
    long long int switch_time = get_time_value_xml(top_xml, path);
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
    long long int period = get_time_value_xml(top_xml, path_period);
    
    // If the data was not found or set incorrectly, assume there is no self-healing protocol
    if (period == -1) {
        set_healing_protocol(0, 0);
        return 0;
    }
    
    char* path_time = "/NetworkConfiguration/GeneralInformation/SelfHealingProtocol/Time";
    long long int time = get_time_value_xml(top_xml, path_time);
    
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

/**
 Read and save the information of the topology

 @param top_xml pointer to the top of the tree
 @return 0 if read and saved correctly, -1 otherwise
 */
int read_topology_xml(xmlDoc *top_xml) {
 
    // Read the number of nodes and allocate the needed memory for the topology
    char *path = "/NetworkConfiguration/TopologyInformation/Node";
    int num_nodes = get_occurences_xml(top_xml, path);
    if (num_nodes <= 0) {
        fprintf(stderr, "No nodes found in the topology description\n");
    }
    number_nodes = num_nodes;
    number_links = 0;
    topology = malloc(sizeof(Node_Topology) * num_nodes);
    for (int i = 0; i < num_nodes; i++) {
        topology[i].node_pt = malloc(sizeof(Node));     // Allocate memory first
    }
    
    // For all nodes, save the information
    for (int i = 0; i < num_nodes; i++) {
        
        // Set the category of the node
        char *node_type = get_property_occur_xml(top_xml, path, i, "category");
        if (set_nodetype_str(topology[i].node_pt, node_type) == -1) {
            fprintf(stderr, "The node type could not be saved correctly\n");
            return -1;
        }
        
        // Search and save the node id
        char *value = get_occur_value_xml(top_xml, path, i, "NodeID");
        if (value == NULL) {
            fprintf(stderr, "The node id could not be saved correctly\n");
            return -1;
        }
        int node_id = atoi(value);
        if (node_id < 0) {
            fprintf(stderr, "The node id needs to be a natural number\n");
            return -1;
        }
        // Check if the node was defined before
        for (int j = 0; j < i; j++) {
            if (topology[j].node_id == node_id) {
                fprintf(stderr, "The node id %d has been defined multiple times\n", node_id);
                return -1;
            }
        }
        topology[i].node_id = node_id;
        
        // Read the number of connections and allocate the needed memory, also allocate all the pointers correctly
        int num_connections = get_ocurrences_in_ocurrences_xml(top_xml, path, i, "Connection");
        topology[i].connections_pt = malloc(sizeof(Connection_Topology) * num_connections);
        for (int j = 0; j < num_connections; j++) {
            topology[i].connections_pt[j].link_pt = malloc(sizeof(Link));
        }
        // For all the connections, save the information
        for (int j = 0; j < num_connections; j++) {
            number_links += 1;
            // Search and save the node id and point to it
            char *value = get_ocurr_in_ocurr_value_xml(top_xml, path, i, "Connection", j, "NodeID");
            if (value == NULL) {
                fprintf(stderr, "The node %d failed to find the node id of one of its connections \n", node_id);
                return -1;
            }
            int node_id = atoi(value);
            if (node_id < 0) {
                fprintf(stderr, "The node id needs to be a natural number\n");
                return -1;
            }
            if (node_id == topology[i].node_id) {
                fprintf(stderr, "The node %d is connected to itself\n", node_id);
                return -1;
            }
            topology[i].connections_pt[j].node_id = node_id;
            
            // Search the link id
            value = get_ocurr_in_ocurr_value_xml(top_xml, path, i, "Connection", j, "Link/LinkID");
            if (value == NULL) {
                fprintf(stderr, "The node %d failed to find the link id of one of its connections \n", node_id);
                return -1;
            }
            int link_id = atoi(value);
            if (link_id < 0) {
                fprintf(stderr, "The link id needs to be a natural number\n");
                return -1;
            }
            for (int h = 0; h < j; h++) {
                if (topology[i].connections_pt[h].link_id == link_id) {
                    fprintf(stderr, "The node %d has two connections with the same link %d\n", node_id, link_id);
                    return -1;
                }
            }
            topology[i].connections_pt[j].link_id = link_id;
            if (link_id > higher_link_id) {
                higher_link_id = link_id;
            }
            
            // Seach the link type and the speed and save it
            char *link_type = get_prop_occur_in_occur_xml(top_xml, path, i, "Connection", j, "Link", "category");
            int speed = get_occur_in_ocurr_speed_value_xml(top_xml, path, i, "Connection", j, "Link/Speed");
            if (set_link_str(topology[i].connections_pt[j].link_pt, link_type, speed) == -1) {
                fprintf(stderr, "Error setting the values of link %d\n", link_id);
                return -1;
            }
        }
    }
    
    return 0;
}

/**
 Read the traffic of the network and save it in memory

 @param top_xml pointer to the top of the tree
 @return 0 if done correctly, -1 otherwise
 */
int read_traffic_xml(xmlDoc *top_xml) {
    
    // Read the number of frames and allocate the needed memory in the list of frames
    char *path = "/NetworkConfiguration/TrafficDescription/Frame";
    int num_frames = get_occurences_xml(top_xml, path);
    if (num_frames <= 0) {
        fprintf(stderr, "No frames found in the traffic description\n");
        return -1;
    }
    traffic.num_frames = num_frames;
    traffic.frames = malloc(sizeof(Frame) * num_frames);
    traffic.frames_id = malloc(sizeof(int) * num_frames);
    
    // For all frames, save its information
    for (int i = 0; i < num_frames; i++) {
        
        // Search and save the frame ID
        char *value = get_occur_value_xml(top_xml, path, i, "FrameID");
        if (value == NULL) {
            fprintf(stderr, "A frameID could not be found\n");
            return -1;
        }
        int frame_id = atoi(value);
        if (frame_id < 0) {
            fprintf(stderr, "The frameID should be a natural number\n");
            return -1;
        }
        traffic.frames_id[i] = frame_id;
        
        // Seach and save the sender ID
        value = get_occur_value_xml(top_xml, path, i, "SenderID");
        if (value == NULL) {
            fprintf(stderr, "A SenderID could not be found\n");
            return -1;
        }
        int sender_id = atoi(value);
        if (is_node_id_defined(sender_id) == -1) {
            fprintf(stderr, "The frame %d has the sender %d not defined in the topology\n", frame_id, sender_id);
            return -1;
        }
        set_sender_id(&traffic.frames[i], sender_id);
        
        // Search and save the period
        long long int period = get_occur_time_value_xml(top_xml, path, i, "Period");
        if (set_period(&traffic.frames[i], period) == -1) {
            fprintf(stderr, "The period of the frame %d is not well defined\n", frame_id);
            return -1;
        }
        
        // Search and save the deadline, deadline == 0 or missing => deadline = period
        long long int deadline = get_occur_time_value_xml(top_xml, path, i, "Deadline");
        if (deadline == -1) {
            set_deadline(&traffic.frames[i], 0);
        } else {
            if (set_deadline(&traffic.frames[i], deadline) == -1) {
                fprintf(stderr, "The deadline of the frame %d is not well defined\n", frame_id);
                return -1;
            }
        }
        
        // Search and save the size, size missing or 0 ==> size = 1000 Bytes
        int size = get_occur_size_value_xml(top_xml, path, i, "Size");
        if (size == -1 || size == 0) {
            set_size(&traffic.frames[i], 1000);
        } else {
            if (set_size(&traffic.frames[i], size) == -1) {
                fprintf(stderr, "The size of the frame %d is not well defined\n", frame_id);
                return -1;
            }
        }
        
        // Search and save the starting time, starting time missing ==> starting time = 0
        long long int starting_time = get_occur_time_value_xml(top_xml, path, i, "StartingTime");
        if (starting_time == -1) {
            set_starting_time(&traffic.frames[i], 0);
        } else {
            if (set_starting_time(&traffic.frames[i], starting_time) == -1) {
                fprintf(stderr, "The starting time of the frame %d is not well defined\n", frame_id);
                return -1;
            }
        }
        
        // Seach and save the end to end time, end to end time missing ==> end to end = 0 => not taken into account
        long long int end = get_occur_time_value_xml(top_xml, path, i, "EndToEnd");
        if (end == -1) {
            set_end_to_end(&traffic.frames[i], 0);
        } else {
            if (set_end_to_end(&traffic.frames[i], end) == -1) {
                fprintf(stderr, "The end to end time of the frame %d is not well defined\n", frame_id);
                return -1;
            }
        }
        
        // Read the number of receivers and allocate the needed memory
        int num_receivers = get_ocurrences_in_ocurrences_xml(top_xml, path, i, "Paths/Receiver");
        traffic.frames[i].num_paths = num_receivers;
        traffic.frames[i].receivers_id = malloc(sizeof(int) * num_receivers);
        traffic.frames[i].list_paths = malloc(sizeof(Path*) * num_receivers);
        for (int j = 0; j < num_receivers; j++) {
            
            // Read the receiver ID
            value = get_ocurr_in_ocurr_value_xml(top_xml, path, i, "Paths/Receiver", j, "ReceiverID");
            if (value == NULL) {
                fprintf(stderr, "A ReceiverID could not be found\n");
                return -1;
            }
            int receiver_id = atoi(value);
            if (is_node_id_defined(receiver_id) == -1) {
                fprintf(stderr, "The frame %d has the sender %d not defined in the topology\n", frame_id, receiver_id);
                return -1;
            }
            set_receiver_id(&traffic.frames[i], j, receiver_id);
            
            // Read and save the path into the traffic structure
            value = get_ocurr_in_ocurr_value_xml(top_xml, path, i, "Paths/Receiver", j, "Path");
            // Parse the string into an array
            char *link_char = strtok(value, ";");
            int link_char_it = 0;
            int *path_array = NULL;
            // Count the number of hops, to avoid reallocs and potential memory leaks
            while (link_char != NULL) {
                if (path_array == NULL) {
                    path_array = malloc(sizeof(int));
                } else {
                    path_array = realloc(path_array, sizeof(int) * link_char_it + 1);
                }
                path_array[link_char_it] = atoi(link_char);
                link_char = strtok(NULL, ";");
                link_char_it++;
            }
            set_path_receiver_id(&traffic.frames[i], receiver_id, path_array, link_char_it);
            
        }
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
    
    // Read the topology of the network
    if (read_topology_xml(top_xml) == -1) {
        fprintf(stderr, "The topology of the network could not be read\n");
        return -1;
    }
    
    // Read the traffic of the network
    if (read_traffic_xml(top_xml) == -1) {
        fprintf(stderr, "The traffic of the network could not be read\n");
        return -1;
    }
    
    printf("It is working for now\n");
    return 0;
}
