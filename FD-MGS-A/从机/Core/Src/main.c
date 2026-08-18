/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "string.h"
#include "stdio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

// DMA宏定义
#ifndef DMA_IT_HT
#define DMA_IT_HT                         ((uint32_t)0x0004)
#endif

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define CMD_BUFFER_SIZE 20
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;
UART_HandleTypeDef huart3;
DMA_HandleTypeDef hdma_usart1_rx;
DMA_HandleTypeDef hdma_usart1_tx;
DMA_HandleTypeDef hdma_usart2_rx;
DMA_HandleTypeDef hdma_usart2_tx;
DMA_HandleTypeDef hdma_usart3_rx;
DMA_HandleTypeDef hdma_usart3_tx;

/* USER CODE BEGIN PV */
// 接收缓冲区
uint8_t UART1_RxBuffer[UART_RX_BUFFER_SIZE];
uint8_t UART1_TxBuffer[UART_RX_BUFFER_SIZE];
uint16_t UART1_RxCount = 0;
uint8_t UART2_RxChar;
uint8_t UART3_RxChar;
uint8_t DataReady = 0;
uint8_t CmdMode = 0xA2;  // 默认模式为8bit AD数据
// 处理后的数据缓冲区
uint8_t ProcessedDataBuffer[PROCESSED_DATA_SIZE];
// 数据转发目标控制
typedef enum {
  FORWARD_TO_NONE = 0,
  FORWARD_TO_UART2 = 1,
  FORWARD_TO_UART3 = 2
} ForwardTarget_t;

ForwardTarget_t CurrentForwardTarget = FORWARD_TO_NONE;
uint32_t LastCommandTime = 0;  // 记录最后一次接收指令的时间
#define COMMAND_TIMEOUT_MS 30000  // 30秒超时，超时后清除转发目标
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART3_UART_Init(void);
/* USER CODE BEGIN PFP */
void ProcessCommand(uint8_t cmd);
void ProcessReceivedData(uint8_t* inputData, uint16_t inputSize);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/**
 * @brief Process received data by averaging every 5 values
 * @param inputData Pointer to input data buffer
 * @param inputSize Size of input data
 * @retval None
 */


/**
 * @brief Process received command
 * @param cmd Command byte
 * @retval None
 */
void ProcessCommand(uint8_t cmd)
{ 
  switch(cmd)
  {
    case 0xA1:
      CmdMode = 0xA1;
      // 发送0xA1命令到H750
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xA1", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
    
    case 0xA2:
      CmdMode = 0xA2;
      // 发送0xA2命令到H750
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xA2", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
    
    case 0xA4:
      CmdMode = 0xA4;
      // 发送0xA4命令到H750
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xA4", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
      
    // 曝光时间设置命令 0xB1-0xBF
    case 0xB1:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB1", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB2:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB2", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB3:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB3", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB4:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB4", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB5:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB5", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
         
    case 0xB6:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB6", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB7:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB7", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB8:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB8", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xB9:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xB9", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBA:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBA", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBB:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBB", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBC:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBC", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBD:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBD", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBE:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBE", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
       
    case 0xBF:
      HAL_UART_Transmit(&huart1, (uint8_t*)"\xBF", 1, 100);
      // 确保DMA接收已启动
      HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
      __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
      break;
      
    default:
      break;
  }
}

