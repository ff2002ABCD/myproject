#include "function.h"
#include "tim.h"
#include "delay.h"
#include "usart.h"
#include "menu.h"
#include "encoder.h"  // 添加编码器头文件
#include <string.h>
#include <stdio.h>
#include "main.h"
#include "ch376.h"
#include <math.h>

// 变量定义
float Current = 0;  // 电流值变量
uint8_t current_page = SPECTRUM_MEASURE; // 默认为光谱测量页面

// 曲线显示相关变量
uint32_t last_curve_update = 0; // 最后一次曲线更新时间

// 电流控制函数实现
void Current_control(void)
{
	// 电流控制逻辑实现
	// 这里根据实际需求实现电流控制功能
}

/**
 * @brief 光谱测量页面显示
 * 在直接转发模式下，这个函数不再需要处理缓冲区数据，仅作状态显示
 */
void Display_Spectrum_Curve(void)
{
    // 在直接转发模式下，数据已经通过UART中断直接转发到屏幕
    // 只需显示收到的字节数
    printf("t0.txt=\"%d\"\xff\xff\xff", UART3_ByteCount);
}
	
/**
 * @brief 标定页面显示
 */
void Display_Calibration_Curve(void)
{
    // 与光谱测量页面使用相同的处理逻辑
    Display_Spectrum_Curve();
}

/**
 * @brief 查询导出页面显示
 */
void Display_Query_Curve(void)
{
    // 显示收到的字节数
    printf("t0.txt=\"%d\"\xff\xff\xff", UART3_ByteCount);
    
    // 进入查询导出界面时自动执行addt透传，显示存储的曲线
    extern SpectrumGroupInfo spectrum_groups_info[12];
    extern uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
    extern volatile uint8_t addt_in_progress;
    
    // 检查第一组RAM数据是否有效且不在进行其他addt操作
    if(spectrum_groups_info[0].is_valid && spectrum_groups_info[0].data_length >= 3640 && !addt_in_progress) {
        // 标记addt正在进行，防止冲突
        addt_in_progress = 1;
        
        // 发送addt透传指令，将数据显示到s0波形控件
        printf("addt s0.id,0,729\xff\xff\xff");
        
        // 基于循环计数的延迟（等待屏幕响应）
        for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
            __NOP(); // 空操作，防止编译器优化
        }
        
        // 透传729个数据点（从3648字节的原始数据中等间隔采样）
        // 注意：需要先计算平均值再发送
        uint8_t* source_data = spectrum_data_ram[0];
        
        // 先处理数据（每5个原始数据计算平均值，得到729个点）
        extern uint8_t ProcessedDataBuffer[];
        for(int i = 0; i < 729; i++) {
            uint16_t sum = 0;
            for(uint8_t j = 0; j < 5; j++) {
                int src_index = i * 5 + j;
                if(src_index < DATA_BUFFER_SIZE) {
                    sum += source_data[src_index];
                }
            }
            ProcessedDataBuffer[i] = (uint8_t)(sum / 5);
        }
        
        // 查询导出页面：正序发送处理后的729个数据点
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
        
        // 完成后重置标志
        addt_in_progress = 0;
    }
}

void system_init()
{
	// 初始化编码器
	encoder_init();
	
//	HAL_DAC_SetValue(&hdac,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00*1.283/3.30);
//	if(*(__IO uint32_t*)0x08009000!=0xffffffff) k= *(__IO uint32_t*)0x08009000/100.000;
	Current_control();
	Current=100;
	HAL_TIM_Base_Start_IT(&htim3);
	page=MAIN;
	printf("page main\xff\xff\xff");
	
	// 重置组别数据
	reset_group_data();
	
	// 初始化12组光谱数据存储
	InitSpectrumGroups();
	
	// 进入光谱测量页面并初始化曲线控件
	printf("page measure\xff\xff\xff");

	// 只初始化s0曲线控件
	printf("cle s0.id,255\xff\xff\xff");
	printf("ref s0.id\xff\xff\xff");
	
	// 设置s0控件的X坐标为62，使曲线从62位置开始
	printf("s0.x=62\xff\xff\xff");
	
	// 删除了系统启动时自动读取标定文件的代码
	// 标定文件只在用户手动按下"导入标定"按钮时读取
	
	// 返回main
	printf("page main\xff\xff\xff");
}

