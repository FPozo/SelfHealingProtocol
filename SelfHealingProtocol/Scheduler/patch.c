/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Patch.c                                                                                                            *
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

//    read_patch_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/Patch_6_1.xml");
//    if (patch() == -1) {
//        write_execution_time_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/Execution.xml");
//        return 0;
//    }
//    write_execution_time_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/Execution.xml");
//    write_patch_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/PatchedSchedule_6_1.xml");
    
    read_patch_xml((char*) argv[1]);
    if (patch() == -1) {
        write_execution_time_xml((char*) argv[3]);
        return 0;
    }
    write_execution_time_xml((char*) argv[3]);
    write_patch_xml((char*) argv[2]);
    return 0;
}
