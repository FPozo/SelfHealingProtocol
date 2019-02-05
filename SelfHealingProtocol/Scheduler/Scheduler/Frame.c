/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Frame.c                                                                                                            *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Description in Frame.h                                                                                             *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include "Frame.h"

                                                /* AUXILIAR FUNCTIONS */

                                                    /* FUNCTIONS */

/* Getters */

/**
 Get the sender id
 */
int get_sender_id(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->sender_id;
}

/**
 Get the receiver id
 */
int get_receiver_id(Frame *pt, int num) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->receivers_id[num];
}

/**
 Get the period of the frame in nanoseconds
 */
long long int get_period(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->period;
}

/**
 Get the deadline of the frame in nanoseconds
 */
long long int get_deadline(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->deadline;
}

/**
 Get the size of the frame
 */
int get_size(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->size;
}

/**
 Get the starting time of the frame
 */
long long int get_starting_time(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->starting;
}

/**
 Get the end to end time of the frame
 */
long long int get_end_to_end(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->end_to_end_delay;
}

/**
 Get the number of different offsets of the frame
 */
int get_num_offsets(Frame *pt) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    return pt->num_offsets;
}

/**
 Get the link id of the frame by the offset iteration
 */
int get_link_id_offset(Frame *pt, int offset_it) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (offset_it < 0 || offset_it >= pt->num_offsets) {
        fprintf(stderr, "The given offset iterator number is out of the bounds\n");
        return -1;
    }
    
    return pt->offset_it[offset_it]->link_id;
    
}

/* Setters */

/**
 Set the sender id
 */
int set_sender_id(Frame *pt, int sender_id) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (sender_id < 0) {
        fprintf(stderr, "The sender ID has to be a natural number\n");
        return -1;
    }
    
    pt->sender_id = sender_id;
    return 0;
}

/**
 Set the receiver id
 @return 0 if done correctly, -1 otherwise
 */
int set_receiver_id(Frame *pt, int num, int receiver_id) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (receiver_id < 0) {
        fprintf(stderr, "The sender ID has to be a natural number\n");
        return -1;
    }
    if (num < 0 || num >= pt->num_paths) {
        fprintf(stderr, "The given index for the receiver id is invalid\n");
        return -1;
    }
    
    pt->receivers_id[num] = receiver_id;
    return 0;
}

/**
 Set the period of the frame
 */
int set_period(Frame *pt, long long int period) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (period <= 0) {
        fprintf(stderr, "The period of the frame should be a natural number\n");
        return -1;
    }
    
    pt->period = period;
    return 0;
}

/**
 Set the deadline of the frame
 */
int set_deadline(Frame *pt, long long int deadline) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (deadline < 0) {
        fprintf(stderr, "The deadline should be a natural number\n");
        return -1;
    }
    if (deadline > pt->period) {
        fprintf(stderr, "The deadline cannot be larger than the period\n");
        return -1;
    }
    if (deadline == 0) {
        pt->deadline = pt->period;
    } else {
        pt->deadline = deadline;
    }
    return 0;
}

/**
 Set the size of the frame
 */
int set_size(Frame *pt, int size) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (size <= 0) {
        fprintf(stderr, "The size of the frame should be a positive number\n");
        return -1;
    }
    
    pt->size = size;
    return 0;
}

/**
 Set the starting time of the frame
 */
int set_starting_time(Frame *pt, long long int starting_time) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (starting_time < 0) {
        fprintf(stderr, "The starting time of the frame should be a natural number\n");
        return -1;
    }
    if (starting_time >= pt->deadline) {
        fprintf(stderr, "The starting time of the frame cannot be larger than the deadline\n");
        return -1;
    }
    
    pt->starting = starting_time;
    return 0;
}

/**
 Set the end to end time of the frame, 0 => not taken into account
 */
int set_end_to_end(Frame *pt, long long int end_to_end) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (end_to_end < 0) {
        fprintf(stderr, "The end to end time of the frame should be a natural number\n");
        return -1;
    }
    if (end_to_end >= pt->deadline) {
        fprintf(stderr, "The end to end time of the frame cannot be larger than the deadline\n");
        return -1;
    }
    
    pt->end_to_end_delay = end_to_end;
    return 0;
}

/**
 Set a path given a receiver id
 */
int set_path_receiver_id(Frame *pt, int receiver_id, int *path, int len) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (len <= 0) {
        fprintf(stderr, "The given length of the path should be positive\n");
        return -1;
    }
    if (path == NULL) {
        fprintf(stderr, "The given path is NULL\n");
        return -1;
    }
    int i = 0;
    // Search for the receiver id
    while (pt->receivers_id[i] != receiver_id && i < pt->num_paths) {
        i += 1;
    }
    if (i == pt->num_paths) {
        fprintf(stderr, "The frame does not have the node %d as receiver\n", receiver_id);
        return -1;
    }
    
    //pt->list_paths[i] = malloc(sizeof(Path));
    pt->list_paths[i].length_path = len;
    pt->list_paths[i].path = malloc(sizeof(int) * len);
    for (int j = 0; j < len; j++) {
        pt->list_paths[i].path[j] = path[j];
    }
    return 0;
}

