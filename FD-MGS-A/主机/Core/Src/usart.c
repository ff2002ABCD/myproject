/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    usart.c
  * @brief   This file provides code for the configuration
  *          of the USART instances.
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
#include "usart.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "delay.h" // 添加delay.h头文件

/* USER CODE BEGIN 0 */
struct __FILE
{
	int handle;
};

FILE __stdout;

void _sys_exit(int x)
{
	x = x;
}

int fputc(int ch, FILE* file)
{
    HAL_UART_Transmit(&huart1,(uint8_t*)&ch,1,0xffff);
    return ch;
}

// UART2接收缓冲区
uint8_t UART2_RxBuffer[4];

// UART3通信状态标志
uint8_t UART3_DataReceived = 0;  // 接收到数据标志
uint16_t UART3_ByteCount = 0;    // 接收到的字节数
CollectMode_t current_collect_mode = COLLECT_MODE_IDLE;

// 数据缓冲区
uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE]; // 原始数据缓冲区
uint8_t ProcessedDataBuffer[PROCESSED_DATA_SIZE]; // 处理后数据缓冲区

// 1组RAM存储的光谱数据
uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
// 所有组的信息（RAM中）
SpectrumGroupInfo spectrum_groups_info[12];

// 连续采集控制标志
volatile uint8_t need_send_a2_flag = 0;

// 透传互斥标志，防止多个addt指令同时发送
volatile uint8_t addt_in_progress = 0;

// 数据处理完成标志，防止在数据处理期间发送新的A2命令
volatile uint8_t data_processing_done = 1; // 初始为完成状态

// 页面切换锁标志，在切换页面时暂停数据处理
volatile uint8_t page_switching_lock = 0; // 初始为未锁定状态

// UART1接收缓冲区和状态（用于接收屏幕响应）
uint8_t UART1_RxBuffer[4];
uint8_t UART1_RxIndex = 0;
uint8_t ADDT_Ready = 0;     // 收到FE FF FF FF标志
uint8_t ADDT_Complete = 0;  // 收到FD FF FF FF标志

// DMA句柄声明
DMA_HandleTypeDef hdma_usart3_rx;
DMA_HandleTypeDef hdma_usart3_tx; // 添加UART3发送DMA句柄
/* USER CODE END 0 */

UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;
UART_HandleTypeDef huart3; 

/* USART1 init function */

void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 256000;
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
/* USART2 init function */

void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 9600;
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
/* USART3 init function */

void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 256000;  // 修改波特率为512000，与UART1匹配
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
  // 初始化状态标志
  UART3_DataReceived = 0;
  UART3_ByteCount = 0;
  memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);

  // 初始状态不启动DMA接收，等待按钮触发
  // HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
  /* USER CODE END USART3_Init 2 */

}

