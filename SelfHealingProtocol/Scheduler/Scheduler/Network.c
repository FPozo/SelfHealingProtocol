/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Network.h                                                                                                          *
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

                                            /* AUXILIAR FUNCTIONS */

/**
 Read the general information of the network and add its into the Network variables

 @param top_xml pointer to general information tree
 @return 0 if all information was saved correctly, -1 otherwise
 */
int read_general_information_xml(xmlDoc *top_xml) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    
    // Search for the minimum switch processing time and save it
    context = xmlXPathNewContext(top_xml);
    xmlChar *path = (xmlChar*) "/NetworkConfiguration/GeneralInformation/SwitchInformation/MinimumTime";
    result = xmlXPathEvalExpression(path, context);
    if (result->nodesetval->nodeTab == NULL) {
        printf("The Switch Minimum Time is not defined\n");
        return -1;
    }
    value = xmlNodeListGetString(top_xml, result->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    
    return 0;
}

                                                /* FUNCTIONS */

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
