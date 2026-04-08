/**
 * @file demo_data.h
 * @brief 演示功能数据头文件
 * @note 包含预存的光谱演示数据，用于演示功能显示
 */

#ifndef __DEMO_DATA_H
#define __DEMO_DATA_H

#include "main.h"

// 演示数据大小（与DATA_BUFFER_SIZE一致）
#define DEMO_DATA_SIZE 3648

// 演示光谱数据（存储在Flash中）
// 数据来源：DATA.csv的光强度灰值列，已转换为uint8_t格式（0-255）
// 原始数据范围0-31058，映射到0-255
extern const uint8_t demo_spectrum_data[DEMO_DATA_SIZE];

#endif /* __DEMO_DATA_H */
