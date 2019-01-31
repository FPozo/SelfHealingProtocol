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
    
    pt->list_paths[i] = malloc(sizeof(Path));
    pt->list_paths[i]->length_path = len;
    pt->list_paths[i]->path = malloc(sizeof(int) * len);
    for (int j = 0; j < len; j++) {
        pt->list_paths[i]->path[j] = path[j];
    }
    return 0;
}
