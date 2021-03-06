/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Node.h                                                                                                             *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that contains the information of a single node in the network.                                             *
 *  A node containts the information of type (End System or Switch or Access Point).                                   *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */


#ifndef Node_h
#define Node_h

#include <stdio.h>
#include <string.h>

#endif /* Node_h */

                                                    /* STRUCT DEFINITIONS */

/**
 Enumeration of different types of nodes
 */
typedef enum NodeType {
    EndSystem,
    Switch,
    AccessPoint
}NodeType;

/**
 Struct with the information of the node
 */
typedef struct Node {
    NodeType type;      // Type of the node
}Node;

                                                    /* CODE DEFINITIONS */

/* Getters */

/**
 Get the node type

 @param pt pointer to the node
 @return node type
 */
NodeType get_nodetype(Node *pt);

/* Setters */

/**
 Set the node type

 @param pt pointer to the node
 @param type node type
 @return 0 if done correctly, -1 otherwise
 */
int set_nodetype(Node *pt, NodeType type);

/**
 Set the node type by giving a str

 @param pt pointer to the node
 @param str_type string with the value to cast to the enum
 @return 0 if done correctly, -1 otherwise
 */
int set_nodetype_str(Node *pt, char* str_type);
