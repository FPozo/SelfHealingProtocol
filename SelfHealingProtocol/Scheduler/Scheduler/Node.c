/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Node.c                                                                                                             *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Description in Node.h                                                                                              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include "Node.h"

                                                /* AUXILIAR FUNCTIONS */

                                                    /* FUNCTIONS */

/* Getters */

/**
 Get the node type
 */
NodeType get_nodetype(Node *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given node pointer is null\n");
        return -1;
    }
    
    return pt->type;
}

/* Setters */

/**
 Set the node type
 */
int set_nodetype(Node *pt, NodeType type) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given node pointer is null\n");
        return -1;
    }
    
    pt->type = type;
    return 0;
}

/**
 Set the node type by giving a str
 */
int set_nodetype_str(Node *pt, char* str_type) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given node pointer is null\n");
        return -1;
    }
    
    // Check which node type was given as string
    if (strcmp(str_type, "EndSystem") == 0) {
        pt->type = EndSystem;
    } else if (strcmp(str_type, "Switch") == 0) {
        pt->type = Switch;
    } else if (strcmp(str_type, "AccessPoint") == 0) {
        pt->type = AccessPoint;
    } else {
        fprintf(stderr, "The given node type is not defined\n");
        return -1;
    }
    return 0;
}
