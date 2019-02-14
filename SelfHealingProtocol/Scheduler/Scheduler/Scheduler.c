/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Scheduler.c                                                                                                        *
 *  Self-Healing Protocol                                                                                              *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 07/02/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Description in Scheduler.h                                                                                         *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include "Scheduler.h"
#include "Network.h"

                                                    /* VARIABLES */

GRBenv *env = NULL;                 // Gurobi solver environment
GRBmodel *model = NULL;             // Gurobi model
int var_it = 0;                     // Iterator to remember the value to position variables in gurobi
int *frame_dis;                     // Indexes for the gurobi variables for the frame distances
int *link_dis;                      // Indexes for the gurobi variables for the link distances
double frame_dis_w = 0.9;           // Weight for the frame distances
double link_dis_w = 0.1;            // Link for the link distances
long long int path_con = 0;         // Counter of path dependent constraints
long long int end_con = 0;          // Counter of end to end constraints
long long int avoid_con = 0;        // Counter of avoid collission constraints
long long int x_con = 0;            // Counter of x bin variables
long long int y_con = 0;            // Counter of y bin variables
long long int z_con = 0;            // Counter of z bin variables
long long int or_con = 0;           // Counter of z = x or y variables

                                                    /* FUNCTIONS */

/* Auxiliar Functions */

/**
 Init the solver and prepare it to add constraints

 @return 0 if done correctly, -1 otherwise
 */
int init_solver(void) {
    
    int error = GRBloadenv(&env, NULL);
    if (error || env == NULL) {
        fprintf(stderr, "The gurobi solver could not be initialized\n");
        return -1;
    }
    error = GRBnewmodel(env, &model, "schedule", 0, NULL, NULL, NULL, NULL, NULL);
    if (error) {
        fprintf(stderr, "The gurobi solver could not create the model\n");
        return -1;
    }
    // Set as maximizing
    GRBsetintattr(model, GRB_INT_ATTR_MODELSENSE, -1);
    
    return 0;
}

/**
 Free the memory of the solver

 @return 0 if done correctly, -1 otherwise
 */
int close_solver(void) {
    
    GRBfreemodel(model);
    GRBfreeenv(env);
    
    return 0;
}

/**
 Init the offsets of all the frames and limit them to their starting time and their deadline

 @param frames list of frames to init
 @param num numbr of frames to init
 @return 0 if done correctly, -1 otherwise
 */
int create_offsets_variables(Frame *frames, int num) {
    
    char name[100];
    
    // Add all the variables for all transmission times of all frames
    for (int i = 0; i < num; i++) {
        int frame_id = get_frame_id(i);
        for (int j = 0; j < get_num_offsets(&frames[i]); j++) {
            Offset *off = get_offset_it(&frames[i], j);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                    
                    sprintf(name, "Off_%d_%d_%d_%d", frame_id, get_link_id_offset_it(&frames[i], j), inst, repl);
                    
                    // Lower bound = starting time + (period * instance) + (replica * time transmission)
                    long long int lb = get_starting_time(&frames[i]) + (inst * get_period(&frames[i])) +
                                       (repl * get_off_time(off));
                    // Upper bound = deadline - time transmission + (period * instance) - (replica * time transmission)
                    long long int ub = get_deadline(&frames[i]) - get_off_time(off) + (get_period(&frames[i]) * inst) -
                                       (repl * get_off_time(off));
                    
                    if (GRBaddvar(model, 0, NULL, NULL, 0, lb, ub, GRB_INTEGER, name)) {
                        printf("%s\n", GRBgeterrormsg(env));
                        return -1;
                    }
                    set_var_name(off, inst, repl, var_it);
                    var_it += 1;
                }
            }
        }
    }
    
    // Add all the variables for the self-healing protocol if it exists
    SelfHealing_Protocol *shp = get_healing_protocol();
    if (shp->period != 0) {
        for (int i = 0; i < get_num_offsets(&shp->reservation); i++) {
            Offset *off = get_offset_it(&shp->reservation, i);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                sprintf(name, "SHP_%d_%d", get_link_id_offset_it(&shp->reservation, i), inst);
                
                long long int value = inst * get_period(&shp->reservation);
                
                if (GRBaddvar(model, 0, NULL, NULL, 0, value, value, GRB_INTEGER, name)) {
                    printf("%s\n", GRBgeterrormsg(env));
                    return -1;
                }
                set_var_name(off, inst, 0, var_it);
                set_trans_time(off, inst, 0, value);
                var_it += 1;
            }
        }
    }
    GRBupdatemodel(model);
    
    return 0;
}

