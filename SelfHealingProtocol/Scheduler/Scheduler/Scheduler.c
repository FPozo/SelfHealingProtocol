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
int *frame_dis = NULL;              // Indexes for the gurobi variables for the frame distances
int *link_dis = NULL;               // Indexes for the gurobi variables for the link distances
double frame_dis_w = 0.9;           // Weight for the frame distances
double link_dis_w = 0.1;            // Link for the link distances
long long int path_con = 0;         // Counter of path dependent constraints
long long int end_con = 0;          // Counter of end to end constraints
long long int avoid_con = 0;        // Counter of avoid collission constraints
long long int x_con = 0;            // Counter of x bin variables
long long int y_con = 0;            // Counter of y bin variables
long long int z_con = 0;            // Counter of z bin variables
long long int or_con = 0;           // Counter of z = x or y variables
long long int fix_con = 0;          // Counter of fixed variables
int frames_it = 1;                  // Frames solved at each iteration of the incremental approach
Scheduler algorithm;                // Algorithm used to schedule the network
double MIPGAP = 0.0;                // MIP GAP limit when to stop searching
double timelimit = 100;             // Time limit when to stop executing the solver (in the case of the incremetal
                                    // it is the time limit PER ITERATION)
LS_Transmission *sorted_trans = NULL;        // Started point of the sorted linked list with the link transmissions
uint64_t execution_time = 0;        // Execution time of the patch or optimization algorithm
int *var_shp_optimize = NULL;       // Gurobi variables for the SHP reservation for the optimize


                                                    /* FUNCTIONS */

/* Auxiliar Functions */

/**
 Set the scheduler algorithm

 @param name string of the name of the algorithm
 @return 0 if done correctly, -1 otherwise
 */
int set_algorithm(char *name) {
    
    if (strcmp(name, "OneShot") == 0) {
        algorithm = one_shot;
    } else if (strcmp(name, "Incremental") == 0) {
        algorithm = incremental;
    } else {
        fprintf(stderr, "The given algorithm is not defined\n");
        return -1;
    }
    
    return 0;
}

/**
 Set the MIP GAP Limit of the solver

 @param value MIP GAP
 @return 0 if done correctly, -1 otherwise
 */
int set_MIPGAP(double value) {
    
    if (value < 0.0) {
        fprintf(stderr, "The MIPGAP should be equal or larger than 0.0\n");
        return -1;
    }
    
    MIPGAP = value;
    
    return 0;
}

/**
 Set the time limit of the solver
 
 @param value time limit
 @return 0 if done correctly, -1 otherwise
 */
int set_timelimit(double value) {
    
    if (value < 0.0) {
        fprintf(stderr, "The time limit should be equal or larger than 0.0\n");
        return -1;
    }
    
    timelimit = value;
    
    return 0;
}

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
    
    // Silence the output
    GRBsetintparam(env, GRB_INT_PAR_OUTPUTFLAG, 0);
    
    // Set the MIPGAP
    GRBsetdblparam(env, GRB_DBL_PAR_MIPGAP, MIPGAP);
    // Set the time limit
    GRBsetdblparam(env, GRB_DBL_PAR_TIMELIMIT, timelimit);
    
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
 @param num number of frames to init
 @param accum_num number of frames that were already created their offsets
 @param do_protocol if 1, add also the Self-Healing Protocol variables
 @return 0 if done correctly, -1 otherwise
 */
