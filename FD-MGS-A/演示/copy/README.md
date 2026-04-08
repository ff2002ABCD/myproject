# STM32F103C8T6 双UART数据转发器项目

## 项目概述

本项目是一个基于STM32F103C8T6微控制器的双UART数据转发器，主要功能是接收来自上位机的命令，转发给H750设备，并将H750返回的数据转发回上位机。项目支持TCD1304线性图像传感器的数据采集和处理。

## 硬件配置

### 微控制器
- **型号**: STM32F103C8T6
- **封装**: LQFP48
- **时钟配置**: 
  - 外部晶振: 8MHz HSE
  - PLL倍频: 9倍 (目标72MHz，当前配置为8MHz)
  - 系统时钟: 8MHz

### GPIO引脚配置

#### UART1 (与H750通信)
- **PA9**: USART1_TX (推挽输出，高速)
- **PA10**: USART1_RX (浮空输入)
- **波特率**: 921600
- **配置**: 8位数据位，1位停止位，无校验

#### UART2 (与上位机通信)  
- **PA2**: USART2_TX
- **PA3**: USART2_RX
- **波特率**: 256000
- **配置**: 8位数据位，1位停止位，无校验

#### UART3 (与上位机通信，与UART2功能相同)
- **PB10**: USART3_TX
- **PB11**: USART3_RX
- **波特率**: 256000
- **配置**: 8位数据位，1位停止位，无校验

#### 调试接口
- **PA13**: SWD-IO
- **PA14**: SWD-CLK

### DMA配置

#### UART1 DMA
- **接收**: DMA1_Channel5 (高优先级，正常模式)
- **发送**: DMA1_Channel4 (中等优先级，正常模式)

#### UART2 DMA
- **接收**: DMA1_Channel6 (低优先级，正常模式)
- **发送**: DMA1_Channel7 (低优先级，正常模式)

#### UART3 DMA
- **接收**: DMA1_Channel3 (低优先级，正常模式)
- **发送**: DMA1_Channel2 (低优先级，正常模式)

## 软件架构

### 主要数据结构

```c
// 缓冲区定义
#define TCD1304_PIXEL_COUNT 3648    // TCD1304像素数量
#define UART_RX_BUFFER_SIZE 3648    // 接收缓冲区大小
#define UART_TX_BUFFER_SIZE 3648    // 发送缓冲区大小
#define PROCESSED_DATA_SIZE 729     // 处理后数据大小 (3645/5)

// 全局变量
uint8_t UART1_RxBuffer[UART_RX_BUFFER_SIZE];  // UART1接收缓冲区
uint8_t UART1_TxBuffer[UART_RX_BUFFER_SIZE];  // UART1发送缓冲区
uint8_t UART2_RxChar;                         // UART2单字符接收
uint8_t UART3_RxChar;                         // UART3单字符接收
uint8_t CmdMode;                              // 当前命令模式
```

### 通信协议

#### 命令格式
项目支持以下命令字：

##### 数据采集模式命令
- **0xA1**: 请求原始数据模式
- **0xA2**: 请求8位AD数据模式 (默认)
- **0xA4**: 请求处理数据模式

##### 曝光时间设置命令
- **0xB1 - 0xBF**: 设置不同的曝光时间等级
  - 0xB1: 最短曝光时间
  - 0xBF: 最长曝光时间

#### 数据流程
1. 上位机通过UART2或UART3发送命令到STM32
2. STM32接收命令后立即转发给H750 (UART1)
3. STM32启动DMA接收，等待H750返回数据
4. 接收完成后，STM32将数据同时通过UART2和UART3发送给上位机

### 关键函数说明

#### 命令处理函数
```c
void ProcessCommand(uint8_t cmd)
```
- 解析接收到的命令
- 转发命令到H750
- 重新启动DMA接收

#### UART接收事件回调
```c
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
```
- 处理UART1的DMA接收完成事件
- 快速复制数据并转发到UART2
- 重启DMA接收准备下次数据

#### UART接收完成回调
```c
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
```
- 处理UART2和UART3的单字符接收
- 调用命令处理函数
- 重启单字符接收

## 数据处理机制

