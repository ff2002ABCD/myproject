/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <math.h>
#include "G85hal.h"
#include <string.h>
#include "menu.h"
#include "function.h"
#include "flash.h"
#include "ch376.h"

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define SW_Pin GPIO_PIN_1
#define SW_GPIO_Port GPIOC
#define KEY_Pin GPIO_PIN_6
#define KEY_GPIO_Port GPIOA
#define CANCEL_Pin GPIO_PIN_6
#define CANCEL_GPIO_Port GPIOC
#define CONFIRM_Pin GPIO_PIN_7
#define CONFIRM_GPIO_Port GPIOC
#define DOWN_Pin GPIO_PIN_8
#define DOWN_GPIO_Port GPIOC
#define UP_Pin GPIO_PIN_9
#define UP_GPIO_Port GPIOC

/* USER CODE BEGIN Private defines */
extern int fputc(int ch, FILE* file);
/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
