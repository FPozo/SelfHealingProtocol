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
NodeType get_type(Node *pt) {
    
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
int set_type(Node *pt, NodeType type) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given node pointer is null\n");
        return -1;
    }
    
    pt->type = type;
    return 0;
}
