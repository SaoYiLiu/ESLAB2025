/**
  ******************************************************************************
  * @file    network_1764519189663_data_params.h
  * @author  AST Embedded Analytics Research Platform
  * @date    2025-12-15T23:39:39+0800
  * @brief   AI Tool Automatic Code Generator for Embedded NN computing
  ******************************************************************************
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  ******************************************************************************
  */

#ifndef NETWORK_1764519189663_DATA_PARAMS_H
#define NETWORK_1764519189663_DATA_PARAMS_H

#include "ai_platform.h"

/*
#define AI_NETWORK_1764519189663_DATA_WEIGHTS_PARAMS \
  (AI_HANDLE_PTR(&ai_network_1764519189663_data_weights_params[1]))
*/

#define AI_NETWORK_1764519189663_DATA_CONFIG               (NULL)


#define AI_NETWORK_1764519189663_DATA_ACTIVATIONS_SIZES \
  { 84324, }
#define AI_NETWORK_1764519189663_DATA_ACTIVATIONS_SIZE     (84324)
#define AI_NETWORK_1764519189663_DATA_ACTIVATIONS_COUNT    (1)
#define AI_NETWORK_1764519189663_DATA_ACTIVATION_1_SIZE    (84324)



#define AI_NETWORK_1764519189663_DATA_WEIGHTS_SIZES \
  { 93356, }
#define AI_NETWORK_1764519189663_DATA_WEIGHTS_SIZE         (93356)
#define AI_NETWORK_1764519189663_DATA_WEIGHTS_COUNT        (1)
#define AI_NETWORK_1764519189663_DATA_WEIGHT_1_SIZE        (93356)



#define AI_NETWORK_1764519189663_DATA_ACTIVATIONS_TABLE_GET() \
  (&g_network_1764519189663_activations_table[1])

extern ai_handle g_network_1764519189663_activations_table[1 + 2];



#define AI_NETWORK_1764519189663_DATA_WEIGHTS_TABLE_GET() \
  (&g_network_1764519189663_weights_table[1])

extern ai_handle g_network_1764519189663_weights_table[1 + 2];


#endif    /* NETWORK_1764519189663_DATA_PARAMS_H */