void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{

  GPIO_InitTypeDef GPIO_InitStruct = {0};
  if(uartHandle->Instance==USART1)
  {
  /* USER CODE BEGIN USART1_MspInit 0 */

  /* USER CODE END USART1_MspInit 0 */
    /* USART1 clock enable */
    __HAL_RCC_USART1_CLK_ENABLE();

    __HAL_RCC_GPIOA_CLK_ENABLE();
    /**USART1 GPIO Configuration
    PA9     ------> USART1_TX
    PA10     ------> USART1_RX
    */
    GPIO_InitStruct.Pin = GPIO_PIN_9;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_10;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USER CODE BEGIN USART1_MspInit 1 */

  /* USER CODE END USART1_MspInit 1 */
  }
  else if(uartHandle->Instance==USART2)
  {
  /* USER CODE BEGIN USART2_MspInit 0 */

  /* USER CODE END USART2_MspInit 0 */
    /* USART2 clock enable */
    __HAL_RCC_USART2_CLK_ENABLE();

    __HAL_RCC_GPIOA_CLK_ENABLE();
    /**USART2 GPIO Configuration
    PA2     ------> USART2_TX
    PA3     ------> USART2_RX
    */
    GPIO_InitStruct.Pin = GPIO_PIN_2;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_3;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* USART2 interrupt Init */
    HAL_NVIC_SetPriority(USART2_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(USART2_IRQn);
  /* USER CODE BEGIN USART2_MspInit 1 */

  /* USER CODE END USART2_MspInit 1 */
  }
  else if(uartHandle->Instance==USART3)
  {
  /* USER CODE BEGIN USART3_MspInit 0 */

  /* USER CODE END USART3_MspInit 0 */
    /* USART3 clock enable */
    __HAL_RCC_USART3_CLK_ENABLE();

    __HAL_RCC_GPIOB_CLK_ENABLE();
    /**USART3 GPIO Configuration
    PB10     ------> USART3_TX
    PB11     ------> USART3_RX
    */
    GPIO_InitStruct.Pin = GPIO_PIN_10;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_11;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;  // 添加上拉电阻
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    /* USART3 DMA Init */
    /* USART3_RX Init */
    hdma_usart3_rx.Instance = DMA1_Channel3;
    hdma_usart3_rx.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_usart3_rx.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_usart3_rx.Init.MemInc = DMA_MINC_ENABLE;
    hdma_usart3_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart3_rx.Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
    hdma_usart3_rx.Init.Mode = DMA_NORMAL;
    hdma_usart3_rx.Init.Priority = DMA_PRIORITY_HIGH;
    if (HAL_DMA_Init(&hdma_usart3_rx) != HAL_OK)
    {
      Error_Handler();
    }

    __HAL_LINKDMA(uartHandle,hdmarx,hdma_usart3_rx);

    /* USART3_TX Init */
    hdma_usart3_tx.Instance = DMA1_Channel2;
    hdma_usart3_tx.Init.Direction = DMA_MEMORY_TO_PERIPH;
    hdma_usart3_tx.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_usart3_tx.Init.MemInc = DMA_MINC_ENABLE;
    hdma_usart3_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart3_tx.Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
    hdma_usart3_tx.Init.Mode = DMA_NORMAL;
    hdma_usart3_tx.Init.Priority = DMA_PRIORITY_HIGH;  // 提高优先级
    if (HAL_DMA_Init(&hdma_usart3_tx) != HAL_OK)
    {
      Error_Handler();
    }

    __HAL_LINKDMA(uartHandle,hdmatx,hdma_usart3_tx);

    /* USART3 interrupt Init */
    HAL_NVIC_SetPriority(USART3_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(USART3_IRQn);

    /* USART3 DMA Interrupt Init */
    HAL_NVIC_SetPriority(DMA1_Channel3_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel3_IRQn);
    
    /* USART3 TX DMA Interrupt Init */
    HAL_NVIC_SetPriority(DMA1_Channel2_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel2_IRQn);

  /* USER CODE BEGIN USART3_MspInit 1 */

  /* USER CODE END USART3_MspInit 1 */
  }
}

void HAL_UART_MspDeInit(UART_HandleTypeDef* uartHandle)
{

  if(uartHandle->Instance==USART1)
  {
  /* USER CODE BEGIN USART1_MspDeInit 0 */

  /* USER CODE END USART1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_USART1_CLK_DISABLE();

    /**USART1 GPIO Configuration
    PA9     ------> USART1_TX
    PA10     ------> USART1_RX
    */
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_9|GPIO_PIN_10);

  /* USER CODE BEGIN USART1_MspDeInit 1 */

  /* USER CODE END USART1_MspDeInit 1 */
  }
  else if(uartHandle->Instance==USART2)
  {
  /* USER CODE BEGIN USART2_MspDeInit 0 */

  /* USER CODE END USART2_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_USART2_CLK_DISABLE();

    /**USART2 GPIO Configuration
    PA2     ------> USART2_TX
    PA3     ------> USART2_RX
    */
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_2|GPIO_PIN_3);

    /* USART2 interrupt Deinit */
    HAL_NVIC_DisableIRQ(USART2_IRQn);
  /* USER CODE BEGIN USART2_MspDeInit 1 */

  /* USER CODE END USART2_MspDeInit 1 */
  }
  else if(uartHandle->Instance==USART3)
  {
  /* USER CODE BEGIN USART3_MspDeInit 0 */

  /* USER CODE END USART3_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_USART3_CLK_DISABLE();

    /**USART3 GPIO Configuration
    PB10     ------> USART3_TX
    PB11     ------> USART3_RX
    */
    HAL_GPIO_DeInit(GPIOB, GPIO_PIN_10|GPIO_PIN_11);

    /* USART3 DMA DeInit */
    HAL_DMA_DeInit(uartHandle->hdmarx);

    /* USART3 interrupt Deinit */
    HAL_NVIC_DisableIRQ(USART3_IRQn);
    HAL_NVIC_DisableIRQ(DMA1_Channel3_IRQn);
  /* USER CODE BEGIN USART3_MspDeInit 1 */

  /* USER CODE END USART3_MspDeInit 1 */
  }
}

