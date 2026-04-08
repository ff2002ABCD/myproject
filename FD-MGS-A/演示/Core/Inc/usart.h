/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    usart.h
  * @brief   This file contains all the function prototypes for
  *          the usart.c file
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
#ifndef __USART_H__
#define __USART_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
/* USER CODE END Includes */

extern UART_HandleTypeDef huart1;

extern UART_HandleTypeDef huart2;

extern UART_HandleTypeDef huart3;

/* USER CODE BEGIN Private defines */
// UART缓冲区
extern uint8_t UART2_RxBuffer[4];

// UART通信状态标志
extern uint8_t UART3_DataReceived;  // 接收到数据标志
extern uint16_t UART3_ByteCount;    // 接收到的字节数

// 采集模式定义
typedef enum {
    COLLECT_MODE_IDLE = 0,      // 空闲状态
    COLLECT_MODE_SINGLE,        // 单次采集
    COLLECT_MODE_CONTINUOUS     // 连续采集
} CollectMode_t;

extern CollectMode_t current_collect_mode;
extern CollectMode_t previous_collect_mode_before_int_time;  // 用于记录进入积分时间选择前的采集模式

// 数据缓冲区定义
#define DATA_BUFFER_SIZE 3648 // 原始数据缓冲区大小
#define PROCESSED_DATA_SIZE 729 // 处理后数据大小 (3645/5 = 729)
#define MAX_SPECTRUM_GROUPS 1     // 只保留1组RAM存储以节省内存
#define EXTERNAL_STORAGE_GROUPS 11 // 其余11组使用外部存储（如Flash）

// 光谱数据存储结构（优化后）
typedef struct {
    uint16_t data_length;                    // 实际数据长度
    uint8_t is_valid;                        // 数据是否有效
    uint16_t timestamp_low;                  // 时间戳低16位（节省空间）
    uint16_t flash_address_offset;           // Flash地址偏移（相对地址，节省空间）
} SpectrumGroupInfo;

extern uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE]; // 原始数据缓冲区
extern uint8_t ProcessedDataBuffer[PROCESSED_DATA_SIZE]; // 处理后数据缓冲区

// 只保留1组RAM存储的光谱数据以节省内存
extern uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
// 所有组的信息（RAM中）
extern SpectrumGroupInfo spectrum_groups_info[12];

// DMA相关定义
extern DMA_HandleTypeDef hdma_usart3_rx; // UART3 DMA接收句柄

// DMA半传输中断禁用宏
#ifndef DMA_IT_HT
#define DMA_IT_HT     ((uint32_t)0x0004)
#endif

// 控制函数声明
void ProcessCollectedData(void);     // 处理收集到的数据并显示到屏幕
void SaveSpectrumData(uint8_t group_index, uint16_t byte_count); // 保存光谱数据到指定组
void InitSpectrumGroups(void);       // 初始化光谱数据组
void ProcessAndDisplayGroupData(uint8_t group_index); // 处理指定组数据并显示到屏幕
void UART3_Send_Command(uint8_t cmd); // 发送命令到UART3
void ProcessZoomData(int start_val, int end_val); // 处理放大数据并透传到屏幕

// 连续采集控制标志
extern volatile uint8_t need_send_a2_flag;

// 透传互斥标志，防止多个addt指令同时发送
extern volatile uint8_t addt_in_progress;

// 数据处理完成标志，防止在数据处理期间发送新的A2命令
extern volatile uint8_t data_processing_done;

// 页面切换锁标志，在切换页面时暂停数据处理
extern volatile uint8_t page_switching_lock;

// UART3 DMA接收相关函数
void UART3_DMA_Start(void);          // 启动UART3 DMA接收
/* USER CODE END Private defines */

void MX_USART1_UART_Init(void);
void MX_USART2_UART_Init(void);
void MX_USART3_UART_Init(void);

/* USER CODE BEGIN Prototypes */
void USART_Config(uint32_t baud);  // 动态配置USART2波特率的函数
/* USER CODE END Prototypes */

#ifdef __cplusplus
}
#endif

#endif /* __USART_H__ */