int create_offsets_variables(Frame *frames, int num, int accum_num, int do_protocol) {
    
    char name[100];
    
    // Add all the variables for all transmission times of all frames
    for (int i = accum_num; (i - accum_num) < num; i++) {
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
    if (shp->period != 0 && do_protocol == 1) {
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
 @param accum_num number of frames that were already created their offsets
 @param it iteration for creating the link intermission differently for each iteration
 @return 0 if done correctly, -1 otherwise
 */
int create_intermission_variables(Frame *frames, int num, int accum_num, int it) {
    
    char name[100];
    
    // If link distances were init, remove the obj from them
    if (link_dis != NULL) {
        for (int i = 0; i <= get_higher_link_id(); i++) {
            GRBsetdblattrelement(model, GRB_DBL_ATTR_OBJ, link_dis[i], 0.0);
        }
    }
    
    // Allocate to save the frame and link distances variables
    frame_dis = realloc(frame_dis, sizeof(int) * (accum_num + num));
    link_dis = malloc(sizeof(int) * (get_higher_link_id() + 1));
    
    // Create all the frame intermissions
    for (int i = accum_num; (i - accum_num) < num; i++) {
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
        sprintf(name, "LinkDis_%d_%d", it, i);
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
 @param accum_num number of frames that were already created their offsets
 @return 0 if done correctly, -1 otherwise
 */
int path_dependent(Frame *frames, int num, int accum_num) {
    
    char name[100];
    // For all frames, for every different path, iterate over all the links
    for (int i = accum_num; (i - accum_num) < num; i++) {
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
 @param accum_num number of frames that were already created their offsets
 @return 0 if done correctly, -1 otherwise
 */
int end_to_end_delay(Frame *frames, int num, int accum_num) {
    
    char name[100];
    // For all xrames, for all paths, add the constraint between the first and last link on the path
    for (int i = accum_num; (i - accum_num) < num; i++) {
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
 @param accum_num number of frames that were already created their offsets
 @return 0 if done correctly, -1 otherwise
 */
int contention_free(Frame *frames, int num, int accum_num) {
    
    char name[100];
    // For all frames, for all its offsets, if the offsets can collide, add constraint to avoid it
    for (int fr_it = accum_num; (fr_it - accum_num) < num; fr_it++) {
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
 @param accum_num number of frames that were already created their offsets
 @return 0 if done correctly, -1 otherwise
 */
int save_offsets(Frame *frames, int num, int accum_num) {
    
    char name[100];
    
    // Iterate over all the given frames and their given offsets
    for (int i = accum_num; (i - accum_num) < num; i++) {
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
                    
                    // Fix the transmission time in the model
                    sprintf(name, "Fix_%lld", fix_con);
                    int ind[] = {get_var_name(off, inst, repl)};
                    double val[] = {1.0};
                    if (GRBaddconstr(model, 1, ind, val, GRB_EQUAL, trans_time, name)) {
                        printf("%s\n", GRBgeterrormsg(env));
                        return -1;
                    }
                    fix_con += 1;
                }
            }
        }
        // Remove the objective from the scheduled frame
        GRBsetdblattrelement(model, GRB_DBL_ATTR_OBJ, frame_dis[i], 0.0);
    }
    
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
                                    long long int end_time = trans_time + get_off_time(off) - 1;
                                    long long int end_time2 = pre_trans_time + get_off_time(pre_off) - 1;
                                    
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
            // Check the first and last links in the path for the end to end delay constraint
            Offset *off = get_offset_path_link(path_pt, 0);
            Offset *last_off = get_offset_path_link(path_pt, get_num_links_path(path_pt) - 1);
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int repl = 0; repl < get_off_num_replicas(off); repl++) {
                    
                    long long int distance = get_end_to_end(&frames[i]) - get_off_time(off) + 1;
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

/* Patch functions */

/**
 Insert a fixed transmission to the list of link transmissions

 @param head head to the link transmissions
 @param transmission_time starting time transmissions
 @param ending_time ending time transmission
 @return the new pointer to the head
 */
LS_Transmission* insert_fixed_trans(LS_Transmission *head, long long int transmission_time, long long int ending_time) {
    
    LS_Transmission *next_pt, *prev_pt;
    
    // Create the transmission block
    LS_Transmission *trans_pt = malloc(sizeof(LS_Transmission));
    trans_pt->starting = transmission_time;
    trans_pt->ending = ending_time;
    trans_pt->next_transmission = NULL;
    
    // If the head is not initialized, do it and add the block
    if (head == NULL) {
        head = trans_pt;
    } else {
        next_pt = head;
        prev_pt = NULL;
        // Search until the starting time is larger
        while (next_pt && next_pt->starting <= trans_pt->starting) {
            prev_pt = next_pt;
            next_pt = next_pt->next_transmission;
        }
        // If is the last, add it at the end
        if (next_pt == NULL) {
            prev_pt->next_transmission = trans_pt;
        // If not, it was in the middle, so add it in between
        } else {
            if (prev_pt) {
                trans_pt->next_transmission = prev_pt->next_transmission;
                prev_pt->next_transmission = trans_pt;
            } else {
                trans_pt->next_transmission = head;
                head = trans_pt;
            }
        }
    }
    return head;
}

/**
 Allocate a new offset in the linked list

 @param off_pt pointer to the offset to allocate
 @param instance number of instance
 @param head pointer to the head of the linked list transmission
 @param min minimum possible transmission time
 @param max maximum possible transmission time
 @param time_slots time slots
 @return the head pointer or null if the offset could not be patched
 */
LS_Transmission* allocate_offset_patch(Offset *off_pt, int instance, LS_Transmission *head, long long int min,
                                       long long int max, int time_slots) {
    
    LS_Transmission *next_pt, *prev_pt;
    int found = 0;
    
    // Create the transmission block
    LS_Transmission *trans_pt = malloc(sizeof(LS_Transmission));
    trans_pt->starting = min;
    trans_pt->ending = min + time_slots - 1;
    trans_pt->next_transmission = NULL;
    
    // If the head is not initialized, do it and add the block
    if (head == NULL) {
        head = trans_pt;
    } else {
        next_pt = head;
        prev_pt = NULL;
        // Iterate over all the linked list
        while (next_pt && found == 0) {
            
            // If it fits, add it
            if (trans_pt->ending < next_pt->starting) {
                found = 1;
            // If not, update the transmission times
            } else {
                // Update starting time only if is larger than the minimum available
                if (next_pt-> ending > min) {
                    trans_pt->starting = next_pt->ending + 1;
                    trans_pt->ending = trans_pt->starting + time_slots - 1;
                    // If it goes over the maximum, we could not patch
                    if (trans_pt->starting > max) {
                        free(trans_pt);
                        return NULL;
                    }
                }
                
                // Prepare pointers for the next iteration
                prev_pt = next_pt;
                next_pt = next_pt->next_transmission;
            }
        }
        
        // If is the last, add it at the end
        if (next_pt == NULL) {
            prev_pt->next_transmission = trans_pt;
            // If not, it was in the middle, so add it in between
        } else {
            if (prev_pt) {
                trans_pt->next_transmission = prev_pt->next_transmission;
                prev_pt->next_transmission = trans_pt;
            } else {
                trans_pt->next_transmission = head;
                head = trans_pt;
            }
        }
        // Allocate the transmission to the offset
        set_trans_time(off_pt, instance, 0, trans_pt->starting);
    }
    
    return head;
}

/**
 Prepare the fixed traffic and load it into the sorted list of the link transmissions

 @param frames pointer to the frames to fix
 @param num number of frames to fix
 @return 0 if done corretly, -1 otherwise
 */
int prepare_fixed_traffic(Frame *frames, int num) {
    
    // For all the fixed frames, add them into the linked list
    for (int fr_it = 0; fr_it < num; fr_it++) {
        // The fixed traffic only has one offset
        Offset *off_pt = get_offset_it(&frames[fr_it], 0);
        int time_slots = get_off_time(off_pt);
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            long long int trans_time = get_trans_time(off_pt, inst, 0);
            sorted_trans = insert_fixed_trans(sorted_trans, trans_time, trans_time + time_slots);
        }
    }
    
    // Also add the self healing protocol bandwith reservation
    SelfHealing_Protocol protocol = *get_healing_protocol();
    int instances_protocol = (int)(get_hyperperiod() / protocol.period);
    for (int i = 0; i < instances_protocol; i++) {
        int trans_time = (int)(protocol.period * i);
        sorted_trans = insert_fixed_trans(sorted_trans, trans_time, trans_time + protocol.time);
    }
    
    return 0;
}

/**
 Allocate the traffic in the available slots left by the dixed offsets
 
 @param frames pointer to the frames to allocate
 @param num number of frames to fix
 @return 0 if done corretly, -1 otherwise
 */
int allocate_patch_traffic(Frame *frames, int num) {
    
    for (int fr_it = 0; fr_it < num; fr_it++) {
        // The fixed traffic only has one offset
        Offset *off_pt = get_offset_it(&frames[fr_it], 0);
        int time_slots = get_off_time(off_pt);
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            long long int min = get_min_trans_time(off_pt, inst, 0);
            long long int max = get_max_trans_time(off_pt, inst, 0);
            sorted_trans = allocate_offset_patch(off_pt, inst, sorted_trans, min, max, time_slots);
            // If it returns null, we failed to patch
            if (sorted_trans == NULL) {
                fprintf(stderr, "A frame could not be patched\n");
                return -1;
            }
        }
    }
    
    return 0;
}

/**
 Add traffic with fixed transmission to the solver

 @param frames pointer to the frames to allocate
 @param num number of frames to fix
 @return 0 if done corretly, -1 otherwise
 */
int add_fixed_traffic(Frame *frames, int num) {
    
    char name[100];
    
    // For all the fixed frames, add them into the solver with a fixed range
    for (int fr_it = 0; fr_it < num; fr_it++) {
        // The fixed traffic only has one offset
        Offset *off_pt = get_offset_it(&frames[fr_it], 0);
        // Fix the transmission time in the model
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            sprintf(name, "Fix_Off_%d_%d", fr_it, inst);
            long long int trans_time = get_trans_time(off_pt, inst, 0);
            if (GRBaddvar(model, 0, NULL, NULL, 0, trans_time, trans_time, GRB_INTEGER, name)) {
                printf("%s\n", GRBgeterrormsg(env));
                return -1;
            }
            set_var_name(off_pt, inst, 0, var_it);
            var_it += 1;
        }
    }
    
    // Add all the variables for the self-healing protocol if it exists
    SelfHealing_Protocol *shp = get_healing_protocol();
    int instances_protocol = (int)(get_hyperperiod() / shp->period);
    var_shp_optimize = malloc(sizeof(int) * instances_protocol);
    for (int i = 0; i < instances_protocol; i++) {
        int trans_time = (int)(shp->period * i);
        sprintf(name, "SHP_%d", i);
        if (GRBaddvar(model, 0, NULL, NULL, 0, trans_time, trans_time, GRB_INTEGER, name)) {
            printf("%s\n", GRBgeterrormsg(env));
            return -1;
        }
        var_shp_optimize[i] = var_it;
        var_it += 1;
    }
    
    GRBupdatemodel(model);
    
    return 0;
}

/**
 Add traffic to the solver with the avaiable range
 
 @param frames pointer to the frames to allocate
 @param num number of frames to fix
 @param accum_num number of frames that were already created their offsets
 @return 0 if done corretly, -1 otherwise
 */
int add_traffic_optimize(Frame *frames, int num, int accum_num) {
    
    char name[100];
    
    // For all the fixed frames, add them into the solver with a fixed range
    for (int i = accum_num; (i - accum_num) < num; i++) {
        int frame_id = get_frame_id(i);
        // The fixed traffic only has one offset
        Offset *off_pt = get_offset_it(&frames[i], 0);
        // Fix the transmission time in the model
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            sprintf(name, "Off_%d_%d", frame_id, inst);
            long long int lb = get_min_trans_time(off_pt, inst, 0);
            long long int ub = get_max_trans_time(off_pt, inst, 0);
            if (GRBaddvar(model, 0, NULL, NULL, 0, lb, ub, GRB_INTEGER, name)) {
                printf("%s\n", GRBgeterrormsg(env));
                return -1;
            }
            set_var_name(off_pt, inst, 0, var_it);
            var_it += 1;
        }
    }
    
    GRBupdatemodel(model);
    
    return 0;
}

/**
 Init the variables that maximize the distances between transmission of frames and the link for the optimize
 
 @param frames list of frames to create the contraint
 @param num number of frames in the list
 @param accum_num number of frames that were already created their offsets
 @param it iteration for creating the link intermission differently for each iteration
 @return 0 if done correctly, -1 otherwise
 */
int create_intermission_variables_optimize(Frame *frames, int num, int accum_num, int it) {
    
    char name[100];
    
    // If link distances were init, remove the obj from them
    if (link_dis != NULL) {
        GRBsetdblattrelement(model, GRB_DBL_ATTR_OBJ, link_dis[0], 0.0);
    }
    
    // Allocate to save the frame and link distances variables
    frame_dis = realloc(frame_dis, sizeof(int) * (accum_num + num));
    link_dis = malloc(sizeof(int));
    
    // Create all the frame intermissions
    for (int i = accum_num; (i - accum_num) < num; i++) {
        sprintf(name, "FrameDis_%d", get_frame_id(i));
        
        // Calculate the maximum distance the frame could have
        Offset *off_pt = get_offset_it(&frames[i], 0);
        long long int max_distance = get_max_trans_time(off_pt, 0, 0) - get_min_trans_time(off_pt, 0, 0);
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            long long int distance = get_max_trans_time(off_pt, inst, 0) - get_min_trans_time(off_pt, inst, 0);;
            if (max_distance < distance) {
                max_distance = distance;
            }
        }
    
        if (GRBaddvar(model, 0, NULL, NULL, frame_dis_w, 0, max_distance, GRB_INTEGER, name)) {
            printf("%s\n", GRBgeterrormsg(env));
            return -1;
        }
        frame_dis[i] = var_it;
        var_it += 1;
        
        for (int inst = 0; inst < get_off_num_instances(off_pt); inst++) {
            int var_off[] = {get_var_name(off_pt, inst, 0), frame_dis[i]};
            double val[] = {1, -1};
            
            // Offset - frame distance > LB
            if (GRBaddconstr(model, 2, var_off, val, GRB_GREATER_EQUAL, get_min_trans_time(off_pt, inst, 0), NULL)) {
                printf("%s\n", GRBgeterrormsg(env));
                return -1;
            }
            
            double val2[] = {1, 1};

            // Offset - frame instance < UB
            if (GRBaddconstr(model, 2, var_off, val2, GRB_LESS_EQUAL, get_max_trans_time(off_pt, inst, 0), NULL)) {
                printf("%s\n", GRBgeterrormsg(env));
                return -1;
            }
        }
        
    }
    
    // Create the link intermissions
    sprintf(name, "LinkDis_%d", it);
    if (GRBaddvar(model, 0, NULL, NULL, link_dis_w, 0, get_hyperperiod(), GRB_INTEGER, name)) {
        printf("%s\n", GRBgeterrormsg(env));
        return -1;
    }
    link_dis[0] = var_it;
    var_it += 1;
    
    return 0;
}

/**
 Avoid that any frame transmission collides at the same time on the optimize
 
 @param frames list of frames to create the constraint
 @param num number of frames in the list
 @param accum_num number of frames that were already created their offsets
 @return 0 if done correctly, -1 otherwise
 */
int avoid_collision_optimize(Frame *frames, int num, int accum_num) {
 
    char name[100];
    SelfHealing_Protocol *shp = get_healing_protocol();
    int instances_protocol = (int)(get_hyperperiod() / shp->period);
    
    // For all frames, for all its offsets, if the offsets can collide, add constraint to avoid it
    for (int fr_it = accum_num; (fr_it - accum_num) < num; fr_it++) {
        Offset *off = get_offset_it(&frames[fr_it], 0);
        int link_inter = link_dis[0];
        
        // For all the frames that were added before, check if the offsets ids are the same to add the constraint
        int pre_fr_it = 0;
        while (pre_fr_it < fr_it) {
            
            // Get the previous frame pointer, or the bandwitdh allocation frame
            Frame *pre_frame_pt = &frames[pre_fr_it];
            
            Offset *pre_off = get_offset_it(pre_frame_pt, 0);
            // If the frame has an offset with the same link, continue
            for (int inst = 0; inst < get_off_num_instances(off); inst++) {
                for (int pre_inst = 0; pre_inst < get_off_num_instances(pre_off); pre_inst++) {
                    
                    // Check if both offsets share an interval and we need to add the constraint
                    long long int min1 = get_min_trans_time(off, inst, 0);
                    long long int max1 = get_max_trans_time(off, inst, 0);
                    long long int min2 = get_min_trans_time(pre_off, pre_inst, 0);
                    long long int max2 = get_max_trans_time(pre_off, pre_inst, 0);
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
            pre_fr_it += 1;
        }
        
        // Take into account the SHP reservation too
        for (int inst = 0; inst < get_off_num_instances(off); inst++) {
            for (int i = 0; i < instances_protocol; i++) {
                
                long long int min1 = get_min_trans_time(off, inst, 0);
                long long int max1 = get_max_trans_time(off, inst, 0);
                long long int min2 = (shp->period * i);
                long long int max2 = (shp->period * i) + shp->time;
                
                if ((min1 <= min2 && min2 < max1) || (min2 <= min1 && min1 < max2)) {
                    
                    long long int distance1 = get_off_time(off);
                    long long int distance2 = shp->time;
                    
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
                    int var[] = {get_var_name(off, inst, 0),
                        var_shp_optimize[i],
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
    GRBupdatemodel(model);
    return 0;
}

/* Functions */

/**
 Get the execution time of the last algorithm applied
 */
long long int get_execution_time(void) {
    
    return (long long int) execution_time;
}

/**
 Schedule all the transmission times of all the frames at the same time given the given scheduling parameters.
 It first init the solver and the variables for all the offsets transmission times between their deadlines.
 Then avoid that any offset collides.
 Forces that all frames has to wait at least a minimum switch time
 There exist a limit between the time the transmission starts and the time all the receivers get the frame
 If the protocol bandwitch is activated, avoid frames to the transmitted at the reserver bandwidth
 There might optimization, such as minimize the timespan, of increase the reparability
 */
int one_shot_scheduling(void) {
    
    init_solver();
    Traffic *t = get_traffic();
    
    if (create_offsets_variables(t->frames, t->num_frames, 0, 1) == -1) {
        fprintf(stderr, "Failure creating offsets\n");
        return -1;
    }
    
    if (create_intermission_variables(t->frames, t->num_frames, 0, 0) == -1) {
        fprintf(stderr, "Failure creating intermission variables\n");
        return -1;
    }

    if (path_dependent(t->frames, t->num_frames, 0) == -1) {
        fprintf(stderr, "Failure adding path dependent constraints\n");
        return -1;
    }

    if (end_to_end_delay(t->frames, t->num_frames, 0) == -1) {
        fprintf(stderr, "Failure adding end to end delay constraints\n");
        return -1;
    }

    if (contention_free(t->frames, t->num_frames, 0) == -1) {
        fprintf(stderr, "Failure adding contention free constraints\n");
        return -1;
    }
    
    
    GRBoptimize(model);
    
    int solcount;
    GRBgetintattr(model, GRB_INT_ATTR_SOLCOUNT, &solcount);
    if (solcount == 0) {
        fprintf(stderr, "No schedule found\n");
        return -1;
    }
    
    // Save the obtained model into internal memory and check if the solver is correct (does not violate constraints)
    save_offsets(t->frames, t->num_frames, 0);
    if (check_schedule(t->frames, t->num_frames) != 0) {
        fprintf(stderr, "The obtained schedule violates some of the given constraints\n");
        return -1;
    }
    
    close_solver();
    return 0;
}

/**
 Schedule all the tranmission times of all the frames iteratively.
 The number of frames per each iteration and the timing limit is given in the scheduling paramenters file
 */
int incremental_approach(void) {
    
    int frames_scheduled = 0;       // Number of frames already scheduled
    int it = 1;                     // Number of iteration done in the incremental approach
    int do_protocol = 1;            // Init variables of the self-healing protocol
    
    init_solver();
    Traffic *t = get_traffic();
    
    // While there are frames to schedule, we iterate
    while (frames_scheduled < t->num_frames) {
        
        // Adjust the frame_it so it does not try to schedule frames that do not exist
        if (frames_scheduled + frames_it > t->num_frames) {
            frames_it = t->num_frames - frames_scheduled;
        }
        if (frames_scheduled == 0) {
            do_protocol = 1;
        } else {
            do_protocol = 0;
        }
        
        if (create_offsets_variables(t->frames, frames_it, frames_scheduled, do_protocol) == -1) {
            fprintf(stderr, "Failure creating offsets\n");
            return -1;
        }
        
        if (create_intermission_variables(t->frames, frames_it, frames_scheduled, it) == -1) {
            fprintf(stderr, "Failure creating intermission variables\n");
            return -1;
        }
        
        if (path_dependent(t->frames, frames_it, frames_scheduled) == -1) {
            fprintf(stderr, "Failure adding path dependent constraints\n");
            return -1;
        }
        
        if (end_to_end_delay(t->frames, frames_it, frames_scheduled) == -1) {
            fprintf(stderr, "Failure adding end to end delay constraints\n");
            return -1;
        }
        
        if (contention_free(t->frames, frames_it, frames_scheduled) == -1) {
            fprintf(stderr, "Failure adding contention free constraints\n");
            return -1;
        }
        
        GRBoptimize(model);
        
        int solcount;
        GRBgetintattr(model, GRB_INT_ATTR_SOLCOUNT, &solcount);
        if (solcount == 0) {
            fprintf(stderr, "No schedule found for the iteration %d\n", it);
            return -1;
        }
        
        // Save the obtained model into internal memory and check if the solver is correct (does not violate constraints)
        save_offsets(t->frames, frames_it, frames_scheduled);
        
        // Adjust the indexes
        it += 1;
        frames_scheduled += frames_it;
    }
    
    if (check_schedule(t->frames, t->num_frames) != 0) {
        fprintf(stderr, "The obtained schedule violates some of the given constraints\n");
        return -1;
    }
    
    close_solver();
    return 0;
}

/**
 Schedule the network given the parameters read before
  */
int schedule_network(void) {
    
    switch (algorithm) {
        case one_shot:
            if (one_shot_scheduling() != 0) {
                fprintf(stderr, "The schedule could not be found with the one-shot approach\n");
                return -1;
            }
            break;
            
        case incremental:
            if (incremental_approach() != 0) {
                fprintf(stderr, "The schedule could not be found with the incremental approach\n");
                return -1;
            }
            break;
        default:
            fprintf(stderr, "The given scheduler algorithm is not implemented\n");
            return -1;
            break;
    }
    return 0;
}

/**
 Patch the traffic in a fast heuristic
 */
int patch(void) {
    
    // Get the starting time to execute
    execution_time = clock_gettime_nsec_np(CLOCK_REALTIME);
    
    Traffic *t = get_traffic();
    int fixed_frames = get_num_fixed_frames();
    
    // Prepare the fixed traffic
    if (prepare_fixed_traffic(t->frames, fixed_frames) == -1) {
        fprintf(stderr, "Error preparing the fixed traffic when patching\n");
        return -1;
    }
    
    // For all frames, allocate a frame at a time
    if (allocate_patch_traffic(&t->frames[fixed_frames], t->num_frames - fixed_frames) == -1) {
        fprintf(stderr, "Error allocating traffic when patching\n");
        return -1;
    }
    
    execution_time = clock_gettime_nsec_np(CLOCK_REALTIME) - execution_time;
    
    return 0;
}

/**
 Optimize the traffic that was patched before
 
 @return 0 if optimize was found, -1 otherwise
 */
int optimize(void) {
    
    // Get the starting time to execute
    execution_time = clock_gettime_nsec_np(CLOCK_REALTIME);
    
    Traffic *t = get_traffic();
    int fixed_frames = get_num_fixed_frames();

    init_solver();
    
    // Add the fixed traffic to the solver
    if (add_fixed_traffic(t->frames, fixed_frames) == -1) {
        fprintf(stderr, "Error adding the fixed variables to the solver when optimizing\n");
        return -1;
    }
    
    int frames_scheduled = fixed_frames;        // Number of frames already scheduled
    int it = 1;                                 // Number of iteration done in the incremental approach
    
    // While there are frames to schedule, we iterate
    while (frames_scheduled < t->num_frames) {
        
        // Adjust the frame_it so it does not try to schedule frames that do not exist
        if (frames_scheduled + frames_it > t->num_frames) {
            frames_it = t->num_frames - frames_scheduled;
        }
        
        // Allocate a frame at a time
        if (add_traffic_optimize(t->frames, frames_it, frames_scheduled) == -1) {
            fprintf(stderr, "Error allocating traffic when optimizing\n");
            return -1;
        }
        
        // Create the intermission variables to maximize
        if (create_intermission_variables_optimize(t->frames, frames_it, frames_scheduled, it) == -1) {
            fprintf(stderr, "Failure creating intermission variables\n");
            return -1;
        }
        
        // Avoid collision for the new allocated frames
        if (avoid_collision_optimize(t->frames, frames_it, frames_scheduled) == -1) {
            fprintf(stderr, "Error avoiding collision when optimizing\n");
            return -1;
        }
        
        GRBoptimize(model);
        
        int solcount;
        GRBgetintattr(model, GRB_INT_ATTR_SOLCOUNT, &solcount);
        if (solcount == 0) {
            fprintf(stderr, "No schedule found for the iteration %d\n", it);
            return -1;
        }
        
        // Save the obtained model into internal memory and check if the solver is correct
        save_offsets(t->frames, frames_it, frames_scheduled);
        
        // Adjust the indexes
        it += 1;
        frames_scheduled += frames_it;
    }
    
    close_solver();
    
    execution_time = clock_gettime_nsec_np(CLOCK_REALTIME) - execution_time;
    
    return 0;
}

/* Input Functions */

/**
 Get the value of the given path in double

 @param top_xml pointer to the top of the xml tree
 @param path to the parameters to read
 @return the read parameter converted to dbl, -1 otherwise
 */
double get_float_value_xml(xmlDoc *top_xml, char *path) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    
    double return_value;
    
    // Search for the value
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) path, context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value float is not defined\n");
        return -1.0;
    }
    value = xmlNodeListGetString(top_xml, result->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
    
    return_value = atof((char*)value);
    
    // Free xml objects
    xmlFree(value);
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    
    return return_value;
}

/**
 Read the scheduler parameters
 */
int read_schedule_parameters_xml(char *parameters_xml) {
    
    // Init xml variables needed to search information in the file
    xmlChar *value = NULL, *value2;
    xmlXPathContextPtr context;
    xmlXPathObjectPtr result;
    xmlDoc *top_xml;        // Variables that contains the xml document top tree
    double timelimit, MIPGAP;
    
    // Open the xml file if it exists
    top_xml = xmlReadFile(parameters_xml, NULL, 0);
    if (top_xml == NULL) {
        fprintf(stderr, "The given xml file does not exist\n");
        return -1;
    }
    
    // Search for the algorithm
    context = xmlXPathNewContext(top_xml);
    result = xmlXPathEvalExpression((xmlChar*) "/Configuration/Schedule/Algorithm", context);
    if (result->nodesetval->nodeTab == NULL) {
        fprintf(stderr, "The searched value algorithm is not defined\n");
        return -1;
    }
    value2 = xmlGetProp(result->nodesetval->nodeTab[0], (xmlChar*) "name");
    if (set_algorithm((char *)value2) != 0) {
        fprintf(stderr, "Error reading the scheduling algorithm\n");
        return -1;
    }
    
    MIPGAP = get_float_value_xml(top_xml, "/Configuration/Schedule/Algorithm/MIPGAP");
    if (set_MIPGAP(MIPGAP) != 0) {
        fprintf(stderr, "The MIPGAP was wrongly read\n");
        return -1;
    }
    timelimit = get_float_value_xml(top_xml, "/Configuration/Schedule/Algorithm/TimeLimit");
    if (set_timelimit(timelimit) != 0) {
        fprintf(stderr, "The time limit was wrongly read\n");
        return -1;
    }
    
    // If the algorithm is the incremental approach, read also the number of frames scheduled per iteration
    if (algorithm == incremental) {
        
        // Search for the value
        context = xmlXPathNewContext(top_xml);
        result = xmlXPathEvalExpression((xmlChar*) "/Configuration/Schedule/Algorithm/FramesIteration", context);
        if (result->nodesetval->nodeTab == NULL) {
            fprintf(stderr, "The searched value Frames Iteration is not defined\n");
            return -1;
        }
        value = xmlNodeListGetString(top_xml, result->nodesetval->nodeTab[0]->xmlChildrenNode, 1);
        frames_it = atoi((char *)value);
    }
    
    // Free xml objects
    xmlFree(value);
    xmlFree(value2);
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    xmlFreeDoc(top_xml);
    return 0;
}