/* USER CODE BEGIN 1 */


// UART接收半传输完成回调函数
void HAL_UART_RxHalfCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART3)
    {
        // 半传输完成时不处理，等待完整数据或空闲检测
        // 这里什么都不做，继续等待完整的数据传输
    }
}

// 当前数据对应的页面（在DMA接收完成时记录）
static PAGE data_received_page = MAIN;

// UART接收完成回调函数  
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART3)
    {
        // 记录接收到的数据大小（固定3648字节）
        UART3_ByteCount = DATA_BUFFER_SIZE;
        UART3_DataReceived = 1;
        
        // 【关键】记录数据接收时的页面状态
        extern PAGE page;
        data_received_page = page;
        
        // 直接处理数据
        ProcessCollectedData();
        
        // 根据采集模式决定是否重启DMA接收
        if(current_collect_mode == COLLECT_MODE_CONTINUOUS) {
            // 连续采集：清空缓冲区并重启DMA接收
            memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
            
            // 重启DMA接收，如果失败则重新初始化
            if(HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE) != HAL_OK) {
                // DMA重启失败，尝试重新初始化UART3
                MX_USART3_UART_Init();
                HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
            }
            
            // 延时后再发送A2指令，避免指令过于频繁
            // 注意：在中断回调中不使用HAL_Delay，而是设置标志位由主循环处理 
            extern volatile uint8_t need_send_a2_flag;
            need_send_a2_flag = 1;
        }
        else if(current_collect_mode == COLLECT_MODE_SINGLE) {
            // 单次采集：停止接收，切换到空闲状态
            current_collect_mode = COLLECT_MODE_IDLE;
            memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
        }
    }
    else if(huart->Instance == USART1)
    {
        // 启动下一次接收
        static uint8_t rx_buffer[1];
        HAL_UART_Receive_IT(&huart1, rx_buffer, 1);
    }
}




