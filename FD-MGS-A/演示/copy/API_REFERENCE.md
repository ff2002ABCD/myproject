# STM32F103C8T6 双UART数据转发器 API参考

## 目录
1. [命令接口](#1-命令接口)
2. [数据格式](#2-数据格式)
3. [错误代码](#3-错误代码)
4. [通信协议](#4-通信协议)
5. [示例代码](#5-示例代码)
6. [故障排除](#6-故障排除)

## 1. 命令接口

### 1.1 数据采集命令

#### 0xA1 - 原始数据模式
```
命令: 0xA1
功能: 请求获取TCD1304的原始数据
参数: 无
返回: 变长数据包 (取决于H750处理器配置)
响应时间: < 100ms
```

**使用场景**: 需要获取未经处理的原始传感器数据时使用。

#### 0xA2 - 8位AD数据模式 (默认)
```
命令: 0xA2
功能: 请求获取8位精度的AD转换数据
参数: 无
返回: 3648字节数据包 (对应TCD1304的3648个像素)
响应时间: < 100ms
```

**使用场景**: 标准图像采集应用，平衡了数据精度和传输效率。

#### 0xA4 - 处理数据模式
```
命令: 0xA4
功能: 请求获取经过处理的数据 (5点平均)
参数: 无
返回: 729字节数据包 (3645/5 = 729个处理后的数据点)
响应时间: < 100ms
```

**使用场景**: 需要降采样数据或减少数据传输量时使用。

### 1.2 曝光控制命令

#### 0xB1 - 曝光级别1 (最短)
```
命令: 0xB1
功能: 设置最短曝光时间
参数: 无
返回: 状态确认或数据 (取决于H750实现)
响应时间: < 50ms
```

#### 0xB2 - 曝光级别2
```
命令: 0xB2
功能: 设置曝光级别2
参数: 无
返回: 状态确认或数据
响应时间: < 50ms
```

#### ... 0xB3 至 0xBE - 曝光级别3-14

#### 0xBF - 曝光级别15 (最长)
```
命令: 0xBF
功能: 设置最长曝光时间
参数: 无
返回: 状态确认或数据
响应时间: < 50ms
```

**曝光级别说明**:
- 0xB1: 适用于强光环境
- 0xB8: 适用于标准光照条件
- 0xBF: 适用于弱光环境

## 2. 数据格式

### 2.1 命令数据包格式

#### 上位机到STM32 (UART2)
```
+--------+
| CMD    | 1字节: 命令字 (0xA1, 0xA2, 0xA4, 0xB1-0xBF)
+--------+
```

#### STM32到H750 (UART1)
```
+--------+
| CMD    | 1字节: 转发的命令字
+--------+
```

### 2.2 响应数据包格式

#### H750到STM32 (UART1)
```
+--------+--------+--------+--------+
| DATA0  | DATA1  | DATA2  | DATAn  | n字节: 响应数据
+--------+--------+--------+--------+
```

#### STM32到上位机 (UART2)
```
+--------+--------+--------+--------+
| DATA0  | DATA1  | DATA2  | DATAn  | n字节: 转发的响应数据
+--------+--------+--------+--------+
```

### 2.3 数据类型定义

#### 8位AD数据 (0xA2模式)
```c
typedef struct {
    uint8_t pixel_data[3648];  // 每个像素一个字节
} ADC_Data_8bit_t;
```

#### 处理数据 (0xA4模式)
```c
typedef struct {
    uint8_t processed_data[729];  // 每5个像素平均后的数据
} Processed_Data_t;
```

## 3. 错误代码

### 3.1 系统错误
| 错误代码 | 说明 | 处理方法 |
|----------|------|----------|
| HAL_ERROR | HAL库函数调用失败 | 重启系统 |
| HAL_BUSY | UART或DMA正忙 | 等待后重试 |
| HAL_TIMEOUT | 通信超时 | 检查连接，重试 |

### 3.2 通信错误
| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无响应 | H750未连接或故障 | 检查H750状态 |
| 数据丢失 | DMA配置错误 | 重启DMA传输 |
| 乱码 | 波特率不匹配 | 检查波特率配置 |

## 4. 通信协议

### 4.1 协议特性
- **通信方式**: 异步串口通信
- **数据传输**: 大端字节序
- **流控制**: 无硬件流控
- **错误检测**: 软件超时检测

### 4.2 时序要求
```
上位机命令 → STM32接收 → 转发H750 → 等待响应 → 转发上位机
    ↓            ↓           ↓           ↓           ↓
   <1ms        <10μs       <1ms       <100ms      <50ms
```

### 4.3 并发控制
- 同一时间只能处理一个命令
- 新命令会中断当前传输
- DMA传输期间禁用相关中断

## 5. 示例代码

### 5.1 上位机发送命令 (Python示例)
```python
import serial
import time

# 配置串口
ser = serial.Serial('COM3', 256000, timeout=2)

def send_command(cmd):
    """发送命令并接收响应"""
    # 发送命令
    ser.write(bytes([cmd]))
    
    # 等待响应
    if cmd == 0xA2:
        # 8位AD数据模式，期望3648字节
        data = ser.read(3648)
    elif cmd == 0xA4:
        # 处理数据模式，期望729字节
        data = ser.read(729)
    else:
        # 其他命令，读取可用数据
        time.sleep(0.1)
        data = ser.read(ser.in_waiting)
    
    return data

# 示例：获取8位AD数据
adc_data = send_command(0xA2)
print(f"接收到 {len(adc_data)} 字节数据")

# 示例：设置曝光级别
send_command(0xB5)  # 设置中等曝光
processed_data = send_command(0xA4)  # 获取处理后数据
```

### 5.2 数据解析示例
```python
def parse_adc_data(data):
    """解析8位AD数据"""
    if len(data) != 3648:
        raise ValueError("数据长度错误")
    
    pixels = []
    for byte in data:
        pixels.append(byte)
    
    return pixels

def parse_processed_data(data):
    """解析处理后数据"""
    if len(data) != 729:
        raise ValueError("数据长度错误")
    
    processed_pixels = []
    for byte in data:
        processed_pixels.append(byte)
    
    return processed_pixels
```

### 5.3 C++示例 (Qt)
```cpp
#include <QSerialPort>
#include <QByteArray>

class STM32Interface {
private:
    QSerialPort* serialPort;
    
public:
    STM32Interface() {
        serialPort = new QSerialPort();
        serialPort->setPortName("COM3");
        serialPort->setBaudRate(256000);
        serialPort->setDataBits(QSerialPort::Data8);
        serialPort->setParity(QSerialPort::NoParity);
        serialPort->setStopBits(QSerialPort::OneStop);
    }
    
    QByteArray sendCommand(uint8_t cmd) {
        if (!serialPort->isOpen()) {
            serialPort->open(QIODevice::ReadWrite);
        }
        
        // 发送命令
        QByteArray command;
        command.append(cmd);
        serialPort->write(command);
        
        // 等待响应
        serialPort->waitForReadyRead(2000);
        return serialPort->readAll();
    }
    
    QVector<uint8_t> getADCData() {
        QByteArray data = sendCommand(0xA2);
        QVector<uint8_t> pixels;
        
        for (int i = 0; i < data.size(); i++) {
            pixels.append(static_cast<uint8_t>(data[i]));
        }
        
        return pixels;
    }
};
```

## 6. 故障排除

### 6.1 常见问题

#### 问题1: 无法建立通信
**症状**: 发送命令后无任何响应

**可能原因**:
- 串口未正确打开
- 波特率配置错误
- STM32未上电或复位

**解决方案**:
1. 检查串口配置: 256000bps, 8N1
2. 确认STM32供电正常
3. 检查串口线缆连接

#### 问题2: 数据不完整
**症状**: 接收到的数据长度小于预期

**可能原因**:
- 传输超时
- H750设备异常
- DMA缓冲区溢出

**解决方案**:
1. 增加接收超时时间
2. 重启STM32设备
3. 检查H750设备状态

#### 问题3: 数据内容异常
**症状**: 接收到的数据全为0或乱码

**可能原因**:
- H750设备故障
- TCD1304传感器问题
- 曝光参数不当

**解决方案**:
1. 调整曝光时间 (0xB1-0xBF)
2. 检查传感器连接
3. 重新初始化H750

### 6.2 调试方法

#### 使用示波器检查信号
```
UART2_TX (PA2): 检查命令发送波形
UART2_RX (PA3): 检查数据接收波形
UART1_TX (PA9): 检查到H750的命令转发
UART1_RX (PA10): 检查H750的数据响应
```

#### 添加调试输出
```c
// 在main.c中添加调试代码
void debug_print(const char* msg) {
    HAL_UART_Transmit(&huart2, (uint8_t*)msg, strlen(msg), 100);
}

// 在关键位置添加调试信息
debug_print("Command received: 0xA2\r\n");
debug_print("DMA transfer completed\r\n");
```

### 6.3 性能监控

#### 传输速度测量
```python
import time

start_time = time.time()
data = send_command(0xA2)
end_time = time.time()

transfer_time = end_time - start_time
data_rate = len(data) / transfer_time
print(f"传输速度: {data_rate:.0f} 字节/秒")
```

#### 数据完整性检查
```python
def verify_data_integrity(data, expected_length):
    """验证数据完整性"""
    if len(data) != expected_length:
        print(f"数据长度错误: 期望{expected_length}, 实际{len(data)}")
        return False
    
    # 检查数据范围 (0-255)
    for i, byte in enumerate(data):
        if byte < 0 or byte > 255:
            print(f"位置{i}数据异常: {byte}")
            return False
    
    return True
```

这份API参考文档提供了完整的接口说明和使用示例，便于用户快速集成和使用该数据转发器系统。 