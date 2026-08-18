/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
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
#define UART_SCREEN_TX_Pin GPIO_PIN_0
#define UART_SCREEN_TX_GPIO_Port GPIOA
#define UART_SCREEN_RX_Pin GPIO_PIN_1
#define UART_SCREEN_RX_GPIO_Port GPIOA
#define USART_COMPUTER_TX_Pin GPIO_PIN_2
#define USART_COMPUTER_TX_GPIO_Port GPIOA
#define USART_COMPUTER_RX_Pin GPIO_PIN_3
#define USART_COMPUTER_RX_GPIO_Port GPIOA
#define AD9288_DA0_Pin GPIO_PIN_0
#define AD9288_DA0_GPIO_Port GPIOB
#define AD9288_DA1_Pin GPIO_PIN_1
#define AD9288_DA1_GPIO_Port GPIOB
#define AD9288_DA2_Pin GPIO_PIN_2
#define AD9288_DA2_GPIO_Port GPIOB
#define AD9288_DB2_Pin GPIO_PIN_10
#define AD9288_DB2_GPIO_Port GPIOB
#define AD9288_DB3_Pin GPIO_PIN_11
#define AD9288_DB3_GPIO_Port GPIOB
#define AD9288_DB4_Pin GPIO_PIN_12
#define AD9288_DB4_GPIO_Port GPIOB
#define AD9288_DB5_Pin GPIO_PIN_13
#define AD9288_DB5_GPIO_Port GPIOB
#define AD9288_DB6_Pin GPIO_PIN_14
#define AD9288_DB6_GPIO_Port GPIOB
#define AD9288_DB7_Pin GPIO_PIN_15
#define AD9288_DB7_GPIO_Port GPIOB
#define AD9833_FSYNC_Pin GPIO_PIN_11
#define AD9833_FSYNC_GPIO_Port GPIOD
#define AD9833_SCLK_Pin GPIO_PIN_12
#define AD9833_SCLK_GPIO_Port GPIOD
#define AD9833_SDATA_Pin GPIO_PIN_13
#define AD9833_SDATA_GPIO_Port GPIOD
#define DIO_S1_Pin GPIO_PIN_6
#define DIO_S1_GPIO_Port GPIOG
#define DIO_S2_Pin GPIO_PIN_7
#define DIO_S2_GPIO_Port GPIOG
#define HC_A1_Pin GPIO_PIN_6
#define HC_A1_GPIO_Port GPIOC
#define HC_B1_Pin GPIO_PIN_7
#define HC_B1_GPIO_Port GPIOC
#define HC_C1_Pin GPIO_PIN_8
#define HC_C1_GPIO_Port GPIOC
#define AD9288_CLKA_Pin GPIO_PIN_8
#define AD9288_CLKA_GPIO_Port GPIOA
#define AD9288_CLKB_Pin GPIO_PIN_9
#define AD9288_CLKB_GPIO_Port GPIOA
#define HC_A0_Pin GPIO_PIN_10
#define HC_A0_GPIO_Port GPIOA
#define HC_B0_Pin GPIO_PIN_11
#define HC_B0_GPIO_Port GPIOA
#define HC_C0_Pin GPIO_PIN_12
#define HC_C0_GPIO_Port GPIOA
#define RLY1_Pin GPIO_PIN_15
#define RLY1_GPIO_Port GPIOA
#define DIO_RA0_Pin GPIO_PIN_10
#define DIO_RA0_GPIO_Port GPIOC
#define DIO_RA1_Pin GPIO_PIN_11
#define DIO_RA1_GPIO_Port GPIOC
#define RLY0_Pin GPIO_PIN_12
#define RLY0_GPIO_Port GPIOC
#define CANCEL_Pin GPIO_PIN_9
#define CANCEL_GPIO_Port GPIOG
#define CONFIRM_Pin GPIO_PIN_10
#define CONFIRM_GPIO_Port GPIOG
#define RIGHT_Pin GPIO_PIN_11
#define RIGHT_GPIO_Port GPIOG
#define LEFT_Pin GPIO_PIN_12
#define LEFT_GPIO_Port GPIOG
#define DOWN_Pin GPIO_PIN_13
#define DOWN_GPIO_Port GPIOG
#define UP_Pin GPIO_PIN_14
#define UP_GPIO_Port GPIOG
#define AD9288_DA3_Pin GPIO_PIN_3
#define AD9288_DA3_GPIO_Port GPIOB
#define AD9288_DA4_Pin GPIO_PIN_4
#define AD9288_DA4_GPIO_Port GPIOB
#define AD9288_DA5_Pin GPIO_PIN_5
#define AD9288_DA5_GPIO_Port GPIOB
#define AD9288_DA6_Pin GPIO_PIN_6
#define AD9288_DA6_GPIO_Port GPIOB
#define AD9288_DA7_Pin GPIO_PIN_7
#define AD9288_DA7_GPIO_Port GPIOB
#define AD9288_DB0_Pin GPIO_PIN_8
#define AD9288_DB0_GPIO_Port GPIOB
#define AD9288_DB1_Pin GPIO_PIN_9
#define AD9288_DB1_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
