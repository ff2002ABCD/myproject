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
#include "stdio.h"
#include <math.h>
#include "tim.h"
#include "gpio.h"
#include "key.h"
#include "menu.h"


/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */
#define UART_RX_BUFFER_SIZE 3648  // 接收缓冲区大小，与参考项目保持一致
/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */
void Get_CCD_Value(void);
/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define DOWN_Pin GPIO_PIN_4
#define DOWN_GPIO_Port GPIOA
#define RIGHT_Pin GPIO_PIN_5
#define RIGHT_GPIO_Port GPIOA
#define LEFT_Pin GPIO_PIN_6
#define LEFT_GPIO_Port GPIOA
#define CANCEL_Pin GPIO_PIN_7
#define CANCEL_GPIO_Port GPIOA
#define CONFIRM_Pin GPIO_PIN_0
#define CONFIRM_GPIO_Port GPIOB
#define UP_Pin GPIO_PIN_1
#define UP_GPIO_Port GPIOB
#define KEY_Pin GPIO_PIN_5
#define KEY_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
