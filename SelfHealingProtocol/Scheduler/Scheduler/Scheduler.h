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

                                                /* AUXILIAR FUNCTIONS */

                                                /* CODE DEFINITIONS */

/**
 Schedule all the transmission times of all the frames at the same time given the given scheduling parameters

 @param schedule_params xml file with the scheduling parameters
 @return 0 if the schedule was found, -1 otherwise
 */
int one_shot_scheduling(char *schedule_params);