/**
 Init the variables that maximize the distances between transmission of frames and links

 @param frames list of frames to create the contraint
 @param num number of frames in the list
 @return 0 if done correctly, -1 otherwise
 */
int create_intermission_variables(Frame *frames, int num) {
    
    char name[100];
    // Allocate to save the frame and link distances variables
    frame_dis = malloc(sizeof(int) * num);
    link_dis = malloc(sizeof(int) * (get_higher_link_id() + 1));
    
    // Create all the frame intermissions
    for (int i = 0; i < num; i++) {
        sprintf(name, "FrameDis_%d", get_frame_id(i));
        
        if (GRBaddvar(model, 0, NULL, NULL, frame_dis_w, 0, get_end_to_end(&frames[i]), GRB_INTEGER, name)) {
            printf("%s\n", GRBgeterrormsg(env));
            return -1;
        }
        frame_dis[i] = var_it;
        var_it += 1;
    }
    
    // Create all the link intermissions
    for (int i = 0; i <= get_higher_link_id(); i++) {
        sprintf(name, "LinkDis_%d", i);
        if (GRBaddvar(model, 0, NULL, NULL, link_dis_w, 0, get_hyperperiod(), GRB_INTEGER, name)) {
            printf("%s\n", GRBgeterrormsg(env));
            return -1;
        }
        link_dis[i] = var_it;
        var_it += 1;
    }
    
    return 0;
}

/**
 Assures that all the frames follow their path and stay at least the minimum switch time

 @param frames list of frames to create the contraint
 @param num number of frames in the list
 @return 0 if done correctly, -1 otherwise
 */
int path_dependent(Frame *frames, int num) {
    
    char name[100];
    // For all frames, for every different path, iterate over all the links
    for (int i = 0; i < num; i++) {
        for (int j = 0; j < get_num_paths(&frames[i]); j++) {
            
            Path *path_pt = get_path(&frames[i], j);
            for (int h = 0; h < (get_num_links_path(path_pt) - 1); h++) {
                Offset *off_pt = get_offset_path_link(path_pt, h);
                Offset *next_off_pt = get_offset_path_link(path_pt, h + 1);
                for (int inst = 0; inst < get_off_num_instances(off_pt); inst ++) {
                    
                    // OFFSET + MIN TIME SWITCH + TRANSMISSION TIME + FRAME INTER <= NEXT OFFSET
                    long long int distance = get_off_time(off_pt) + get_switch_min_time();
                    int var_off[] = {get_var_name(off_pt, inst, 0), get_var_name(next_off_pt, inst, 0), frame_dis[i]};
                    double val[] = {-1, 1, -1};
                    
                    sprintf(name, "PathDep_%lld", path_con);
                    path_con += 1;
                    if (GRBaddconstr(model, 3, var_off, val, GRB_GREATER_EQUAL, distance, name)) {
                        printf("%s\n", GRBgeterrormsg(env));
                        return -1;
                    }
                }
            }
        }
    }
    GRBupdatemodel(model);
    
    return 0;
}

/**
 Assures that the time between the start of the transmission and the end is bounded by a delay

 @param frames list of frames to create the constraint
 @param num number of frames in the list
 @return 0 if done correctly, -1 otherwise
 */
