/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Link.c                                                                                                             *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Description in Link.h                                                                                              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include "Link.h"

                                                /* AUXILIAR FUNCTIONS */

                                                    /* FUNCTIONS */

/* Getters */

/**
 Get the link speed
 */
int get_speed(Link *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given link pointer is null\n");
        return -1;
    }
    
    return pt->speed;
}

/**
 Get the link type
 */
LinkType get_type(Link *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given link pointer is null\n");
        return -1;
    }
    
    return pt->type;
}

/* Setters */

/**
 Set the link information
 */
int set_link(Link *pt, LinkType type, int speed) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given link pointer is null\n");
        return -1;
    }
    
    if (speed <= 0) {
        fprintf(stderr, "The link speed should be a positive number\n");
        return -1;
    }
    
    pt->speed = speed;
    pt->type = type;
    return 0;
}
