/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Optimize.c                                                                                                            *
 *  SelfHealingProtocol Scheduler                                                                                      *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 28/01/19.                                                                             *
 *  Copyright © 2019 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include <stdio.h>
#include "Scheduler/Network.h"
#include "Scheduler/Scheduler.h"

int main(int argc, const char * argv[]) {
    // insert code here...
    printf("Hello, Optimizing World!\n");
//    read_optimize_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/Optimize_6_1.xml");
//    optimize();
//    write_optimize_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/OptimizedSchedule_6_1.xml");
    read_optimize_xml((char*) argv[1]);
    if (optimize() == -1) {
        write_execution_time_xml((char*) argv[3]);
        return 0;
    }
    write_optimize_xml((char*) argv[2]);
    write_execution_time_xml((char*) argv[3]);
    return 0;
}
