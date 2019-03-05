/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Scheduler.h                                                                                                        *
 *  Self-Healing Protocol                                                                                              *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 07/02/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package that contains the information, creates the constraints and algorithms to synthesize the Schedule.          *
 *  The main approaches used are one-shot and incremental.                                                             *
 *  Every technique has a different performance. The better performance, the worse "quality".                          *
 *  Also numerous optimizations can be applied to different techniques to try to modify the "quality" of the schedules *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#ifndef Scheduler_h
#define Scheduler_h

#include <stdio.h>
#include <gurobi_c.h>

#endif /* Scheduler_h */

                                                /* STRUCT DEFINITIONS */

typedef enum Scheduler{
    one_shot,
    incremental
}Scheduler;

/**
 Sorted linked list transmission block
 */
typedef struct LS_Transmission{
    long long int starting;
    long long int ending;
    struct LS_Transmission *next_transmission;
}LS_Transmission;

                                                /* AUXILIAR FUNCTIONS */

                                                /* CODE DEFINITIONS */

/**
 Schedule all the transmission times of all the frames at the same time given the given scheduling parameters

 @return 0 if the schedule was found, -1 otherwise
 */
int one_shot_scheduling(void);

/**
 Schedule all the tranmission times of all the frames iteratively.
 The number of frames per each iteration and the timing limit is given in the scheduling paramenters file

 @return 0 if the schedule was found, -1 otherwise
 */
int incremental_approach(void);

/**
 Schedule the network given the parameters read before

 @return 0 if the schedule was found, -1 otherwise
 */
int schedule_network(void);

/**
 Patch the traffic in a fast heuristic

 @return 0 if patch was found, -1 otherwise
 */
int patch(void);

/**
 Read the scheduler parameters

 @param parameters_xml name and path of the parameter xml file
 @return 0 if done correctly, -1 otherwise
 */
int read_schedule_parameters_xml(char *parameters_xml);
