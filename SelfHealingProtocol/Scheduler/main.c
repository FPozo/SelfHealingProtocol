/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Main.c                                                                                                             *
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
    
    read_network_xml((char*) argv[1]);
    prepare_network();
    read_schedule_parameters_xml((char*) argv[2]);
    schedule_network();
    write_schedule_xml((char*) argv[3]);
    return 0;
}
