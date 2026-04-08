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
#include "stm32h7xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */
extern uint16_t current_count,last_count,adc_value,current_angle,last_angle,adc_value_setzero;
extern uint32_t	current_time;

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
#define CONFIRM_Pin GPIO_PIN_1
#define CONFIRM_GPIO_Port GPIOD
#define CANCEL_Pin GPIO_PIN_2
#define CANCEL_GPIO_Port GPIOD
#define LEFT_Pin GPIO_PIN_3
#define LEFT_GPIO_Port GPIOD
#define RIGHT_Pin GPIO_PIN_4
#define RIGHT_GPIO_Port GPIOD
#define UP_Pin GPIO_PIN_5
#define UP_GPIO_Port GPIOD
#define DOWN_Pin GPIO_PIN_6
#define DOWN_GPIO_Port GPIOD
#define FUNC_Pin GPIO_PIN_7
#define FUNC_GPIO_Port GPIOD

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