// 处理收集的数据 - 存储原始数据并显示处理后的数据到屏幕
void ProcessCollectedData(void)
{
    // 标记数据处理开始
    extern volatile uint8_t data_processing_done;
    data_processing_done = 0;
    
    // 【关键】先保存并清空UART3_ByteCount，防止DMA回调重新设置后产生竞争
    uint16_t local_byte_count = UART3_ByteCount;
    UART3_ByteCount = 0;
    
    // 检查页面切换锁，如果正在切换页面则跳过本次处理
    extern volatile uint8_t page_switching_lock;
    if(page_switching_lock) {
        data_processing_done = 1; // 恢复标志
        return;
    }
    
    // 检查是否有收集到数据
    if(local_byte_count == 0) {
        data_processing_done = 1; // 恢复标志
        return;
    }
    
    // 检查是否有其他addt指令正在进行，如果有则跳过本次处理
    if(addt_in_progress) {
        data_processing_done = 1; // 恢复标志
        return;
    }
    
    // 检查数据量是否接近3648（允许一定范围内的波动）
    if(local_byte_count < 3640 || local_byte_count > 3648) {
        data_processing_done = 1; // 恢复标志
        return;  // 数据量不符合预期，不处理
    }
    
    // 先保存原始数据到当前组别 (current_group是1-12，需要转换为0-11的数组索引)
    extern uint8_t current_group; // 从menu.c引用当前组别变量
    if(current_group >= 1 && current_group <= 12) {
        SaveSpectrumData(current_group - 1, local_byte_count); // 转换为数组索引 (0-11)，传递字节数
    }
    
    // 检查是否处于放大查看状态
    extern DisplayRange display_range;
    
    // 如果当前处于放大状态（zoom_level > 0），则使用放大数据处理
    if(display_range.zoom_level > 0) {
        // 获取当前放大范围（从t8到t15的值）
        int start_val = display_range.current_values[0];
        int end_val = display_range.current_values[7];
        
        // 调用放大数据处理函数，它会自动处理数据并透传
        ProcessZoomData(start_val, end_val);
    } else {
        // 正常模式：处理并显示整条曲线
        // 舍弃最后3个点，处理前3645个数据点
        uint16_t processedSize = 729;  // 处理后固定得到729个数据点 (3645/5)
        
        // 每5个数据计算平均值
        for (uint16_t i = 0; i < processedSize; i++) {
            uint16_t sum = 0;
            
            // 计算5个数据的和
            for (uint8_t j = 0; j < 5; j++) {
                sum += UART3_DataBuffer[i * 5 + j];
            }
            
            // 计算平均值并存储到处理后的缓冲区
            ProcessedDataBuffer[i] = (uint8_t)(sum / 5);
        }
        
        // 设置透传进行标志
        addt_in_progress = 1;
        
        // 发送addt指令，指定总数据量729个点
        printf("addt s0.id,0,729\xff\xff\xff");
        
        // 基于循环计数的延迟（替代delay_ms）
        for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
            __NOP(); // 空操作，防止编译器优化
        }
        
        // 【修复】统一所有界面都使用正序发送（与初始化保持一致）
        // ProcessedDataBuffer[0] 对应选中范围的起始数据
        // ProcessedDataBuffer[728] 对应选中范围的结束数据
        // 正序发送：屏幕最左边显示起始数据，最右边显示结束数据
        for(uint16_t i = 0; i < 729; i++) {
            putchar(ProcessedDataBuffer[i]);
        }
        
        // 短延迟确保数据传输完成
        for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
            __NOP();
        }
        
        // 发送结束标记
        printf("\x01\xff\xff\xff");
        
        // 最终延迟确保传输完全结束
        for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
            __NOP();
        }
        
        // 清除透传进行标志
        addt_in_progress = 0;
    }
    
    // 标记数据处理完成
    data_processing_done = 1;
}

// 初始化光谱数据组
void InitSpectrumGroups(void)
{
    // 清空RAM存储的数据
    memset(spectrum_data_ram, 0, sizeof(spectrum_data_ram));
    
    // 初始化所有组的信息
    memset(spectrum_groups_info, 0, sizeof(spectrum_groups_info));
}

// 保存光谱数据到指定组
void SaveSpectrumData(uint8_t group_index, uint16_t byte_count)
{
    // 检查组别索引是否有效 (0-11对应组别1-12)
    if(group_index >= 12) {
        return;
    }
    
    // 检查是否有有效数据
    if(byte_count == 0 || byte_count < 3640) {
        return;
    }
    
    // 只有第1组存储在RAM中，其他组存储到Flash
    if(group_index == 0) {
        memcpy(spectrum_data_ram[0], UART3_DataBuffer, DATA_BUFFER_SIZE);
        spectrum_groups_info[group_index].flash_address_offset = 0; // RAM存储，偏移为0
    } else {
        // 其他组需要存储到Flash（暂时跳过Flash实现，只记录信息）
        // TODO: 实现Flash存储功能
        spectrum_groups_info[group_index].flash_address_offset = group_index * (DATA_BUFFER_SIZE / 1024); // 以KB为单位的偏移
    }
    
    // 设置组信息
    spectrum_groups_info[group_index].data_length = byte_count;
    spectrum_groups_info[group_index].is_valid = 1;
    spectrum_groups_info[group_index].timestamp_low = (uint16_t)(HAL_GetTick() & 0xFFFF);
}

