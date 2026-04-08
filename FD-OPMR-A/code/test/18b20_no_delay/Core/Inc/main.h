/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
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
#define HC_C0_Pin GPIO_PIN_3
#define HC_C0_GPIO_Port GPIOE
#define HC_B0_Pin GPIO_PIN_4
#define HC_B0_GPIO_Port GPIOE
#define HC_A0_Pin GPIO_PIN_5
#define HC_A0_GPIO_Port GPIOE
#define HC_C1_Pin GPIO_PIN_13
#define HC_C1_GPIO_Port GPIOC
#define HC_B1_Pin GPIO_PIN_14
#define HC_B1_GPIO_Port GPIOC
#define HC_A1_Pin GPIO_PIN_15
#define HC_A1_GPIO_Port GPIOC
#define RLY0_Pin GPIO_PIN_0
#define RLY0_GPIO_Port GPIOA
#define DIO_RA0_Pin GPIO_PIN_1
#define DIO_RA0_GPIO_Port GPIOA
#define RLY1_Pin GPIO_PIN_2
#define RLY1_GPIO_Port GPIOA
#define DIO_RA1_Pin GPIO_PIN_3
#define DIO_RA1_GPIO_Port GPIOA
#define DAC0_Pin GPIO_PIN_4
#define DAC0_GPIO_Port GPIOA
#define DAC1_Pin GPIO_PIN_5
#define DAC1_GPIO_Port GPIOA
#define TP_Pin GPIO_PIN_7
#define TP_GPIO_Port GPIOA
#define FUN_Pin GPIO_PIN_8
#define FUN_GPIO_Port GPIOE
#define CANCEL_Pin GPIO_PIN_12
#define CANCEL_GPIO_Port GPIOE
#define CONFIRM_Pin GPIO_PIN_13
#define CONFIRM_GPIO_Port GPIOE
#define RIGHT_Pin GPIO_PIN_14
#define RIGHT_GPIO_Port GPIOE
#define LEFT_Pin GPIO_PIN_15
#define LEFT_GPIO_Port GPIOE
#define DOWN_Pin GPIO_PIN_10
#define DOWN_GPIO_Port GPIOB
#define UP_Pin GPIO_PIN_11
#define UP_GPIO_Port GPIOB
#define TCO1_Pin GPIO_PIN_12
#define TCO1_GPIO_Port GPIOB
#define TCO2_Pin GPIO_PIN_13
#define TCO2_GPIO_Port GPIOB
#define DB0_Pin GPIO_PIN_8
#define DB0_GPIO_Port GPIOD
#define DB1_Pin GPIO_PIN_9
#define DB1_GPIO_Port GPIOD
#define DB2_Pin GPIO_PIN_10
#define DB2_GPIO_Port GPIOD
#define DB3_Pin GPIO_PIN_11
#define DB3_GPIO_Port GPIOD
#define DB4_Pin GPIO_PIN_12
#define DB4_GPIO_Port GPIOD
#define DB5_Pin GPIO_PIN_13
#define DB5_GPIO_Port GPIOD
#define DB6_Pin GPIO_PIN_14
#define DB6_GPIO_Port GPIOD
#define DB7_Pin GPIO_PIN_15
#define DB7_GPIO_Port GPIOD
#define TX1_Pin GPIO_PIN_9
#define TX1_GPIO_Port GPIOA
#define RX1_Pin GPIO_PIN_10
#define RX1_GPIO_Port GPIOA
#define RX2_Pin GPIO_PIN_11
#define RX2_GPIO_Port GPIOA
#define TX2_Pin GPIO_PIN_12
#define TX2_GPIO_Port GPIOA
#define DIO_S1_Pin GPIO_PIN_11
#define DIO_S1_GPIO_Port GPIOC
#define DIO_S2_Pin GPIO_PIN_12
#define DIO_S2_GPIO_Port GPIOC
#define DA0_Pin GPIO_PIN_0
#define DA0_GPIO_Port GPIOD
#define DA1_Pin GPIO_PIN_1
#define DA1_GPIO_Port GPIOD
#define DA2_Pin GPIO_PIN_2
#define DA2_GPIO_Port GPIOD
#define DA3_Pin GPIO_PIN_3
#define DA3_GPIO_Port GPIOD
#define DA4_Pin GPIO_PIN_4
#define DA4_GPIO_Port GPIOD
#define DA5_Pin GPIO_PIN_5
#define DA5_GPIO_Port GPIOD
#define DA6_Pin GPIO_PIN_6
#define DA6_GPIO_Port GPIOD
#define DA7_Pin GPIO_PIN_7
#define DA7_GPIO_Port GPIOD

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
