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
    // insert code here...
    printf("Hello, World!\n");
    read_network_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Networks/network.xml");
    prepare_network();
    read_schedule_parameters_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Configurations/Configuration.xml");
    schedule_network();
    write_schedule_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Schedules/schedule.xml");
    return 0;
}