// 处理指定组数据并显示到屏幕
void ProcessAndDisplayGroupData(uint8_t group_index)
{
    // 检查是否有其他addt指令正在进行，如果有则跳过
    if(addt_in_progress) {
        return;
    }
    
    // 检查组别索引是否有效
    if(group_index >= 12) {
        return;
    }
    
    // 检查该组是否有有效数据
    if(!spectrum_groups_info[group_index].is_valid || spectrum_groups_info[group_index].data_length < 3640) {
        return;
    }
    
    uint8_t* source_data = NULL;
    
    // 根据存储位置获取数据
    if(group_index == 0) {
        // 第1组RAM存储的数据
        source_data = spectrum_data_ram[0];
    } else {
        // 其他组Flash存储的数据（暂时不实现，返回错误）
        // TODO: 从Flash读取数据
        return;
    }
    
    // 舍弃最后3个点，处理前3645个数据点
    uint16_t processedSize = 729;  // 处理后固定得到729个数据点 (3645/5) 
    
    // 每5个数据计算平均值
    for (uint16_t i = 0; i < processedSize; i++) {
        uint16_t sum = 0;
        
        // 计算5个数据的和
        for (uint8_t j = 0; j < 5; j++) {
            sum += source_data[i * 5 + j];
        }
        
        // 计算平均值并存储到处理后的缓冲区
        ProcessedDataBuffer[i] = (uint8_t)(sum / 5);
    }
    
    // 设置透传进行标志
    addt_in_progress = 1;
    
    // 发送addt指令，指定总数据量729个点
    printf("addt s0.id,0,729\xff\xff\xff");
    
    // 基于循环计数的延迟（替代delay_ms）
    for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
        __NOP(); // 空操作，防止编译器优化
    }
    
    // 【修复】统一所有界面都使用正序发送（与初始化保持一致）
    // ProcessedDataBuffer[0] 对应选中范围的起始数据
    // ProcessedDataBuffer[728] 对应选中范围的结束数据
    // 正序发送：屏幕最左边显示起始数据，最右边显示结束数据
    for(int i = 0; i < 729; i++) {
        putchar(ProcessedDataBuffer[i]);
    }
    
    // 短延迟确保数据传输完成
    for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
        __NOP();
    }
    
    // 发送结束标记
    printf("\x01\xff\xff\xff");
    
    // 最终延迟确保传输完全结束
    for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
        __NOP();
    }
    
    // 清除透传进行标志
    addt_in_progress = 0;
}

