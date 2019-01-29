/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Link.h                                                                                                             *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that contains the information of a single link in the network.                                             *
 *  A link containts the information of the speed of the link and the type (wired or wireless).                        *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#ifndef Link_h
#define Link_h

#include <stdio.h>
#include <string.h>

#endif /* Link_h */

                                                /* STRUCT DEFINITIONS */

/**
 Enumeration of different types of links
 */
typedef enum LinkType {
    wired,
    wireless
}LinkType;

/**
 Structure with the information of the link type and speed
 */
typedef struct Link {
    LinkType type;          // Type of the link
    int speed;              // Speed of the link in MB/s
}Link;

                                                /* CODE DEFINITIONS */

/* Getters */

/**
 Get the link speed

 @param pt pointer to the Link
 @return speed in MB/s
 */
int get_speed(Link *pt);

/**
 Get the link type

 @param pt pointer to the link
 @return link type
 */
LinkType get_linktype(Link *pt);

/* Setters */

/**
 Set the link information

 @param pt Pointer to the link
 @param type type of the ink
 @param speed speed of the link in MB/s
 @return 0 if done correctly, -1 otherwise
 */
int set_link(Link *pt, LinkType type, int speed);

/**
 Set the link information with the type as string
 
 @param pt Pointer to the link
 @param type string describing the link type
 @param speed speed of the link in MB/s
 @return 0 if done correctly, -1 otherwise
 */
int set_link_str(Link *pt, char* type, int speed);
