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
    read_optimize_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/Optimize_6_1.xml");
    //    patch();
    //    write_patch_xml("/Users/fpo01/OneDrive - Mälardalens högskola/PhD Folder/Software/SelfHealingProtocol/SelfHealingProtocol/Files/Outputs/PatchedSchedule_6_1.xml");
//    read_patch_xml((char*) argv[1]);
//    patch();
//    write_patch_xml((char*) argv[2]);
    return 0;
}