int end_to_end_delay(Frame *frames, int num) {
    
    char name[100];
    // For all xrames, for all paths, add the constraint between the first and last link on the path
    for (int i = 0; i < num; i++) {
        for (int j = 0; j < get_num_paths(&frames[i]); j++) {
            Path *path_pt = get_path(&frames[i], j);
            Offset *first_off_pt = get_offset_path_link(path_pt, 0);
            Offset *last_off_pt = get_offset_path_link(path_pt, get_num_links_path(path_pt) - 1);
            for (int inst = 0; inst < get_off_num_instances(first_off_pt); inst ++) {
                
                // FIRST OFFSET + END TO END DELAY - TRANSMISSION TIME >= LAST OFFSET
                long long int distance = get_end_to_end(&frames[i]) - get_off_time(first_off_pt);
                int var_off[] = {get_var_name(first_off_pt, inst, 0), get_var_name(last_off_pt, inst, 0)};
                double val[] = {-1, 1};
                
                sprintf(name, "End_%lld_1", end_con);
                if (GRBaddconstr(model, 2, var_off, val, GRB_LESS_EQUAL, distance, name)) {
                    printf("%s\n", GRBgeterrormsg(env));
                    return -1;
                }
                
                // Also add the frame intermission for the first and last offset to the starting point and deadline
                // FIRST OFFSET >= FRAME DISTANCE + STARTING TIME
                distance = get_starting_time(&frames[i]) + (get_period(&frames[i]) * inst);
                var_off[1] = frame_dis[i];
                val[0] = 1; val[1] = -1;
                
                sprintf(name, "End_%lld_2", end_con);
                if (GRBaddconstr(model, 2, var_off, val, GRB_GREATER_EQUAL, distance, name)) {
                    printf("%s\n", GRBgeterrormsg(env));
                    return -1;
                }
                
                // LAST OFFSET + FRAME DISTANCE <= DEADLINE
                distance = get_deadline(&frames[i]) + (get_period(&frames[i]) * inst) - get_off_time(last_off_pt);
                var_off[0] = get_var_name(last_off_pt, inst, 0);
                val[1] = 1;
                
                sprintf(name, "End_%lld_3", end_con);
                end_con += 1;
                if (GRBaddconstr(model, 2, var_off, val, GRB_LESS_EQUAL, distance, name)) {
                    printf("%s\n", GRBgeterrormsg(env));
                    return -1;
                }
                
            }
        }
    }
    return 0;
}

/**
 Avoid that any frame transmission collides at the same time at the same link

 @param frames list of frames to create the constraint
 @param num number of frames in the list
 @return 0 if done correctly, -1 otherwise
 */