### 高速数据传输优化
1. **DMA传输**: 使用DMA减少CPU负担
2. **中断禁用**: 数据复制时禁用中断防止数据污染
3. **快速复制**: 使用memcpy进行快速数据复制
4. **容错机制**: 超时重传和逐字节发送备选方案

### 缓冲区管理
- 双缓冲区设计：接收缓冲区和发送缓冲区分离
- 大容量缓冲区：支持3648字节的大数据包传输
- 内存保护：使用中断控制确保数据完整性

## 中断优先级配置

| 中断源 | 优先级 | 说明 |
|--------|--------|------|
| DMA1_Channel5 (UART1_RX) | 高 | 关键数据接收 |
| DMA1_Channel4 (UART1_TX) | 中 | 命令发送 |
| DMA1_Channel6 (UART2_RX) | 低 | 命令接收 |
| DMA1_Channel7 (UART2_TX) | 低 | 数据发送 |
| DMA1_Channel3 (UART3_RX) | 低 | 命令接收 |
| DMA1_Channel2 (UART3_TX) | 低 | 数据发送 |
| USART1_IRQn | 0 | UART1中断 |
| USART2_IRQn | 0 | UART2中断 |
| USART3_IRQn | 0 | UART3中断 |

## 性能特点

### 传输性能
- **UART1**: 921600 bps，用于高速数据传输
- **UART2**: 256000 bps，用于命令和数据回传
- **UART3**: 256000 bps，用于命令和数据回传 (与UART2功能相同)
- **数据包大小**: 最大3648字节
- **传输延迟**: < 1ms (DMA + 快速复制)

### 可靠性设计
- **错误处理**: 完善的HAL错误处理机制
- **超时保护**: 2000ms发送超时，100ms单字节超时
- **重传机制**: 发送失败时自动重试
- **数据完整性**: 中断保护确保数据不被污染

## 编译和调试

### 开发环境
- **IDE**: Keil MDK-ARM V5.32
- **HAL库**: STM32Cube FW_F1 V1.8.6
- **调试接口**: SWD

### 编译配置
- **优化等级**: 6 (平衡优化)
- **堆大小**: 0x200 (512字节)
- **栈大小**: 0x400 (1024字节)

### 调试配置
- 使用DEBUG_UART (huart2) 进行调试输出
- SWD接口支持在线调试
- 错误处理函数进入无限循环便于调试

## 使用说明

### 初始化序列
1. 系统启动后自动发送0xA2命令初始化H750
2. 启动UART1 DMA接收等待数据
3. 启动UART2和UART3中断接收等待命令

### 命令发送流程
1. 上位机发送命令字节到UART2或UART3
2. STM32接收命令并转发到H750
3. 等待H750数据返回
4. 将接收到的数据同时转发给UART2和UART3连接的上位机

### 故障排除
- **通信异常**: 检查波特率配置和线路连接
- **数据丢失**: 检查DMA配置和缓冲区大小
- **响应超时**: 检查H750设备状态和命令格式

## 项目文件结构

```
copy/
├── Core/
│   ├── Inc/
│   │   ├── main.h                 # 主头文件，包含宏定义
│   │   ├── stm32f1xx_it.h        # 中断处理头文件
│   │   └── stm32f1xx_hal_conf.h  # HAL配置
│   └── Src/
│       ├── main.c                 # 主程序文件
│       ├── stm32f1xx_it.c        # 中断处理函数
│       ├── stm32f1xx_hal_msp.c   # MSP初始化
│       └── system_stm32f1xx.c    # 系统初始化
├── Drivers/                       # STM32 HAL驱动库
├── MDK-ARM/                       # Keil项目文件
└── copy.ioc                       # STM32CubeMX配置文件
```

## 技术特色

1. **高效数据转发**: 基于DMA的零拷贝数据传输
2. **双波特率设计**: 针对不同用途优化的波特率配置
3. **实时响应**: 中断驱动的命令处理机制
4. **大数据量支持**: 支持3648字节的图像数据传输
5. **健壮性**: 完善的错误处理和恢复机制

这个项目特别适用于需要高速、可靠的串口数据转发应用，特别是图像传感器数据采集系统。 