// 处理放大数据并透传到屏幕
void ProcessZoomData(int start_val, int end_val)
{
    // 检查是否有其他addt指令正在进行，如果有则跳过
    if(addt_in_progress) {
        return;
    }
    
    // 检查是否有原始数据可用（使用当前组的数据）
    extern uint8_t current_group;
    if(current_group < 1 || current_group > 12) {
        return; // 无效的组别
    }
    
    uint8_t *source_data = NULL;
    
    // 获取数据源
    if(current_group == 1) {
        // 第1组存储在RAM中
        source_data = spectrum_data_ram[0];
    } else {
        // 其他组应该从Flash读取，这里暂时返回（未实现Flash存储）
        return;
    }
    
    // 验证数据源
    if(source_data == NULL) {
        return;
    }
    
    // start_val 和 end_val 是横坐标标签值（像素位，0-3500范围）
    // 这些值直接对应原始数据的索引位置
    // 映射关系：
    //   - 横坐标标签值 = 像素位 = 原始数据索引
    //   - ProcessedDataBuffer[i] 对应 source_data[i*5 到 i*5+4]
    //   - 横坐标值X 对应 source_data[X]
    int pixel_start_val = start_val;
    int pixel_end_val = end_val;
    
    // 确保像素值在有效范围内（0-3644，因为只使用前3645个数据）
    if(pixel_start_val < 0) pixel_start_val = 0;
    if(pixel_end_val > 3644) pixel_end_val = 3644;
    if(pixel_start_val > pixel_end_val) {
        // 交换顺序
        int temp = pixel_start_val;
        pixel_start_val = pixel_end_val;
        pixel_end_val = temp;
    }
    
    // 【修复】直接使用传入的像素值作为数据索引
    // current_values 应该始终存储像素索引值，不需要在这里再映射
    int start_index = pixel_start_val;
    int end_index = pixel_end_val;
    
    // 边界检查（注意：实际只使用前3645个数据）
    if(start_index < 0) start_index = 0;
    if(end_index >= 3645) end_index = 3644;
    if(start_index >= end_index) return;
    
    // 计算选中范围的数据点数
    int selected_points = end_index - start_index + 1;
    
    // 清空处理缓冲区
    memset(ProcessedDataBuffer, 0, PROCESSED_DATA_SIZE);
    
    // 【修复】不要在填充时倒序，只在发送时倒序（避免双重倒序）
    // ProcessedDataBuffer 始终按正序填充：
    //   - ProcessedDataBuffer[0] = 选中范围的起始数据
    //   - ProcessedDataBuffer[728] = 选中范围的结束数据
    // 发送时根据页面类型决定是否倒序发送
    
    if(selected_points <= 729) {
        // 情况1：选中点数不足729个，需要数据插值扩展
        
        // 计算需要补充的点数，使总数达到729
        int needed_points = 729;
        
        // 使用线性插值扩展数据（正序填充）
        for(int i = 0; i < needed_points; i++) {
            // 计算在原始选中范围内的浮点索引
            float original_index = start_index + (float)i * (selected_points - 1) / (needed_points - 1);
            int base_index = (int)original_index;
            float fraction = original_index - base_index;
            
            // 边界检查
            if(base_index >= end_index) {
                ProcessedDataBuffer[i] = source_data[end_index];
            } else if(base_index + 1 >= 3648) {
                ProcessedDataBuffer[i] = source_data[base_index];
            } else {
                // 线性插值
                ProcessedDataBuffer[i] = (uint8_t)(
                    source_data[base_index] * (1.0f - fraction) + 
                    source_data[base_index + 1] * fraction
                );
            }
        }
    } else {
        // 情况2：选中点数超过729个，需要压缩数据
        
        // 使用平均值压缩方法
        float compression_ratio = (float)selected_points / 729.0f;
        
        for(int i = 0; i < 729; i++) {
            // 计算当前输出点对应的原始数据范围
            float start_float = start_index + i * compression_ratio;
            float end_float = start_index + (i + 1) * compression_ratio;
            
            int range_start = (int)start_float;
            int range_end = (int)end_float;
            
            // 边界检查
            if(range_start >= 3648) range_start = 3647;
            if(range_end >= 3648) range_end = 3647;
            if(range_start == range_end) range_end = range_start + 1;
            if(range_end >= 3648) range_end = 3647;
            
            // 计算该范围内的平均值
            uint32_t sum = 0;
            int count = 0;
            
            for(int j = range_start; j <= range_end && j < 3648; j++) {
                sum += source_data[j];
                count++;
            }
            
            if(count > 0) {
                ProcessedDataBuffer[i] = (uint8_t)(sum / count);
            } else {
                ProcessedDataBuffer[i] = 0;
            }
        }
    }
    
    // 设置透传进行标志
    addt_in_progress = 1;
    
    // 发送addt指令，指定总数据量729个点
    printf("addt s0.id,0,729\xff\xff\xff");
    
    // 基于循环计数的延迟（替代delay_ms）
    for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
        __NOP(); // 空操作，防止编译器优化
    }
    
    // 【修复】统一所有界面都使用正序发送（与初始化保持一致）
    // ProcessedDataBuffer[0] 对应选中范围的起始数据
    // ProcessedDataBuffer[728] 对应选中范围的结束数据
    // 正序发送：屏幕最左边显示起始数据，最右边显示结束数据
    for(int i = 0; i < 729; i++) {
        putchar(ProcessedDataBuffer[i]);
    }
    
    // 短延迟确保数据传输完成
    for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
        __NOP();
    }
    
    // 发送结束标记
    printf("\x01\xff\xff\xff");
    
    // 最终延迟确保传输完全结束
    for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
        __NOP();
    }
    
    // 清除透传进行标志
    addt_in_progress = 0;
}

// 动态配置USART2波特率的函数
void USART_Config(uint32_t baud)
{
	UART_HandleTypeDef *huart = &huart2;
	
	// 禁用USART2
	HAL_UART_DeInit(huart);
	
	// 重新配置波特率
	huart->Instance = USART2;
	huart->Init.BaudRate = baud;
	huart->Init.WordLength = UART_WORDLENGTH_8B;
	huart->Init.StopBits = UART_STOPBITS_1;
	huart->Init.Parity = UART_PARITY_NONE;
	huart->Init.Mode = UART_MODE_TX_RX;
	huart->Init.HwFlowCtl = UART_HWCONTROL_NONE;
	huart->Init.OverSampling = UART_OVERSAMPLING_16;
	
	// 重新初始化USART2
	if (HAL_UART_Init(huart) != HAL_OK)
	{
		Error_Handler();
	}
     HAL_UART_Receive_IT(huart, UART2_RxBuffer, 1);
}

/* USER CODE END 1 */