/**
 Set the time to transmit the offset
 */
int set_time_offset_it(Frame *pt, int offset_it, int time) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    if (offset_it < 0 || offset_it >= pt->num_offsets) {
        fprintf(stderr, "The given offset iterator number is out of the bounds\n");
        return -1;
    }
    
    pt->offset_it[offset_it]->time = time;
    return 0;
}

/* Functions */

/**
 Initialize all the offsets once the frame values and the paths are filled
 */
int init_offsets(Frame *pt, int max_link_id, long long int hyperperiod) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    
    // Init the offset hash depending in the number of max link ids
    pt->num_offsets = 0;
    pt->offset_it = NULL;
    pt->offset_hash = malloc(sizeof(Offset*) * max_link_id + 1);
    for (int i = 0; i <= max_link_id; i++) {
        pt->offset_hash[i] = NULL;
    }
    int instances = (int)(hyperperiod / pt->period);
    // For all paths in the network
    for (int i = 0; i < pt->num_paths; i++) {
        // For all the links in the path
        pt->list_paths[i].list_offsets = malloc(sizeof(Offset*) * pt->list_paths[i].length_path);
        for (int j = 0; j < pt->list_paths[i].length_path; j++) {
            
            // If the offset in the hash has not been initialized yet, init before assign it
            int link_id = pt->list_paths[i].path[j];
            if (pt->offset_hash[link_id] == NULL) {
                
                // Populate the offset
                pt->offset_hash[link_id] = malloc(sizeof(Offset));
                pt->offset_hash[link_id]->link_id = link_id;
                pt->offset_hash[link_id]->num_instances = instances;
                pt->offset_hash[link_id]->num_replicas = 1;     // We do not implement Wireless yet...
                pt->offset_hash[link_id]->time = -1;            // Will be defined later
                // Allocate also the transmission times matrix and set to undifined
                pt->offset_hash[link_id]->offset = malloc(sizeof(long long int*) *
                                                          pt->offset_hash[link_id]->num_instances);
                for (int inst = 0; inst < pt->offset_hash[link_id]->num_instances; inst++) {
                    pt->offset_hash[link_id]->offset[inst] = malloc(sizeof(long long int) *
                                                                    pt->offset_hash[link_id]->num_replicas);
                    for (int repl = 0; repl < pt->offset_hash[link_id]->num_replicas; repl++) {
                        pt->offset_hash[link_id]->offset[inst][repl] = -1;
                    }
                }
                
                // Add the offset to the offset iterator
                pt->num_offsets += 1;
                pt->offset_it = realloc(pt->offset_it, sizeof(Offset*) * pt->num_offsets);
                pt->offset_it[pt->num_offsets - 1] = pt->offset_hash[link_id];
                
            }
            pt->list_paths[i].list_offsets[j] = pt->offset_hash[link_id];
        }
        
    }
    
    return 0;
}

/**
 Initialize all the offsets for a reservation frame.
 This frame is special as only has filled the offset iterator for all the links, with already filled transmission
 times.
 The purpose of these kind of frames is to avoid other frames to be transmitted in the times the reservation is active.

 */
int init_offset_reservation(Frame *pt, int max_link_id, long long int hyperperiod) {
    
    if (pt == NULL) {
        fprintf(stderr, "The given pointer is NULL\n");
        return -1;
    }
    
    // Init the offset iterator depending in the number of max link ids
    pt->num_offsets = 0;
    pt->offset_hash = malloc(sizeof(Offset*) * max_link_id + 1);
    int instances = (int)(hyperperiod / pt->period);
    
    // For all possible links we create the offset, eventhough we might not needed
    for (int i = 0; i <= max_link_id; i++) {
        pt->offset_hash[i] = malloc(sizeof(Offset));
        pt->offset_hash[i]->link_id = i;
        pt->offset_hash[i]->num_instances = instances;
        pt->offset_hash[i]->num_replicas = 1;
        pt->offset_hash[i]->time = pt->size;
        
        // Allocate the transmission times and already set them as we know them
        pt->offset_hash[i]->offset = malloc(sizeof(long long int*) * instances);
        for (int inst = 0; inst < instances; inst++) {
            pt->offset_hash[i]->offset[inst] = malloc(sizeof(long long int));
            pt->offset_hash[i]->offset[inst][0] = pt->period * inst;
        }
        
        // Add the offset to the offset iterator
        pt->num_offsets += 1;
        pt->offset_it = realloc(pt->offset_it, sizeof(Offset*) * pt->num_offsets);
        pt->offset_it[pt->num_offsets - 1] = pt->offset_hash[i];
    }
    
    return 0;
}
