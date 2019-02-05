/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Frame.h                                                                                                            *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 29/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that contains the information of a single frame in the network.                                            *
 *  A frame should contain the information of period, deadline, size and the tree path it is following.                *
 *  It also contains the offset for every link. As it is meant to work with different solvers, it also contains its    *
 *  variables                                                                                                          *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#ifndef Frame_h
#define Frame_h

#include <stdio.h>
#include <stdlib.h>

#endif /* Frame_h */

                                                /* STRUCT DEFINITIONS */

typedef struct Offset {
    long long int **offset;             // Matrix with the transmission times in ns
    int num_instances;                  // Number of offset instances (hyperperiod / period frame)
    int num_replicas;                   // Number of offset replicas due to wireless (1 => no replication)
    int time;                           // Number of timeslots to transmit in the current link
    int link_id;                        // Link id of the current offset
}Offset;

/**
 Structure with the information of all the offsets in a path in order
 */
typedef struct Path {
    int length_path;                    // Length of the path in offsets
    int *path;                          // List of link ids that form the path
    Offset **list_offsets;              // List of pointers to all the offsets in the path
}Path;

/**
 Struct with the information of the frame.
 Every frame has a number of paths. We accelerate searching for offsets of the links by a hash of offsets.
 */
typedef struct Frame {
    int size;                           // Size of the frames in bytes
    long long int period;               // Period of the frame in ns
    long long int deadline;             // Deadline of the frame in ns
    long long int end_to_end_delay;     // Maximum end to end delay from a frame being sent to being received in ns
    long long int starting;             // Starting time of the frame in ns
    int num_paths;                      // Number of paths in the frame
    int sender_id;                      // Sender ID of the frame
    int *receivers_id;                  // Receivers ID for every of the paths
    Path *list_paths;                   // List paths structures in the frame
    Offset **offset_hash;               // List that stores the offsets pointers with index the link identifier
                                        // to accelerate (we have double reference because we want to have NULL!)
    int num_offsets;                    // Number of offsets needed to iterate over the offset iteration
    Offset **offset_it;                 // List that stores pointers to the Offset so we can iterate over faster
}Frame;

                                                /* CODE DEFINITIONS */

/* Getters */

/**
 Get the sender id

 @param pt pointer to the frame
 @return sender id
 */
int get_sender_id(Frame *pt);

/**
 Get the receiver id
 
 @param pt pointer to the frame
 @param num number of the receiver
 @return receiver id
 */
int get_receiver_id(Frame *pt, int num);

/**
 Get the period of the frame in nanoseconds

 @param pt pointer to the frame
 @return period of the frame in nanoseconds
 */
long long int get_period(Frame *pt);

/**
 Get the deadline of the frame in nanoseconds
 
 @param pt pointer to the frame
 @return deadline of the frame in nanoseconds
 */
long long int get_deadline(Frame *pt);

/**
 Get the size of the frame

 @param pt pointer to the frame
 @return size of the frame in Bytes
 */
int get_size(Frame *pt);

/**
 Get the starting time of the frame

 @param pt pointer to the frame
 @return starting time of the frame in nanoseconds
 */
long long int get_starting_time(Frame *pt);

/**
 Get the end to end time of the frame

 @param pt pointer to the frame
 @return end to end time of the frame in nanoseconds
 */
long long int get_end_to_end(Frame *pt);

/**
 Get the number of different offsets of the frame

 @param pt pointer to the frame
 @return number of different offsets of the frame, -1 if something was wrong
 */
int get_num_offsets(Frame *pt);

/**
 Get the link id of the frame by the offset iteration

 @param pt pointer to the frame
 @param offset_it position in the offset iteration
 @return link id, -1 if something was wrong
 */
int get_link_id_offset(Frame *pt, int offset_it);

/* Setters */

/**
 Set the sender id

 @param pt pointer to the frame
 @param sender_id given sender id
 @return 0 if done correctly, -1 otherwise
 */
int set_sender_id(Frame *pt, int sender_id);

/**
 Set the receiver id
 
 @param pt pointer to the frame
 @param num number of the receiver
 @param receiver_id given receiver id
 @return 0 if done correctly, -1 otherwise
 */
int set_receiver_id(Frame *pt, int num, int receiver_id);

/**
 Set the period of the frame

 @param pt pointer to the frame
 @param period period of the frame in nanoseconds
 @return 0 if done correctly, -1 otherwise
 */
int set_period(Frame *pt, long long int period);

/**
 Set the deadline of the frame
 
 @param pt pointer to the frame
 @param deadline deadline of the frame in nanoseconds
 @return 0 if done correctly, -1 otherwise
 */
int set_deadline(Frame *pt, long long int deadline);

/**
 Set the size of the frame

 @param pt pointer to the frame
 @param size size of the frame in Bytes
 @return 0 if done correctly, -1 otherwise
 */
int set_size(Frame *pt, int size);

/**
 Set the starting time of the frame

 @param pt pointer to the frame
 @param starting_time starting time of the frame in nanoseconds
 @return 0 if done correctly, -1 otherwise
 */
int set_starting_time(Frame *pt, long long int starting_time);

/**
 Set the end to end time of the frame, 0 => not taken into account

 @param pt pointer to the frame
 @param end_to_end end to end time of the frame in nanoseconds
 @return 0 if done correctly, -1 otherwise
 */
int set_end_to_end(Frame *pt, long long int end_to_end);

/**
 Set a path given a receiver id

 @param pt pointer to the frame
 @param receiver_id node receiver id
 @param path list with the link ids of the path
 @param len length of the path
 @return 0 if done correctly, -1 otherwise
 */
int set_path_receiver_id(Frame *pt, int receiver_id, int *path, int len);

/**
 Set the time to transmit the offset

 @param pt pointer to the frame
 @param offset_it offset it number
 @param time time to transmit the offset
 @return 0 if done correctly, -1 otherwise
 */
int set_time_offset_it(Frame *pt, int offset_it, int time);

/* Functions */

/**
 Initialize all the offsets once the frame values and the paths are filled

 @param pt pointer to the frame
 @param max_link_id maximum link id needed to init the offset hash
 @param hyperperiod hyperperiod of the schedule needed to calculate the frame number of instances
 @return 0 if done correctly, -1 otherwise
 */
int init_offsets(Frame *pt, int max_link_id, long long int hyperperiod);

/**
 Initialize all the offsets for a reservation frame.
 This frame is special as only has filled the offset iterator for all the links, with already filled transmission
 times.
 The purpose of these kind of frames is to avoid other frames to be transmitted in the times the reservation is active.

 @param pt pointer to the reservation frame
 @param max_link_id maximum link id needed to init the offset hash
 @param hyperperiod of the schedule needed to calculate the frame number of instances
 @return 0 if done correctly, -1 otherwise
 */
int init_offset_reservation(Frame *pt, int max_link_id, long long int hyperperiod);