/**
 * @brief  Reception Event Callback (Rx event notification called after use of advanced reception service).
 * @param  huart UART handle
 * @param  Size  Number of data available in application reception buffer (indicates a reception complete to Size data)
 * @retval None
 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
  if (huart->Instance == huart1.Instance)
  {
    // 记录接收到的数据大小
    UART1_RxCount = Size;
    
    // 禁用全局中断，确保数据处理不被打�?
    __disable_irq();
    
    // 立即停止DMA接收，防止数据被覆盖
    HAL_UART_DMAStop(&huart1);
    
    // 使用memcpy快�?�复制数据到发�?�缓冲区
    memcpy(UART1_TxBuffer, UART1_RxBuffer, Size);
    
    // 重新启用中断
    __enable_irq();
    
    // 检查指令超时
    if(CurrentForwardTarget != FORWARD_TO_NONE && 
       (HAL_GetTick() - LastCommandTime) > COMMAND_TIMEOUT_MS)
    {
      // 指令超时，清除转发目标
      CurrentForwardTarget = FORWARD_TO_NONE;
    }
    
    // 根据当前转发目标智能转发数据
    uint16_t total_sent = 0;
    UART_HandleTypeDef *target_uart = NULL;
    
    // 确定目标UART
    switch(CurrentForwardTarget)
    {
      case FORWARD_TO_UART2:
        target_uart = &huart2;
        break;
      case FORWARD_TO_UART3:
        target_uart = &huart3;
        break;
      case FORWARD_TO_NONE:
      default:
        // 没有指定目标，不转发数据
        goto restart_reception;
    }
    
    // 发送数据到指定的目标UART
    while(total_sent < Size)
    {
      // 计算剩余字节数
      uint16_t remaining = Size - total_sent;
      
      // 发送剩余数据，使用较短的超时时间但会重试
      HAL_StatusTypeDef result = HAL_UART_Transmit(target_uart, &UART1_TxBuffer[total_sent], remaining, 2000);
      
      if(result == HAL_OK)
      {
        // 全部发送成功
        total_sent = Size;
        break;
      }
      else if(result == HAL_TIMEOUT)
      {
        // 超时，可能部分发送成功，尝试逐字节发送剩余数据
        for(uint16_t i = total_sent; i < Size; i++)
        {
          if(HAL_UART_Transmit(target_uart, &UART1_TxBuffer[i], 1, 100) == HAL_OK)
          {
            total_sent++;
          }
          else
          {
            break;  // 如果单字节也失败，退出
          }
        }
        break;
      }
      else
      {
        // 其他错误，短暂延时后重试
        HAL_Delay(10);
      }
    }
    
restart_reception:
    
    // 发�?�完成后重启UART1接收
    HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
    __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
  }
}
/**
 * @brief Process received data
 * @param None
 * @retval None
 */


/**
 * @brief UART RX complete callback
 * @param huart UART handle
 * @retval None
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == huart2.Instance)
  {
    // 接收到UART2指令，设置转发目标为UART2
    CurrentForwardTarget = FORWARD_TO_UART2;
    LastCommandTime = HAL_GetTick();  // 记录指令时间
    
    // Process received command from UART2
    ProcessCommand(UART2_RxChar);
    
    // Restart reception
    HAL_UART_Receive_IT(&huart2, &UART2_RxChar, 1);
  }
  else if (huart->Instance == huart3.Instance)
  {
    // 接收到UART3指令，设置转发目标为UART3
    CurrentForwardTarget = FORWARD_TO_UART3;
    LastCommandTime = HAL_GetTick();  // 记录指令时间
    
    // Process received command from UART3
    ProcessCommand(UART3_RxChar);
    
    // Restart reception
    HAL_UART_Receive_IT(&huart3, &UART3_RxChar, 1);
  }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART1_UART_Init();
  MX_USART2_UART_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */
  
  // 启动时自动发送0xA2命令到H750
  HAL_UART_Transmit(&huart1, (uint8_t*)"\xA2", 1, 100);
  
  // 重新启动DMA接收
  HAL_UARTEx_ReceiveToIdle_DMA(&huart1, UART1_RxBuffer, UART_RX_BUFFER_SIZE);
  __HAL_DMA_DISABLE_IT(&hdma_usart1_rx, 0x0004);
  
  // Start UART2 single character reception
  HAL_UART_Receive_IT(&huart2, &UART2_RxChar, 1);
  
  // Start UART3 single character reception (与UART2相同的配置)
  HAL_UART_Receive_IT(&huart3, &UART3_RxChar, 1);
  
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    // Check if new data needs to be processed
 
    
    // Add a small delay to avoid high CPU usage
    HAL_Delay(1);
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 921600;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 256000;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel2_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel2_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel2_IRQn);
  /* DMA1_Channel3_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);
  /* DMA1_Channel4_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
  /* DMA1_Channel5_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);
  /* DMA1_Channel6_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel6_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel6_IRQn);
  /* DMA1_Channel7_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel7_IRQn);

}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 256000;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