int contention_free(Frame *frames, int num) {
    
    char name[100];
    // For all frames, for all its offsets, if the offsets can collide, add constraint to avoid it
    for (int fr_it = 0; fr_it < num; fr_it++) {
        for (int i = 0; i < get_num_offsets(&frames[fr_it]); i++) {
            Offset *off = get_offset_it(&frames[fr_it], i);
            int link_id = get_link_id_offset_it(&frames[fr_it], i);
            int link_inter = link_dis[link_id];
            
            // For all the frames that were added before, check if the offsets ids are the same to add the constraint
            // Also avoid collision with the bandwith reservation if needed
            int pre_fr_it = 0;
            int checked_prot = 0;       // 1 if we already checked the protocol, 0 otherwise
            SelfHealing_Protocol protocol = *get_healing_protocol();
            if (protocol.period == 0) {
                checked_prot = 1;
            }
            while (pre_fr_it < fr_it || checked_prot == 0) {
                
                // Get the previous frame pointer, or the bandwitdh allocation frame
                Frame *pre_frame_pt = NULL;
                if (checked_prot == 0) {
                    pre_frame_pt = &protocol.reservation;
                } else {
                    pre_frame_pt = &frames[pre_fr_it];
                }
                
                Offset *pre_off = get_offset_by_link(pre_frame_pt, link_id);
                // If the frame has an offset with the same link, continue
                if (pre_off != NULL) {
                    for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                        for (int pre_inst = 0; pre_inst < get_off_num_instances(pre_off); pre_inst++) {
                            
                            // Check if both offsets share an interval and we need to add the constraint
                            long long int min1 = (get_period(&frames[fr_it]) * inst) +
                                                 (get_starting_time(&frames[fr_it]) + 1);
                            long long int max1 = (get_period(&frames[fr_it]) * inst) +
                                                 (get_deadline(&frames[fr_it]) + 1);
                            long long int min2 = (get_period(pre_frame_pt) * pre_inst) +
                                                 (get_starting_time(pre_frame_pt) + 1);
                            long long int max2 = (get_period(pre_frame_pt) * pre_inst) +
                                                 (get_deadline(pre_frame_pt) + 1);
                            if ((min1 <= min2 && min2 < max1) || (min2 <= min1 && min1 < max2)) {
                                
                                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                                    for (int pre_repl = 0; pre_repl < get_off_num_replicas(pre_off); pre_repl++) {
                                        
                                        long long int distance1 = get_off_time(off);
                                        long long int distance2 = get_off_time(pre_off);
                                        
                                        sprintf(name, "x_%lld", x_con);
                                        x_con += 1;
                                        // Add two binary variables to chosse between two constraints
                                        if (GRBaddvar(model, 0, NULL, NULL, 0, 0, 1, GRB_BINARY, name)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        sprintf(name, "y_%lld", y_con);
                                        y_con += 1;
                                        if (GRBaddvar(model, 0, NULL, NULL, 0, 0, 1, GRB_BINARY, name)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        sprintf(name, "z_%lld", z_con);
                                        z_con += 1;
                                        var_it += 2;
                                        // Add binary variable to force one of both previous variables to true
                                        if (GRBaddvar(model, 0, NULL, NULL, 0, 1, 1, GRB_BINARY, name)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        var_it += 1;
                                        int ind[] = {var_it -3, var_it -2};
                                        sprintf(name, "or_%lld", or_con);
                                        or_con += 1;
                                        if (GRBaddgenconstrOr(model, name, var_it - 1, 2, ind)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        
                                        // Depending of the active variable, we choose one or the other constraint
                                        // Offset + distance1 + link_dis <= previous offset
                                        int var[] = {get_var_name(off, inst, repl),
                                                     get_var_name(pre_off, pre_inst, pre_repl),
                                                     link_inter};
                                        double val[] = {-1.0, 1.0, -1.0};
                                        sprintf(name, "Avoid_%lld_1", avoid_con);
                                        if (GRBaddgenconstrIndicator(model, name, var_it - 3, 1, 3, var, val,
                                                                     GRB_GREATER_EQUAL, distance1)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        // Previous offset + distance2 + link_dis <= offset
                                        double val2[] = {1.0, -1.0, -1.0};
                                        sprintf(name, "Avoid_%lld_2", avoid_con);
                                        avoid_con += 1;
                                        if (GRBaddgenconstrIndicator(model, name, var_it - 2, 1, 3, var, val2,
                                                                     GRB_GREATER_EQUAL, distance2)) {
                                            printf("%s\n", GRBgeterrormsg(env));
                                            return -1;
                                        }
                                        
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Update if we compared with the bandwidth reservation, or check the next frame
                if (checked_prot == 0) {
                    checked_prot = 1;
                } else {
                    pre_fr_it += 1;
                }
            }
        }
    }
    GRBupdatemodel(model);
    return 0;
}

/**
 Save the obtained transmission times from the solver in the frames, also if needed, fix them into the solver

 @param frames list of frames to create the constraint
 @param num number of frames in the list
 @return 0 if done correctly, -1 otherwise
 */
int save_offsets(Frame *frames, int num) {
    
    // Iterate over all the given frames and their given offsets
    for (int i = 0; i < num; i++) {
        for (int j = 0; j < get_num_offsets(&frames[i]); j++) {
            Offset *off = get_offset_it(&frames[i], j);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                    // Get the transmission time from the model and write it in the offset memory
                    double trans_time;
                    if (GRBgetdblattrelement(model, GRB_DBL_ATTR_X, get_var_name(off, inst, repl), &trans_time)) {
                        printf("%s\n", GRBgeterrormsg(env));
                        return -1;
                    }
                    set_trans_time(off, inst, repl, (long long int) trans_time);
                }
            }
        }
    }
    GRBupdatemodel(model);
    return 0;
}

/**
 Check if the schedule obtained violates any of the constraints.
 It is useful in the case of more complex algorithms that obtain the schedule in steps and a bug might slip

 @param frames list of frames to create the constraint
 @param num number of frames in the list
 @return 0 if the schedule is correct, -1 if any constraint is violated
 */
int check_schedule(Frame *frames, int num) {
    
    SelfHealing_Protocol *protocol = get_healing_protocol();
    
    // Iterate over all the frames to check their constriants
    for (int i = 0; i < num; i++) {
        
        // Check if the transmission times are between their limits
        for (int j = 0; j < get_num_offsets(&frames[i]); j++) {
            Offset *off = get_offset_it(&frames[i], j);
            int link_id = get_link_id_offset_it(&frames[i], j);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                    
                    long long int trans_time = get_trans_time(off, inst, repl);
                    long long int lb = (get_period(&frames[i]) * inst) + get_starting_time(&frames[i]);
                    long long int ub = (get_period(&frames[i]) * inst) + get_deadline(&frames[i]) - get_off_time(off);
                    if (trans_time < lb) {
                        fprintf(stderr, "The transmission time of frame %d link %d is smaller than should be\n",
                                get_frame_id(i), get_link_id_offset_it(&frames[i], j));
                        return -1;
                    }
                    if (trans_time > ub) {
                        fprintf(stderr, "The transmission time of frame %d link %d is larger than should be\n",
                                get_frame_id(i), get_link_id_offset_it(&frames[i], j));
                        return -1;
                    }
                }
            }
            
            // Also check if the frame collides with the bandwidth allocation protocol
            if (protocol->period != 0) {
                for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                    for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                        
                        long long int trans_time = get_trans_time(off, inst, repl);
                        long long int end_time = get_off_time(off) + get_off_time(off);
                        Offset *prot_off = get_offset_by_link(&protocol->reservation, link_id);
                        for (int prot_inst = 0; prot_inst < get_off_num_instances(prot_off); prot_inst++) {
                            
                            long long int prot_trans_time = get_trans_time(prot_off, prot_inst, 0);
                            long long int end_time2 = prot_trans_time + get_off_time(prot_off);
                            
                            
                            if ((prot_trans_time < end_time) && (trans_time < end_time2)) {
                                fprintf(stderr, "The frame %d collides with the protocol in link %d\n",
                                        get_frame_id(i), link_id);
                                return -1;
                            }
                            
                        }
                        
                    }
                }
            }
            
            // Check if the transmissions in the same link of different frames collide
            for (int pre_fr_it = 0; pre_fr_it < i; pre_fr_it++) {

                Offset *pre_off = get_offset_by_link(&frames[pre_fr_it], link_id);
                // If the frame has an offset with the same link, continue
                if (pre_off != NULL) {
                    
                    
                    for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                        for (int pre_inst = 0; pre_inst < get_off_num_instances(pre_off); pre_inst++) {
                            for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                                for (int pre_repl = 0; pre_repl < get_off_num_replicas(pre_off); pre_repl++) {
                                    
                                    long long int trans_time = get_trans_time(off, inst, repl);
                                    long long int pre_trans_time = get_trans_time(pre_off, pre_inst, pre_repl);
                                    long long int end_time = trans_time + get_off_time(off);
                                    long long int end_time2 = pre_trans_time + get_off_time(pre_off);
                                    
                                    if ((pre_trans_time < end_time) && (trans_time < end_time2)) {
                                        fprintf(stderr, "The frames %d and %d collide in link %d\n",
                                                get_frame_id(i), get_frame_id(pre_fr_it), link_id);
                                        return -1;
                                    }
                                    
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Check if the paths are correctly followed and the end to end delay is satisfied
        for (int j = 0; j < get_num_paths(&frames[i]); j++) {
            Path *path_pt = get_path(&frames[i], j);
            for (int h = 0; h < get_num_links_path(path_pt) - 1; h++) {
                Offset *off = get_offset_path_link(path_pt, h);
                Offset *next_off = get_offset_path_link(path_pt, h + 1);
                for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                    for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                        
                        long long int distance = get_off_time(off) + get_switch_min_time();
                        long long int trans_time = get_trans_time(off, inst, repl);
                        long long int next_trans_time = get_trans_time(next_off, inst, repl);
                        if ((next_trans_time - trans_time) < distance) {
                            fprintf(stderr, "The distances of the path of frame %d is wrong\n", get_frame_id(i));
                            return -1;
                        }
                        
                    }
                }
            }
            // Check the first and last liks in the path for the end to end delay constraint
            Offset *off = get_offset_path_link(path_pt, 0);
            Offset *last_off = get_offset_path_link(path_pt, get_num_links_path(path_pt) - 1);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                    
                    long long int distance = get_end_to_end(&frames[i]) - get_off_time(off);
                    long long int trans_time = get_trans_time(off, inst, repl);
                    long long int last_trans_time = get_trans_time(last_off, inst, repl);
                    if ((last_trans_time - trans_time) > distance) {
                        fprintf(stderr, "The end to end delay of frame %d is wrong\n", get_frame_id(i));
                        return -1;
                    }
                    
                }
            }
        }
    }
    
    return 0;
}

/* Functions */

/**
 Schedule all the transmission times of all the frames at the same time given the given scheduling parameters.
 It first init the solver and the variables for all the offsets transmission times between their deadlines.
 Then avoid that any offset collides.
 Forces that all frames has to wait at least a minimum switch time
 There exist a limit between the time the transmission starts and the time all the receivers get the frame
 If the protocol bandwitch is activated, avoid frames to the transmitted at the reserver bandwidth
 There might optimization, such as minimize the timespan, of increase the reparability
 */
int one_shot_scheduling(char *schedule_params) {
    
    init_solver();
    Traffic *t = get_traffic();
    
    // Allocate the memory for the link intermissions
    
    
    if (create_offsets_variables(t->frames, t->num_frames) == -1) {
        fprintf(stderr, "Failure creating offsets\n");
        return -1;
    }
    
    if (create_intermission_variables(t->frames, t->num_frames) == -1) {
        fprintf(stderr, "Failure creating intermission variables\n");
        return -1;
    }

    if (path_dependent(t->frames, t->num_frames) == -1) {
        fprintf(stderr, "Failure adding path dependent constraints\n");
        return -1;
    }

    if (end_to_end_delay(t->frames, t->num_frames) == -1) {
        fprintf(stderr, "Failure adding end to end delay constraints\n");
        return -1;
    }

    if (contention_free(t->frames, t->num_frames) == -1) {
        fprintf(stderr, "Failure adding contention free constraints\n");
        return -1;
    }
    
    GRBoptimize(model);
    
    // For testing purposes print the model
    GRBwrite(model, "/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/model.lp");
    
    int solcount;
    GRBgetintattr(model, GRB_INT_ATTR_SOLCOUNT, &solcount);
    if (solcount == 0) {
        fprintf(stderr, "No schedule found\n");
        return -1;
    }
    
    // For testing purposes print the solution
    GRBwrite(model, "/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/model.sol");
    
    // Save the obtained model into internal memory and check if the solver is correct (does not violate constraints)
    save_offsets(t->frames, t->num_frames);
    if (check_schedule(t->frames, t->num_frames) != 0) {
        fprintf(stderr, "The obtained schedule violates some of the given constraints\n");
        return -1;
    }
    
    close_solver();
    return 0;
}