/**
 * @brief 查询导出页面初始化
 */
void query_export_page_init(void)
{
    // 设置默认光标为标定按钮
    cursor_spectrum = CURSOR_CALIBRATION;
    printf("paging.bco=61277\xff\xff\xff");  // 高亮标定按钮
    
    // 确保其他按钮为正常状态
    printf("zoom.bco=50779\xff\xff\xff");    // zoom按钮正常色
    printf("reset1.bco=50779\xff\xff\xff");  // auto_scale按钮正常色
    printf("reset2.bco=50779\xff\xff\xff");  // reset_zoom按钮正常色
    printf("output.bco=50779\xff\xff\xff");  // export_usb按钮正常色
    printf("coeff.bco=50779\xff\xff\xff");   // export_coeff按钮正常色
    
    // 初始化Y轴强度标签为默认值10000-60000
    for(int i = 0; i < 6; i++) {
        uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
    }
    
    // 【关键修复】初始化横坐标标签（根据全局wavelength_display_enabled标志）
    // 需要声明外部全局变量
    extern uint8_t wavelength_display_enabled;
    
    // 检查是否启用波长显示模式且有有效标定参数
    if(wavelength_display_enabled && saved_calib_params.is_valid) {
        // 波长显示模式
        printf("vis z1,0\xff\xff\xff");    // z1不可见（像素位）
        printf("vis z2,1\xff\xff\xff");    // z2可见（波长）
        
        // 【关键修复】更新t8-t15为波长值（显示波长，但存储像素值）
        for(int i = 0; i < 8; i++) {
            int pixel_val = DEFAULT_T_VALUES[i]; // 【修复】使用标准像素范围（0-3500）
            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【关键】存储像素值！
        }
    } else {
        // 像素位显示模式（无标定或用户切换为像素显示）
        printf("vis z1,1\xff\xff\xff");    // z1可见（像素位）
        printf("vis z2,0\xff\xff\xff");    // z2不可见（波长）
        
        // 更新t8-t15为像素值
        for(int i = 0; i < 8; i++) {
            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
            display_range.current_values[i] = DEFAULT_T_VALUES[i];
        }
    }
    
    // 重置放大相关状态
    display_range.is_selecting = 0;
    display_range.first_selected = -1;
    display_range.second_selected = -1;
    display_range.zoom_level = 0;
    
    // 进入查询导出界面时自动执行addt透传，显示存储的曲线
    extern SpectrumGroupInfo spectrum_groups_info[12];
    extern uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
    extern volatile uint8_t addt_in_progress;
    
    // 检查第一组RAM数据是否有效
    if(spectrum_groups_info[0].is_valid && spectrum_groups_info[0].data_length >= 3640 && !addt_in_progress) {
        // 标记addt正在进行，防止冲突
        addt_in_progress = 1;
        
        // 发送addt透传指令，将数据显示到s0波形控件
        printf("addt s0.id,0,729\xff\xff\xff");
        
        // 基于循环计数的延迟（等待屏幕响应）
        for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
            __NOP(); // 空操作，防止编译器优化
        }
        
        // 透传729个数据点（从3648字节的原始数据中等间隔采样）
        // 注意：需要先计算平均值再发送
        uint8_t* source_data = spectrum_data_ram[0];
        
        // 先处理数据（每5个原始数据计算平均值，得到729个点）
        extern uint8_t ProcessedDataBuffer[];
        for(int i = 0; i < 729; i++) {
            uint16_t sum = 0;
            for(uint8_t j = 0; j < 5; j++) {
                int src_index = i * 5 + j;
                if(src_index < DATA_BUFFER_SIZE) {
                    sum += source_data[src_index];
                }
            }
            ProcessedDataBuffer[i] = (uint8_t)(sum / 5);
        }
        
        // 查询导出页面初始化：正序发送处理后的729个数据点
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
        
        // 完成后重置标志
        addt_in_progress = 0;
    }
}
