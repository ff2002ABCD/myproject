#include "menu.h"
#include "function.h"
#include "usart.h"   // 使用UART进行串口通信
#include "ch376.h"   // 使用CH376进行USB通信
#include "FILE_SYS.h" // 使用CH376文件系统函数
#include <stdio.h>
#include <stdlib.h>  // 使用rand()函数
#include <math.h>    // 使用fabs()函数
#include <string.h>  // 使用memset()函数
#include "delay.h"   // 使用delay_ms()函数
#include "key.h"     // 使用key.h中的按键处理函数
extern int fputc(int ch, FILE* file);

// 发送命令到UART3
void UART3_Send_Command(uint8_t cmd);

// 自动应用校准函数声明
void auto_apply_calibration(void);

// 外部定义的按键标志
extern KEY_TYPE g_KeyActionFlag;

PAGE page = MAIN;
CURSOR_MAIN cursor_main = CALIBO;  // 初始化为CALIBO
CURSOR_SPECTRUM cursor_spectrum;
CURSOR_CALIBRATION1 cursor_calibration1;
CALIB_STATE calib_state;
DisplayRange display_range;
SpectrumData spectrum_data;
IntegrationTime current_int_time = INT_TIME_1MS;
uint8_t cursor_int_time = 1; // 默认选择1ms (a1)
uint8_t cursor_wavelength = 0; // 默认选择第一个波长
uint8_t current_group = 1; // 当前波段从1开始
uint8_t saved_groups = 0; // 保存的波段数量为0

// 查看坐标状态
ViewCoordinateState view_coord_state = {0, 62, 1, -1, -1}; // 初始位置设为中间 (62+791)/2 ≈ 427, saved_screen_position和saved_full_curve_pixel初始化为-1

// 定义校准参数结构体
CalibrationParams calib_params;
CalibrationParams saved_calib_params = {0}; // 保存的校准参数

CALIBO_STATE calibo_state=NONE;
_Bool output_flag;//1成功 0失败

// 用于记录进入积分时间选择前的采集模式
CollectMode_t previous_collect_mode_before_int_time = COLLECT_MODE_IDLE;

unsigned int cursor_sheet_num;

// 默认的t8-t15值（用于t8-t15的显示）
// 保持原有的0-3500标签，但映射逻辑使用3648作为数据范围
const int DEFAULT_T_VALUES[8] = {0, 500, 1000, 1500, 2000, 2500, 3000, 3500};

// 【新增】用于标定计算的实际像素值（对应3648个数据点，索引0-3647）
// 映射关系：actual_pixel = (DEFAULT_T_VALUE * 3647) / 3500
const int ACTUAL_PIXEL_VALUES[8] = {0, 521, 1042, 1564, 2085, 2606, 3127, 3647};

// 【新增】标定界面的像素索引值（因为标定界面横坐标倒序）
// 横坐标 X -> 像素 (3644 - X * 3644 / 3500)
const int DEFAULT_PIXEL_VALUES_CALIB[8] = {3644, 3123, 2602, 2082, 1561, 1041, 520, 0};

// 保存进入标定界面前的显示状态
uint16_t saved_dis_value = 100;  // 默认dis值为100
uint32_t saved_y_axis_values[6] = {10000, 20000, 30000, 40000, 50000, 60000};  // 默认Y轴刻度值

// 波长显示控制标志（默认为0，即像素位显示）
uint8_t wavelength_display_enabled = 0;

// 长按检测变量（用于重置缩放按钮）
static uint32_t reset_button_press_time = 0;  // 按钮按下时间（使用HAL_GetTick()）
static uint8_t reset_button_pressed = 0;      // 按钮是否正在被按下
#define LONG_PRESS_DURATION 1000               // 长按时间阈值（毫秒）

// 积分时间值（用于显示）
const uint32_t INTEGRATION_TIMES[INT_TIME_COUNT] = {
    10,     // 10us
    20,     // 20us
    50,     // 50us
    100,    // 100us
    200,    // 200us
    500,    // 500us
    1000,   // 1ms
    2000,   // 2ms
    4000,   // 4ms
    8000,   // 8ms
    20000,  // 20ms
    50000,  // 50ms
    100000, // 100ms
    200000, // 200ms
    500000  // 500ms
};

// 积分时间文本（用于显示）
const char* INT_TIME_TEXT[INT_TIME_COUNT] = {
    "10us",
    "20us",
    "50us",
    "100us",
    "200us",
    "500us",
    "1ms",
    "2ms",
    "4ms",
    "8ms",
    "20ms",
    "50ms",
    "100ms",
    "200ms",
    "500ms"
};

// 积分时间对应的UART3命令（用于发送）
const uint8_t INT_TIME_COMMANDS[INT_TIME_COUNT] = {
    0xB1,   // 10us
    0xB2,   // 20us
    0xB3,   // 50us
    0xB4,   // 100us
    0xB5,   // 200us
    0xB6,   // 500us
    0xB7,   // 1ms
    0xB8,   // 2ms
    0xB9,   // 4ms
    0xBA,   // 8ms 
    0xBB,   // 20ms
    0xBC,   // 50ms
    0xBD,   // 100ms
    0xBE,   // 200ms
    0xBF    // 500ms
};

// 校准波长（用于显示）
const float CALIBRATION_WAVELENGTHS[WAVELENGTH_COUNT] = {
    365.016,  // 365.016nm
    404.656,  // 404.656nm
    435.833,  // 435.833nm
    546.075,  // 546.075nm
    576.961,  // 576.961nm
    579.067   // 579.067nm
};

// 辅助函数：更新标定标签的可见性（根据缩放状态）
void update_calibration_labels_visibility(void) {
    // 如果没有标定参数，不显示标签
    if(!saved_calib_params.is_valid && calib_params.point_count == 0) {
        for(int i = 24; i <= 29; i++) {
            printf("vis t%d,0\xff\xff\xff", i);
        }
        return;
    }
    
    // 【关键修复】获取当前显示范围（像素坐标）
    // 如果处于放大状态，使用放大后的范围；否则使用全范围
    int display_start, display_end;
    if(display_range.is_zoomed) {
        // 放大状态：使用当前放大后的像素范围
        display_start = display_range.current_values[0];
        display_end = display_range.current_values[7];
    } else {
        // 未放大状态：使用实际像素值的全范围
        display_start = ACTUAL_PIXEL_VALUES[0];
        display_end = ACTUAL_PIXEL_VALUES[7];
    }
    
    // 遍历所有标定点，检查是否在显示范围内
    for(int i = 0; i < calib_params.point_count; i++) {
        int calib_x_pixel = (int)calib_params.points[i].x;
        
        // 找到对应的显示标签索引（t31-t36对应的波长）
        int t_display_index = -1;
        for(int j = 0; j < 6; j++) {
            if(calib_params.points[i].lambda == CALIBRATION_WAVELENGTHS[j]) {
                t_display_index = 24 + j;
                break;
            }
        }
        
        if(t_display_index < 0) continue;
        
        // 检查是否在当前显示范围内
        // 注意：current_values存储的是像素坐标，即使已经标定也是如此
        if(calib_x_pixel >= display_start && calib_x_pixel <= display_end) {
            // 在范围内，显示标签并更新位置
            // 需要计算缩放后的屏幕坐标
            // 屏幕X范围：62-791 (729像素)
            // 将像素坐标映射到屏幕坐标
            int screen_x = 62 + (calib_x_pixel - display_start) * 729 / (display_end - display_start);
            printf("t%d.x=%d-37\xff\xff\xff", t_display_index, screen_x);
            
            // 设置Y坐标（奇偶交替）
            int y_coordinate = ((t_display_index - 24 + 1) % 2 == 1) ? 104 : 79;
            printf("t%d.y=%d\xff\xff\xff", t_display_index, y_coordinate);
            
            // 显示标签
            printf("vis t%d,1\xff\xff\xff", t_display_index);
        } else {
            // 不在范围内，隐藏标签
            printf("vis t%d,0\xff\xff\xff", t_display_index);
        }
    }
}

// 清除标定数据（双击重置缩放按钮时调用）
void clear_calibration_data(void) {
    // 清空保存的标定参数
    saved_calib_params.is_valid = 0;
    saved_calib_params.k = 0.0f;
    saved_calib_params.b = 0.0f;
    saved_calib_params.r_squared = 0.0f;
    saved_calib_params.point_count = 0;
    
    // 清空当前标定参数
    calib_params.point_count = 0;
    calib_params.is_valid = 0;
    calib_params.k = 0.0f;
    calib_params.b = 0.0f;
    calib_params.r_squared = 0.0f;
    
    // 隐藏所有标定标签
    for(int i = 24; i <= 29; i++) {
        printf("vis t%d,0\xff\xff\xff", i);
    }
    
    // 显示像素坐标轴（z1），隐藏波长坐标轴（z2）
    printf("vis z1,1\xff\xff\xff");
    printf("vis z2,0\xff\xff\xff");
    
    // 重置横坐标显示为像素值
    for(int i = 0; i < 8; i++) {
        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
        display_range.current_values[i] = DEFAULT_T_VALUES[i];
    }
    
    // 发送提示信息
    printf("debug.txt=\"已清除标定数据\"\xff\xff\xff");
}

// 初始化光谱页面
void spectrum_page_init(void) {
    display_range.x_min = DEFAULT_X_MIN;
    display_range.x_max = DEFAULT_X_MAX;
    display_range.y_min = DEFAULT_Y_MIN;
    display_range.y_max = DEFAULT_Y_MAX;
    display_range.is_zoomed = 0;
    display_range.is_selecting = 0;
    display_range.cursor_pos = DEFAULT_X_MIN;
    display_range.first_selected = -1;
    display_range.second_selected = -1;
    display_range.zoom_level = 0; // 初始放大倍数
    
    // 初始化current_values为默认值t8-t15对应的0-3500
    for(int i = 0; i < 8; i++) {
        display_range.current_values[i] = DEFAULT_T_VALUES[i];
    }
    
    cursor_spectrum = CURSOR_INT_TIME;
    current_int_time = INT_TIME_1MS;
    current_group = 1; // 初始化波段为1
    saved_groups = 0; // 初始化保存的波段数量为0
    
    // 初始化group按钮的文本和颜色
    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
    printf("group.bco=61277\xff\xff\xff");  // 设置group按钮颜色
    printf("a1.bco=61277\xff\xff\xff");     // 设置a1按钮颜色
    printf("a7.bco=61277\xff\xff\xff");     // 设置a7按钮颜色
    
    // 初始化z1和z2的显示
    printf("vis z1,1\xff\xff\xff");    // z1显示
    printf("vis z2,0\xff\xff\xff");    // z2显示
    
    // 初始化t8为固定的"0"（最底部刻度）
    printf("t8.txt=\"0\"\xff\xff\xff");
    
    // 初始化Y轴强度范围（t17-t22显示10000-60000）
    for(int i = 0; i < 6; i++) {
        uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
    }
    
    // 外部定义的spectrum_groups_info和spectrum_data_ram
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
        // 【修复】光谱测量页面：正序发送数据（与ProcessZoomData保持一致）
        uint8_t* source_data = spectrum_data_ram[0];
        for(int i = 0; i < 729; i++) {
            // 等间隔采样：从3648个数据点中采样729个点，正序发送
            int src_index = i * 5; // 3648/729 ≈ 5
            if(src_index < DATA_BUFFER_SIZE) {
                putchar(source_data[src_index]);
            }
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


void up_button(void) {
    // 【禁止切换】如果处于红色等待状态，禁止切换按钮
    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
        return;  // 直接返回，不执行任何切换操作
    }
    
    switch(page) {
        default:break;
  	    	case MAIN://main 页面
			switch(cursor_main)
			{
				case CALIBO:
					printf("calibo.bco=50779\xff\xff\xff");
					printf("data.bco=61277\xff\xff\xff");
					cursor_main=DATA;
				    break;
				
				case DATA:
					printf("data.bco=50779\xff\xff\xff");
					printf("calibo.bco=61277\xff\xff\xff");
					cursor_main=CALIBO;
				    break;
				
				default:break;
			}
			
		break;
        case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，禁用上键功能
            if(view_coord_state.is_active) {
                return;
            }
            
            switch(cursor_spectrum)
            {
                case CURSOR_CALIBRATION: // calibration
                    // 先放大查看 
                    printf("paging.bco=50779\xff\xff\xff"); // 获取当前页面
                    printf("a.bco=61277\xff\xff\xff");   // 设置放大查看
                    cursor_spectrum = CURSOR_INT_TIME;
                    break;
                case CURSOR_ZOOM: // 放大查看
                    // 先缩小
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("photo1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SINGLE_COLLECT;
                    break;
                case CURSOR_AUTO_SCALE: // 自动缩放
                    // 先采集
                    printf("reset1.bco=50779\xff\xff\xff");
                    printf("photo2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    break;
                case CURSOR_RESET_ZOOM: // 重置缩放
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为灰色
                        printf("reset2.bco=50779\xff\xff\xff");
                    }
                    printf("pause.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_PAUSE_COLLECT;
                    break;

                case CURSOR_INT_TIME:
                    printf("paging.bco=61277\xff\xff\xff"); // 获取当前页面
                    printf("a.bco=50779\xff\xff\xff");   // 设置放大查看
                    cursor_spectrum = CURSOR_CALIBRATION;
                    break;
                case CURSOR_SINGLE_COLLECT: 
                    printf("zoom.bco=61277\xff\xff\xff");
                    printf("photo1.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_ZOOM;
                    break;
                case CURSOR_CONT_COLLECT:
                    printf("reset1.bco=61277\xff\xff\xff");
                    printf("photo2.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    break;
                case CURSOR_PAUSE_COLLECT:
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为高亮
                        printf("reset2.bco=61277\xff\xff\xff");
                    }
                    printf("pause.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    break;
                    default:break;
            }
    break;
    
        case INT_TIME_SELECT:
            // 选择积分时间按钮
            printf("a%d.bco=50779\xff\xff\xff", cursor_int_time + 1);
            if(cursor_int_time > 0) {
                cursor_int_time--;
            } else {
                cursor_int_time = INT_TIME_COUNT - 1; // 循环选择最后一个
            }
            printf("a%d.bco=61277\xff\xff\xff", cursor_int_time + 1);
            break;
            
     case QUERY_EXPORT://选择查看 
            // 删除当前选择的
    break;

	case OUTPUTING:
			
	break;

    case OUTPUT_COMPLETE:
        // 显示当前页面
        printf("page main\xff\xff\xff");
        page = MAIN;
        cursor_main = CALIBO;  // 默认选择进入页面
        printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
        break;

    case CALIBRATION:

    break;
    
    case WAVELENGTH_SELECT:
        // 选择波长按钮
        printf("t%d.bco=50779\xff\xff\xff", cursor_wavelength); // 获取当前选择的波长
        if(cursor_wavelength > 0) {
            cursor_wavelength--; // 减少一个波长
        } else {
            cursor_wavelength = WAVELENGTH_COUNT - 1; // 循环选择最后一个波长
        }
        printf("t%d.bco=61277\xff\xff\xff", cursor_wavelength); // 设置选择的波长
        break;
    }
}

// 向下按钮
void down_button(void) {
    // 【禁止切换】如果处于红色等待状态，禁止切换按钮
    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
        return;  // 直接返回，不执行任何切换操作
    }
    
    switch(page) {
        default:break;
       	case MAIN://main 页面
			switch(cursor_main)
			{
				case CALIBO:
					printf("calibo.bco=50779\xff\xff\xff");
					printf("data.bco=61277\xff\xff\xff");
					cursor_main=DATA;
				    break;
				
				case DATA:
					printf("data.bco=50779\xff\xff\xff");
					printf("calibo.bco=61277\xff\xff\xff");
					cursor_main=CALIBO;
				    break;
				
				default:break;
			}
			
		break;
            
           case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，禁用下键功能
            if(view_coord_state.is_active) {
                return;
            }
            
            switch(cursor_spectrum)
            {
                case CURSOR_CALIBRATION: // calibration
                    // 先放大查看
                    printf("paging.bco=50779\xff\xff\xff"); // 获取当前页面
                    printf("a.bco=61277\xff\xff\xff");   // 设置放大查看
                    cursor_spectrum = CURSOR_INT_TIME;
                    break;
                case CURSOR_ZOOM: // 放大查看
                    // 先缩小
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("photo1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SINGLE_COLLECT;
                    break;
                case CURSOR_AUTO_SCALE: // 自动缩放
                    // 先采集
                    printf("reset1.bco=50779\xff\xff\xff");
                    printf("photo2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    break;
                case CURSOR_RESET_ZOOM: // 重置缩放
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为灰色
                        printf("reset2.bco=50779\xff\xff\xff");
                    }
                    printf("pause.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_PAUSE_COLLECT;
                    break;

                case CURSOR_INT_TIME:
                    printf("paging.bco=61277\xff\xff\xff"); // 获取当前页面
                    printf("a.bco=50779\xff\xff\xff");   // 设置放大查看
                    cursor_spectrum = CURSOR_CALIBRATION;
                    break;
                case CURSOR_SINGLE_COLLECT: 
                    printf("zoom.bco=61277\xff\xff\xff");
                    printf("photo1.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_ZOOM;
                    break;
                case CURSOR_CONT_COLLECT:
                    printf("reset1.bco=61277\xff\xff\xff");
                    printf("photo2.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    break;
                case CURSOR_PAUSE_COLLECT:
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为高亮
                        printf("reset2.bco=61277\xff\xff\xff");
                    }
                    printf("pause.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    break;
                    default:break;
            }
            break;
            
        case INT_TIME_SELECT:
            // 选择积分时间按钮
            printf("a%d.bco=50779\xff\xff\xff", cursor_int_time + 1);
            if(cursor_int_time < INT_TIME_COUNT - 1) {
                cursor_int_time++;
            } else {
                cursor_int_time = 0; // 循环选择第一个
            }
            printf("a%d.bco=61277\xff\xff\xff", cursor_int_time + 1);
            break;
            
     case QUERY_EXPORT://选择查看 
            // 删除当前选择的
    break;

	case OUTPUTING:
			
	break;

    case OUTPUT_COMPLETE:
        // 显示当前页面
        printf("page main\xff\xff\xff");
        page = MAIN;
        cursor_main = CALIBO;  // 默认选择进入页面
        printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
        break;

    case CALIBRATION:

    break;
    
    case WAVELENGTH_SELECT:
        // 选择波长按钮
        printf("t%d.bco=50779\xff\xff\xff", cursor_wavelength); // 获取当前选择的波长
        if(cursor_wavelength < WAVELENGTH_COUNT - 1) {
            cursor_wavelength++; // 增加一个波长
        } else {
            cursor_wavelength = 0; // 循环选择第一个波长
        }
        printf("t%d.bco=61277\xff\xff\xff", cursor_wavelength); // 设置选择的波长
        break;
    }
}
// 左按钮
void left_button(void) {
    // 【禁止切换】如果处于红色等待状态，禁止切换按钮
    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
        return;  // 直接返回，不执行任何切换操作
    }
    
    switch(page) {
        case MAIN:
            // main页面
        break;

        case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，左键控制p0向左移动
            if(view_coord_state.is_active) {
                // 使用固定速度移动，不使用计数器
                int step = view_coord_state.move_speed;
                
                // 最小p0.x值为62
                if(view_coord_state.p0_position > 62 + step - 1) {
                    view_coord_state.p0_position -= step;
                } else {
                    view_coord_state.p0_position = 62; // 确保最小值62
                }
                
                // 【关键修复】用户手动移动p0后，清除保存的像素索引，让update_coordinate_display重新计算
                view_coord_state.saved_full_curve_pixel = -1;
                
                // 显示
                printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                update_coordinate_display();
                
                return; // 直接返回，不执行后续逻辑
            }
            
            switch(cursor_spectrum)
            {   
                case CURSOR_SAVE_SPECTRUM:
                    printf("data_record.bco=50779\xff\xff\xff");
                    printf("pause.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_PAUSE_COLLECT;
                    break;
                case CURSOR_SINGLE_COLLECT:
                    printf("photo1.bco=50779\xff\xff\xff");
                    printf("a.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_INT_TIME;
                    break;
				case CURSOR_INT_TIME:
					printf("a.bco=50779\xff\xff\xff");
					printf("data_record.bco=61277\xff\xff\xff");      
                    cursor_spectrum = CURSOR_SAVE_SPECTRUM;
                    break;
                case CURSOR_CONT_COLLECT:
                    printf("photo2.bco=50779\xff\xff\xff");
                    printf("photo1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SINGLE_COLLECT;
                    break;
                case CURSOR_PAUSE_COLLECT:
                    printf("pause.bco=50779\xff\xff\xff");
                    printf("photo2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    break;
                case CURSOR_CALIBRATION:
                    printf("paging.bco=50779\xff\xff\xff");
                    printf("reset2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    break; 
                case CURSOR_ZOOM:
                    // 当前选择的模式下，t8-t16按钮的显示
                    if(display_range.is_selecting) {
                        // 当前选择的t8按钮不为0
                        if(display_range.cursor_pos > 0) {
                            // 获取当前选择的按钮
                            printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                            
                            // 移动一个按钮
                            display_range.cursor_pos--;
                            
                            // 设置当前选择的按钮
                            printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                        }
                    } else {
                        // 当前选择的模式下，t8-t16按钮的显示
                        printf("zoom.bco=50779\xff\xff\xff");
                        printf("paging.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_CALIBRATION;
                    }
                    break;
                case CURSOR_AUTO_SCALE:
                    printf("reset1.bco=50779\xff\xff\xff");
                    printf("zoom.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_ZOOM;
                    break;
                case CURSOR_RESET_ZOOM:
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为灰色
                        printf("reset2.bco=50779\xff\xff\xff");
                    }
                    printf("reset1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    break;
                default:break;
            }      
        break;
        
        case CALIBRATION:
            // 如果在zoom选择模式下，左键移动光标
            if(cursor_calibration1 == CURSOR_ZOOM_CALIB && display_range.is_selecting) {
                // 当前选择t8按钮不为0
                if(display_range.cursor_pos > 0) {
                    // 取消当前选择的按钮
                    printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                    
                    // 移动一个按钮
                    display_range.cursor_pos--;
                    
                    // 设置当前选择的按钮
                    printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                }
                return; // 直接返回
            }
            
            // 如果在波长选择状态（在t31-t36中选择），左键切换到前一个波长
            if(calib_params.state == CALIB_SELECTING_WAVELENGTH) {
                // 取消当前波长按钮的高亮
                int current_t = 31 + calib_params.selected_wavelength_button;
                printf("t%d.bco=50779\xff\xff\xff", current_t);
                
                // 移动到前一个波长
                if(calib_params.selected_wavelength_button > 0) {
                    calib_params.selected_wavelength_button--;
                } else {
                    calib_params.selected_wavelength_button = 5; // 循环到最后一个
                }
                
                // 高亮新的波长按钮 - 使用黄色让选中更明显
                int new_t = 31 + calib_params.selected_wavelength_button;
                printf("t%d.bco=61277\xff\xff\xff", new_t);
                
                return; // 直接返回
            }
            
            // 当前选择的模式下，p0.x值为当前波段范围
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 使用固定速度移动，使用步进电机
                int step = calib_params.move_speed;
                
                // 最小p0.x值为62
                if(calib_params.temp_peak_x > 62 + step - 1) {
                    calib_params.temp_peak_x -= step;
                } else {
                    calib_params.temp_peak_x = 62; // 确定最小值62
                }
                
                // 显示
                printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                
                return; // 直接返回，不执行后续代码
            }
            
            // 当前选择的按钮（左键循环：t5→input→coeff→switch→saving→reset2→zoom→t5）
            switch(cursor_calibration1)
            {
                case CURSOR_SELECT_PEAK:  // t5
                    printf("t5.bco=50779\xff\xff\xff");
                    printf("input.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_INPUT_COEFF;
                    break;
                case CURSOR_INPUT_COEFF:  // input
                    printf("input.bco=50779\xff\xff\xff");
                    printf("coeff.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_EXPORT_COEFF_CALIB;
                    break;
                case CURSOR_EXPORT_COEFF_CALIB:  // coeff
                    printf("coeff.bco=50779\xff\xff\xff");
                    printf("switch.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SWITCH_CALIB;
                    break;
                case CURSOR_SWITCH_CALIB:  // switch
                    printf("switch.bco=50779\xff\xff\xff");
                    printf("saving.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SAVE_CALIB;
                    break;
                case CURSOR_SAVE_CALIB:  // saving
                    printf("saving.bco=50779\xff\xff\xff");
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为高亮
                        printf("reset2.bco=61277\xff\xff\xff");
                    }
                    cursor_calibration1 = CURSOR_RESET_CALIB;
                    break;
                case CURSOR_RESET_CALIB:  // reset2
                    // 【修复】检查是否在红色等待状态
                    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                        // 在红色等待状态，保持红色
                        printf("reset2.bco=48634\xff\xff\xff");
                    } else {
                        // 不在等待状态，设为灰色
                        printf("reset2.bco=50779\xff\xff\xff");
                    }
                    printf("zoom.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_ZOOM_CALIB;
                    break;
                case CURSOR_ZOOM_CALIB:  // zoom
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("t5.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SELECT_PEAK;
                    break;
                default:break;
            }
        break;
  
        case QUERY_EXPORT:
            // 当前选择的波段和模式下，发送按钮的显示
            if(cursor_spectrum == CURSOR_ZOOM && display_range.is_selecting) {
                // 当前选择的模式是zoom
                if(display_range.cursor_pos > 0) {
                    // 获取当前选择的按钮
                    printf("t%d.bco=50779\xff\xff\xff", (int)display_range.cursor_pos + 8);
                    
                    // 移动按钮
                    display_range.cursor_pos--;
                    
                    // 设置按钮
                    printf("t%d.bco=61277\xff\xff\xff", (int)display_range.cursor_pos + 8);
                } else {
                    // 当前选择的模式是t8，没有选择波段
                    // 获取当前选择的按钮
                    printf("t%d.bco=50779\xff\xff\xff", (int)display_range.cursor_pos + 8);
                    
                    // 选择模式
                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    
                    // 重置zoom按钮
                    printf("zoom.bco=61277\xff\xff\xff");
                }
            } else if(cursor_spectrum == CURSOR_CALIBRATION || cursor_spectrum == CURSOR_ZOOM || 
               cursor_spectrum == CURSOR_AUTO_SCALE || cursor_spectrum == CURSOR_RESET_ZOOM || 
               cursor_spectrum == CURSOR_EXPORT_USB || cursor_spectrum == CURSOR_EXPORT_COEFF) {
                // 当前选择的波段和模式下，发送按钮的显示
                switch(cursor_spectrum)
                {   
                    case CURSOR_CALIBRATION:
                        // calibration按钮的显示
                        printf("paging.bco=50779\xff\xff\xff");
                        printf("coeff.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_COEFF;
                        break;
                    case CURSOR_ZOOM:
                        printf("zoom.bco=50779\xff\xff\xff");
                        printf("paging.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_CALIBRATION;
                        break;
                    case CURSOR_AUTO_SCALE:
                        printf("reset1.bco=50779\xff\xff\xff");
                        printf("zoom.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_ZOOM;
                        break;
                    case CURSOR_RESET_ZOOM:
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为灰色
                            printf("reset2.bco=50779\xff\xff\xff");
                        }
                        printf("reset1.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_AUTO_SCALE;
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为高亮
                            printf("reset2.bco=61277\xff\xff\xff");
                        }
                        cursor_spectrum = CURSOR_RESET_ZOOM;
                        break;
                    case CURSOR_EXPORT_COEFF:
                        printf("coeff.bco=50779\xff\xff\xff");
                        printf("output.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_USB;
                        break;
                    default:
                        break;
                }
            }
        break;
        
        case OUTPUTING:
            // 当前选择的波段和模式下，发送按钮的显示
        break;

        case OUTPUT_COMPLETE:
            // 显示当前页面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
    }
}
// 右按钮
void right_button(void) {
    // 【禁止切换】如果处于红色等待状态，禁止切换按钮
    if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
        return;  // 直接返回，不执行任何切换操作
    }
    
     switch(page) {
        default:break;
        case MAIN:
            // main页面
        break;

        case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，右键控制p0向右移动
            if(view_coord_state.is_active) {
                // 使用固定速度移动，不使用计数器
                int step = view_coord_state.move_speed;
                
                // p0.x值的范围（屏幕坐标）：62-791
                // 检测是否溢出，p0在屏幕坐标系上向右移动
                if(view_coord_state.p0_position < 791 - step + 1) {
                    view_coord_state.p0_position += step;
                } else {
                    view_coord_state.p0_position = 791; // 确保最大值791
                }
                
                // 【关键修复】用户手动移动p0后，清除保存的像素索引，让update_coordinate_display重新计算
                view_coord_state.saved_full_curve_pixel = -1;
                
                // 显示
                printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                update_coordinate_display();
                
                // 返回，不执行后续逻辑
                return;
            }
            
              switch(cursor_spectrum)
            {
                case CURSOR_SAVE_SPECTRUM:
                  printf("data_record.bco=50779\xff\xff\xff");
                  printf("a.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_INT_TIME;
                  break;
                case CURSOR_INT_TIME:
                  printf("a.bco=50779\xff\xff\xff");
                  printf("photo1.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_SINGLE_COLLECT;
                  break;
                case CURSOR_SINGLE_COLLECT:
                   printf("photo1.bco=50779\xff\xff\xff");
                   printf("photo2.bco=61277\xff\xff\xff");
                   cursor_spectrum = CURSOR_CONT_COLLECT;
                   break;
                case CURSOR_CONT_COLLECT:
                  printf("photo2.bco=50779\xff\xff\xff");
                  printf("pause.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_PAUSE_COLLECT;
                  break;
                case CURSOR_PAUSE_COLLECT:
                  printf("pause.bco=50779\xff\xff\xff");
                  printf("data_record.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_SAVE_SPECTRUM;
                  break;
                case CURSOR_CALIBRATION:
                  printf("paging.bco=50779\xff\xff\xff");
                  printf("zoom.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_ZOOM; 
                  break; 
                case CURSOR_ZOOM:
                  // 当前选择的模式下，t8-t15按钮的显示
                  if(display_range.is_selecting) {
                      // 当前选择的t15按钮不为7
                      if(display_range.cursor_pos < 7) {
                          // 获取当前选择的按钮
                          printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                          
                          // 移动一个按钮
                          display_range.cursor_pos++;
                          
                          // 设置当前选择的按钮
                          printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                      }
                  } else {
                      // 当前选择的模式下，t8-t15按钮的显示
                      printf("zoom.bco=50779\xff\xff\xff");
                      printf("reset1.bco=61277\xff\xff\xff");
                      cursor_spectrum = CURSOR_AUTO_SCALE;
                  }
                  break;
                case CURSOR_AUTO_SCALE:
                  printf("reset1.bco=50779\xff\xff\xff");
                  // 【修复】检查是否在红色等待状态
                  if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                      // 在红色等待状态，保持红色
                      printf("reset2.bco=63488\xff\xff\xff");
                  } else {
                      // 不在等待状态，设为高亮
                      printf("reset2.bco=61277\xff\xff\xff");
                  }
                  cursor_spectrum = CURSOR_RESET_ZOOM;
                  break;
                case CURSOR_RESET_ZOOM:
                  // 【修复】检查是否在红色等待状态
                  if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                      // 在红色等待状态，保持红色
                      printf("reset2.bco=63488\xff\xff\xff");
                  } else {
                      // 不在等待状态，设为灰色
                      printf("reset2.bco=50779\xff\xff\xff");
                  }
                  printf("paging.bco=61277\xff\xff\xff");  
                  cursor_spectrum = CURSOR_CALIBRATION;
                  break;
                  default:break;
            }      
        break;
        case CALIBRATION:
            // 如果在zoom选择模式下，右键移动光标
            if(cursor_calibration1 == CURSOR_ZOOM_CALIB && display_range.is_selecting) {
                // 当前选择t15按钮不为7
                if(display_range.cursor_pos < 7) {
                    // 取消当前选择的按钮
                    printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                    
                    // 移动一个按钮
                    display_range.cursor_pos++;
                    
                    // 设置当前选择的按钮
                    printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                }
                return; // 直接返回
            }
            
            // 如果在波长选择状态（在t31-t36中选择），右键切换到下一个波长
            if(calib_params.state == CALIB_SELECTING_WAVELENGTH) {
                // 取消当前波长按钮的高亮
                int current_t = 31 + calib_params.selected_wavelength_button;
                printf("t%d.bco=50779\xff\xff\xff", current_t);
                
                // 移动到下一个波长
                if(calib_params.selected_wavelength_button < 5) {
                    calib_params.selected_wavelength_button++;
                } else {
                    calib_params.selected_wavelength_button = 0; // 循环到第一个
                }
                
                // 高亮新的波长按钮 - 使用黄色让选中更明显
                int new_t = 31 + calib_params.selected_wavelength_button;
                printf("t%d.bco=61277\xff\xff\xff", new_t);
                
                return; // 直接返回
            }
            
            // 当前选择的模式下，p0.x值为当前波段范围
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 使用固定速度移动，使用步进电机
                int step = calib_params.move_speed;
                
                // p0.x值的最大范围（屏幕坐标）：62-791
                // 不论是否缩放，p0都在屏幕坐标系内移动
                if(calib_params.temp_peak_x < 791 - step + 1) {
                    calib_params.temp_peak_x += step;
                } else {
                    calib_params.temp_peak_x = 791; // 确定最大值791
                }
                
                // 显示
                printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                
                // 返回，不执行后续代码
                return;
            }
            
            // 当前选择的按钮（右键循环：t5→zoom→reset2→saving→switch→coeff→input→t5）
           switch(cursor_calibration1)
         {
           case CURSOR_SELECT_PEAK:  // t5
              printf("t5.bco=50779\xff\xff\xff");
              printf("zoom.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_ZOOM_CALIB;
              break;
           case CURSOR_ZOOM_CALIB:  // zoom
              printf("zoom.bco=50779\xff\xff\xff");
              // 【修复】检查是否在红色等待状态
              if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                  // 在红色等待状态，保持红色
                  printf("reset2.bco=63488\xff\xff\xff");
              } else {
                  // 不在等待状态，设为高亮
                  printf("reset2.bco=61277\xff\xff\xff");
              }
              cursor_calibration1 =  CURSOR_RESET_CALIB;
              break;
           case CURSOR_RESET_CALIB:  // reset2
              // 【修复】检查是否在红色等待状态
              if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                  // 在红色等待状态，保持红色
                  printf("reset2.bco=63488\xff\xff\xff");
              } else {
                  // 不在等待状态，设为灰色
                  printf("reset2.bco=50779\xff\xff\xff");
              }
              printf("saving.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_SAVE_CALIB;
              break;
           case CURSOR_SAVE_CALIB:  // saving
              printf("saving.bco=50779\xff\xff\xff");
              printf("switch.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_SWITCH_CALIB;
              break;
           case CURSOR_SWITCH_CALIB:  // switch
              printf("switch.bco=50779\xff\xff\xff");
              printf("coeff.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_EXPORT_COEFF_CALIB;
              break;
           case CURSOR_EXPORT_COEFF_CALIB:  // coeff
              printf("coeff.bco=50779\xff\xff\xff");
              printf("input.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_INPUT_COEFF;
              break;
           case CURSOR_INPUT_COEFF:  // input
              printf("input.bco=50779\xff\xff\xff");
              printf("t5.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_SELECT_PEAK;
              break;
              default:break;
         }
        break;
  
        case QUERY_EXPORT:
            // 当前选择的波段和模式下，发送按钮的显示
            if(cursor_spectrum == CURSOR_ZOOM && display_range.is_selecting) {
                // 当前选择的模式是zoom
                if(display_range.cursor_pos < 7) {
                    // 获取当前选择的按钮
                    printf("t%d.bco=50779\xff\xff\xff", (int)display_range.cursor_pos + 8);
                    
                    // 移动按钮
                    display_range.cursor_pos++;
                    
                    // 设置按钮
                    printf("t%d.bco=61277\xff\xff\xff", (int)display_range.cursor_pos + 8);
                }
            } else if(cursor_spectrum == CURSOR_CALIBRATION || cursor_spectrum == CURSOR_ZOOM || 
                     cursor_spectrum == CURSOR_AUTO_SCALE || cursor_spectrum == CURSOR_RESET_ZOOM || 
                     cursor_spectrum == CURSOR_EXPORT_USB || cursor_spectrum == CURSOR_EXPORT_COEFF) {
                // 当前选择的波段和模式下，发送按钮的显示
                switch(cursor_spectrum)
                {   
                    case CURSOR_CALIBRATION:
                        printf("paging.bco=50779\xff\xff\xff");
                        printf("zoom.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_ZOOM;
                        break; 
                    case CURSOR_ZOOM:
                        printf("zoom.bco=50779\xff\xff\xff"); 
                        printf("reset1.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_AUTO_SCALE;
                        break;
                    case CURSOR_AUTO_SCALE:
                        printf("reset1.bco=50779\xff\xff\xff");
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为高亮
                            printf("reset2.bco=61277\xff\xff\xff");
                        }
                        cursor_spectrum = CURSOR_RESET_ZOOM;
                        break;
                    case CURSOR_RESET_ZOOM:
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为灰色
                            printf("reset2.bco=50779\xff\xff\xff");
                        }
                        printf("output.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_USB;
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        printf("coeff.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_COEFF;
                        break;
                    case CURSOR_EXPORT_COEFF:
                        // 发送按钮的显示
                        printf("coeff.bco=50779\xff\xff\xff");
                        printf("paging.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_CALIBRATION;
                        break;
                    default:
                        break;
                }
            }
        break;
        
        case OUTPUTING:
			
	     break;

        case OUTPUT_COMPLETE:
            // 显示当前页面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
    }
}


// 确认按钮
void confirm_button(void) {
    switch(page) {
        case MAIN:
           switch(cursor_main)
			{
			        	case CALIBO:
                    // 获取当前页面
                    printf("calibo.bco=50779\xff\xff\xff");
                    
                    printf("page measure\xff\xff\xff");
                    printf("s0.x=62\xff\xff\xff");  // 设置曲线从62位置开始
                    page = SPECTRUM_MEASURE;
                    // 初始化measure页面
                    cursor_spectrum = CURSOR_INT_TIME;
                    printf("a.bco=61277\xff\xff\xff");  // 设置进入页面

                    // 【修复】恢复自动缩放状态（使用保存的缩放参数）
                    extern uint16_t saved_dis_value;
                    extern uint32_t saved_y_axis_values[6];
                    
                    // 恢复dis参数
                    printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
                    
                    // 恢复Y轴强度范围（使用保存的值）
                    for(int i = 0; i < 6; i++) {
                        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
                    }
                    
                    // 【关键修复】根据wavelength_display_enabled标志初始化z1/z2的显示和横坐标值
                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                        // 波长显示模式：显示波长坐标（z2）
                        printf("vis z1,0\xff\xff\xff");    // z1隐藏
                        printf("vis z2,1\xff\xff\xff");    // z2显示
                        
                        // 【关键】设置t8-t15的横坐标为波长值
                        for(int i = 0; i < 8; i++) {
                            int pixel_val = DEFAULT_T_VALUES[i];
                            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                        }
                    } else {
                        // 像素位显示模式：显示像素坐标（z1）
                    printf("vis z1,1\xff\xff\xff");    // z1显示
                        printf("vis z2,0\xff\xff\xff");    // z2隐藏
                        
                        // 【关键】设置t8-t15的横坐标为像素值
                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                        }
                    }
                    
                    // 【新增修复】重新发送存储的曲线数据到屏幕
                    extern SpectrumGroupInfo spectrum_groups_info[12];
                    extern uint8_t current_group;
                    extern volatile uint8_t addt_in_progress;
                    
                    if(current_group >= 1 && current_group <= 12) {
                        uint8_t group_index = current_group - 1;
                        
                        if(spectrum_groups_info[group_index].is_valid && 
                           spectrum_groups_info[group_index].data_length >= 3640 && 
                           !addt_in_progress) {
                            
                            // 延迟确保页面加载完成
                            for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                                __NOP();
                            }
                            
                            extern void ProcessAndDisplayGroupData(uint8_t group_index);
                            ProcessAndDisplayGroupData(group_index);
                        }
                    }
                    
                    // 【新增】更新p0位置（无论是否激活查看坐标功能）
                    printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                    
                    // 【新增】如果查看坐标功能已激活，根据p0位置更新t1显示
                    if(view_coord_state.is_active) {
                        update_coordinate_display();
                    }
                    break;
                    
                case DATA:
                    // 获取当前页面
                    printf("data.bco=50779\xff\xff\xff");
                    
                    printf("page query\xff\xff\xff");
                    page = QUERY_EXPORT;
                    
                    // 初始化query页面
                    query_export_page_init();
                    break;
                    
 
                default:
                    break;
            }
            break;
            
        case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，禁用确认键功能
            if(view_coord_state.is_active) {
                return;
            }
            
            switch(cursor_spectrum) {
                case CURSOR_INT_TIME:
                    // 选择积分时间 - 进入前先检查并暂停连续采集
                    
                    // 记录当前的采集模式，以便稍后恢复
                    previous_collect_mode_before_int_time = current_collect_mode;
                    
                    // 检查当前是否为连续采集状态，如果是则先暂停
                    if(current_collect_mode == COLLECT_MODE_CONTINUOUS) {
                        // 设置调试信息
                        printf("debug.txt=\"暂停连续采集以修改积分时间\"\xff\xff\xff");
                        
                        // 暂停连续采集
                        extern volatile uint8_t need_send_a2_flag;
                        need_send_a2_flag = 0;  // 停止A2标志
                        HAL_UART_AbortReceive(&huart3);  // 停止DMA传输
                        current_collect_mode = COLLECT_MODE_IDLE;  // 设置当前模式为空闲模式
                        
                        // 等待一段时间确保采集完全停止
                        for(volatile uint32_t delay_count = 0; delay_count < 500000; delay_count++) {
                            __NOP(); // 等待约50ms
                        }
                        
                        // 更新界面状态 - 取消连续采集按钮高亮
                        printf("photo2.bco=50779\xff\xff\xff");  // 取消连续采集按钮高亮
                    }
                    
                    // 进入积分时间选择页面
                    printf("page timer1\xff\xff\xff");
                    page = INT_TIME_SELECT;
                    printf("a1.bco=61277\xff\xff\xff");
                    cursor_int_time = 0; // 设置为最小积分时间
                    break;
                    
                case CURSOR_CALIBRATION:
                    // 选择校准
                    printf("page calibration\xff\xff\xff");
                    page = CALIBRATION;
                    
                    // 初始化calibration页面
                    calibration_page_init();
                    break;
                    
                case CURSOR_SINGLE_COLLECT:
                {
                   // 设置t8-t15的显示状态
                   printf("photo1.bco=61277\xff\xff\xff"); // 设置为采集状态
                   cursor_spectrum = CURSOR_SINGLE_COLLECT;
                   
                   // 【修复】根据wavelength_display_enabled标志设置t8-t15的显示值，但current_values始终存储像素值
                   if(wavelength_display_enabled && saved_calib_params.is_valid) {
                       // 波长显示模式：横坐标显示波长
                       printf("vis z1,0\xff\xff\xff");    // z1隐藏
                       printf("vis z2,1\xff\xff\xff");    // z2显示
                       
                       for(int i = 0; i < 8; i++) {
                           int pixel_val = DEFAULT_T_VALUES[i];
                           float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                           printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                           // 【关键】current_values始终存储像素值（用于标定标签位置计算）
                           display_range.current_values[i] = DEFAULT_T_VALUES[i];
                       }
                       
                       // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                       // 计算并更新t1显示的波长值（基于当前p0位置）
                       int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                       if(pixel_index < 0) pixel_index = 0;
                       if(pixel_index > 3648) pixel_index = 3648;
                       
                       float wavelength = saved_calib_params.k * pixel_index + saved_calib_params.b;
                       printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
                       
                       // 如果正在查看坐标状态，显示t1/p0控件
                       if(view_coord_state.is_active) {
                           printf("vis p0,1\xff\xff\xff");
                           printf("vis t1,1\xff\xff\xff");
                       }
                   } else {
                       // 像素位显示模式：横坐标显示像素值
                       printf("vis z1,1\xff\xff\xff");    // z1显示
                       printf("vis z2,0\xff\xff\xff");    // z2隐藏
                       
                       for(int i = 0; i < 8; i++) {
                           printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                           display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                       }
                       
                       // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                       // 计算并更新t1显示的像素值（基于当前p0位置）
                       int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                       if(pixel_index < 0) pixel_index = 0;
                       if(pixel_index > 3648) pixel_index = 3648;
                       
                       printf("t1.txt=\"%d\"\xff\xff\xff", pixel_index);
                       
                       // 如果正在查看坐标状态，显示t1/p0控件
                       if(view_coord_state.is_active) {
                           printf("vis p0,1\xff\xff\xff");
                           printf("vis t1,1\xff\xff\xff");
                       }
                   }
                   
                   // 设置t8-t15的显示颜色
                   for(int i = 8; i <= 15; i++) {
                       printf("t%d.pco=0\xff\xff\xff", i); // 设置颜色
                       printf("t%d.bco=50779\xff\xff\xff", i); // 设置背景颜色
                   }
                   
                   // 设置选择状态
                   display_range.is_selecting = 0;
                   display_range.first_selected = -1;
                   display_range.second_selected = -1;
                   display_range.zoom_level = 0; // 设置放大倍数
                   display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                   view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                   
                   // 设置采集模式
                   current_collect_mode = COLLECT_MODE_SINGLE;
                   
                   // 使用DMA进行传输
                   extern uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE];
                   HAL_StatusTypeDef uart_status;
                   HAL_UART_StateTypeDef current_state = HAL_UART_GetState(&huart3);
                   
                   // 检查UART是否忙于接收或发送
                   if(current_state == HAL_UART_STATE_BUSY_RX || current_state == HAL_UART_STATE_BUSY_TX_RX) {
                       HAL_UART_AbortReceive(&huart3);
                       // 重置DMA传输
                       for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
                           __NOP();
                       }
                   }
                   
                   // 清空缓冲区
                   memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
                   
                   // 使用DMA进行传输
                   uart_status = HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                   if(uart_status != HAL_OK) {
                       // 重置UART3
                       MX_USART3_UART_Init();
                       // 重置
                       for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
                           __NOP();
                       }
                       HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                   }
                   
                   // 设置A2标志
                   extern volatile uint8_t need_send_a2_flag;
                   need_send_a2_flag = 1;
                   break;
                }
                    
                case CURSOR_CONT_COLLECT:
                {
                    // 设置t8-t15的显示状态
                    printf("photo2.bco=61277\xff\xff\xff"); // 设置为连续采集状态
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    
                    // 【修复】根据wavelength_display_enabled标志设置t8-t15的显示值，但current_values始终存储像素值
                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                        // 波长显示模式：横坐标显示波长
                        printf("vis z1,0\xff\xff\xff");    // z1隐藏
                        printf("vis z2,1\xff\xff\xff");    // z2显示
                        
                        for(int i = 0; i < 8; i++) {
                            int pixel_val = DEFAULT_T_VALUES[i];
                            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            // 【关键】current_values始终存储像素值（用于标定标签位置计算）
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
                        }
                        
                        // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                        // 计算并更新t1显示的波长值（基于当前p0位置）
                        int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                        if(pixel_index < 0) pixel_index = 0;
                        if(pixel_index > 3648) pixel_index = 3648;
                        
                        float wavelength = saved_calib_params.k * pixel_index + saved_calib_params.b;
                        printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
                        
                        // 如果正在查看坐标状态，显示t1/p0控件
                        if(view_coord_state.is_active) {
                            printf("vis p0,1\xff\xff\xff");
                            printf("vis t1,1\xff\xff\xff");
                        }
                    } else {
                        // 像素位显示模式：横坐标显示像素值
                        printf("vis z1,1\xff\xff\xff");    // z1显示
                        printf("vis z2,0\xff\xff\xff");    // z2隐藏
                        
                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                        }
                        
                        // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                        // 计算并更新t1显示的像素值（基于当前p0位置）
                        int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                        if(pixel_index < 0) pixel_index = 0;
                        if(pixel_index > 3648) pixel_index = 3648;
                        
                        printf("t1.txt=\"%d\"\xff\xff\xff", pixel_index);
                        
                        // 如果正在查看坐标状态，显示t1/p0控件
                        if(view_coord_state.is_active) {
                            printf("vis p0,1\xff\xff\xff");
                            printf("vis t1,1\xff\xff\xff");
                        }
                    }
                    
                    // 设置t8-t15的显示颜色
                    for(int i = 8; i <= 15; i++) {
                        printf("t%d.pco=0\xff\xff\xff", i); // 设置颜色
                        printf("t%d.bco=50779\xff\xff\xff", i); // 设置背景颜色
                    }
                    
                    // 设置选择状态
                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    display_range.zoom_level = 0; // 设置放大倍数
                    display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                    view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                    
                    // 设置连续采集模式
                    current_collect_mode = COLLECT_MODE_CONTINUOUS;
                    
                    // 使用DMA进行传输
                    extern uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE];
                    HAL_StatusTypeDef uart_status;
                    HAL_UART_StateTypeDef current_state = HAL_UART_GetState(&huart3);
                    
                    // 检查UART是否忙于接收或发送
                    if(current_state == HAL_UART_STATE_BUSY_RX || current_state == HAL_UART_STATE_BUSY_TX_RX) {
                        HAL_UART_AbortReceive(&huart3);
                        // 重置DMA传输
                        for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
                            __NOP();
                        }
                    }
                    
                    // 清空缓冲区
                    memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
                    
                    // 使用DMA进行传输
                    uart_status = HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                    if(uart_status != HAL_OK) {
                        // 重置UART3
                        MX_USART3_UART_Init();
                        // 重置
                        for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
                            __NOP();
                        }
                        HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                    }
                    
                    // 设置A2标志
                    extern volatile uint8_t need_send_a2_flag;
                    need_send_a2_flag = 1;
                    
                    // 设置调试信息
                    printf("debug.txt=\"开始采集\"\xff\xff\xff");
                    break;
                }
                    
                case CURSOR_PAUSE_COLLECT:
                    // 暂停采集
                    // 禁用DMA
                    current_collect_mode = COLLECT_MODE_IDLE;
                    HAL_UART_AbortReceive(&huart3);
                    
                    // 设置A2标志
                    extern volatile uint8_t need_send_a2_flag;
                    need_send_a2_flag = 0;
                    break;
                
                case CURSOR_SAVE_SPECTRUM:
                    // 保存当前波形
                    // 重置溯源
                    //save_spectrum_to_flash(); // 删除当前波形
                    
                    // 保存的波段数量为12
                    if(saved_groups < 12) {
                        saved_groups++;
                    }
                    
                    // 当前波段数量为12
                    if(current_group < 12) {
                        current_group++;
                    } else {
                        current_group = 1; // 达到最大值，循环回到第一个波段
                    }
                    
                    // 只更新group按钮的文本和值
                    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
                    
                    // 同时更新t8-t15的值
                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                        // 波长显示模式
                        for(int i = 0; i < 8; i++) {
                            int pixel_val = DEFAULT_T_VALUES[i]; // 使用默认的像素坐标
                            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            
                            // 【关键】存储像素值（用于标定标签位置计算）
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
                        }
                        
                        // 设置z1和z2的显示
                        printf("vis z1,0\xff\xff\xff");    // z1隐藏
                        printf("vis z2,1\xff\xff\xff");    // z2显示
                    } else {
                        // 像素位显示模式
                        for(int i = 0; i < 8; i++) {
                            int pixel_val = DEFAULT_T_VALUES[i];
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, pixel_val);
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
                        }
                        
                        // 设置z1和z2的显示
                        printf("vis z1,1\xff\xff\xff");    // z1显示
                        printf("vis z2,0\xff\xff\xff");    // z2隐藏
                    }
                    
                    // 设置data_record按钮
                    printf("data_record.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SAVE_SPECTRUM;
                    break;
                    
                case CURSOR_ZOOM:
                    // 放大查看
                    cursor_spectrum = CURSOR_ZOOM;
                    
                    // 当前选择的模式下，没有选择波段
                    if(display_range.is_selecting) {
                        // 当前选择的波段
                        int current_pos = (int)display_range.cursor_pos;
                        
                        // 当前选择的波段没有选择
                        if(display_range.first_selected == -1) {
                            // 选择第一个波段
                            display_range.first_selected = current_pos;
                            // 设置当前选择的按钮
                            printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 【修复】红色文字（RGB565: 63488）
                        }
                        // 当前选择的波段没有选择
                        else if(display_range.second_selected == -1) {
                            // 选择不同的波段
                            if(current_pos != display_range.first_selected) { 
                                // 选择第二个波段
                                display_range.second_selected = current_pos;
                                // 设置当前选择的按钮
                                printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 【修复】红色文字（RGB565: 63488）
                                
                                // 获取选择的波段值
                                int first_idx = display_range.first_selected;
                                int second_idx = display_range.second_selected;
                                
                                // 【关键】current_values中存储的是像素值（不是屏幕显示值）
                                int start_pixel, end_pixel;
                                int start_idx, end_idx;
                                
                                // 确保start_pixel <= end_pixel
                                if(display_range.current_values[first_idx] <= display_range.current_values[second_idx]) {
                                    start_pixel = display_range.current_values[first_idx];
                                    end_pixel = display_range.current_values[second_idx];
                                    start_idx = first_idx;
                                    end_idx = second_idx;
                                } else {
                                    start_pixel = display_range.current_values[second_idx];
                                    end_pixel = display_range.current_values[first_idx];
                                    start_idx = second_idx;
                                    end_idx = first_idx;
                                }
                                
                                // 生成8个新的横坐标值（像素值和显示值）
                                for(int i = 0; i < 8; i++) {
                                    int new_pixel_val;  // 像素值（用于存储）
                                    
                                    if(i == 7) {
                                        // 最后一个值
                                        new_pixel_val = end_pixel;
                                    } else {
                                        // 线性插值
                                        new_pixel_val = start_pixel + (end_pixel - start_pixel) * i / 7;
                                    }
                                    
                                    // 显示值
                                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                        // 波长显示模式：显示波长，但存储像素值
                                        float wavelength = saved_calib_params.k * new_pixel_val + saved_calib_params.b;
                                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                    } else {
                                        // 像素位显示模式：显示像素值，存储像素值
                                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, new_pixel_val);
                                    }
                                    
                                    // 【关键】存储像素值（用于标定标签位置计算和下次放大）
                                    display_range.current_values[i] = new_pixel_val;
                                }
                                
                                // 设置放大倍数
                                if(display_range.zoom_level < 2) {
                                    display_range.zoom_level++;
                                }
                                
                                // 设置t8-t15的显示颜色
                                for(int i = 8; i <= 15; i++) {
                                    printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                                    printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景色
                                }
                                
                                // 处理缩放数据（传入像素值）
                                ProcessZoomData(start_pixel, end_pixel);
                                
                                // 【关键修复】设置放大状态标志
                                display_range.is_zoomed = 1;
                                
                                // 【新增】放大查看后，调整p0位置到合适的位置
                                // 如果当前p0位置对应的像素值在放大范围内，则将p0映射到放大后的对应位置
                                // 否则，将p0移动到起始位置（x=62）
                                // 计算当前p0位置对应的像素索引（基于放大前的完整曲线）
                                // 注意：这里需要使用放大前的映射关系
                                int old_pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                                
                                // 检查该像素索引是否在放大范围内
                                if(old_pixel_index >= start_pixel && old_pixel_index <= end_pixel) {
                                    // 【关键修复】在范围内：保存完整曲线的像素索引，避免多次整数除法累积误差
                                    view_coord_state.saved_full_curve_pixel = old_pixel_index;
                                    
                                    // 使用浮点数计算新位置，提高精度
                                    float relative_pos = (float)(old_pixel_index - start_pixel) / (end_pixel - start_pixel);
                                    int new_p0_position = 62 + (int)(relative_pos * (791 - 62) + 0.5f); // 四舍五入
                                    view_coord_state.p0_position = new_p0_position;
                                    
                                    // 【修复】放大后，如果p0在范围内，直接显示p0（不管是否激活查看坐标模式）
                                    printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                                } else {
                                    // 【新需求】不在范围内：保存原始屏幕坐标，隐藏p0
                                    view_coord_state.saved_screen_position = view_coord_state.p0_position;
                                    view_coord_state.saved_full_curve_pixel = -1; // 清除像素索引
                                    view_coord_state.p0_position = 62; // 设为起始位置（但不显示）
                                    printf("vis p0,0\xff\xff\xff"); // 隐藏p0
                                }
                                
                                // 更新t1的显示（如果查看坐标功能已激活）
                                if(view_coord_state.is_active) {
                                    // 更新t1的显示（显示p0位置对应的坐标值）
                                    // 放大后的像素索引计算：基于新的范围
                                    int new_pixel_index = start_pixel + ((view_coord_state.p0_position - 62) * (end_pixel - start_pixel)) / (791 - 62);
                                    
                                    // 显示对应的坐标值
                                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                        // 波长显示模式
                                        float wavelength = saved_calib_params.k * new_pixel_index + saved_calib_params.b;
                                        printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
                                    } else {
                                        // 像素位显示模式
                                        printf("t1.txt=\"%d\"\xff\xff\xff", new_pixel_index);
                                    }
                                }
                                
                                // 重置选择状态
                                display_range.is_selecting = 0;
                                display_range.first_selected = -1;
                                display_range.second_selected = -1;
                            }
                            // 如果选择了相同的波段，则不执行任何操作
                        }
                    } else {
                        // 初始化t8
                        printf("t8.bco=61277\xff\xff\xff");  // 初始化第一个波段
                        
                        // 当前选择的按钮对应的t8值为0
                        display_range.cursor_pos = 0;
                        display_range.is_selecting = 1;  // 设置选择模式
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                    }
                    break;
                    
                                case CURSOR_AUTO_SCALE:
                    printf("s0.dis=150\xff\xff\xff"); 
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    
                    // 自动缩放 - 计算当前波段的平均值
                    // 实际应用中，可能需要更复杂的算法来确定缩放比例
                    auto_scale_spectrum();
                    break;
                    
                case CURSOR_RESET_ZOOM:
                {
                    printf("s0.dis=100\xff\xff\xff"); 
                
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    
                    // 获取当前时间
                    uint32_t current_time = HAL_GetTick();
                    
                    // 判断是否在等待长按确认状态
					if(reset_button_pressed && (current_time - reset_button_press_time < LONG_PRESS_DURATION)) {
						// 长按确认 - 清除标定数据
						printf("debug.txt=\"长按确认，清除标定\"\xff\xff\xff");
						
						// 恢复按钮颜色和文本
						printf("reset2.bco=61277\xff\xff\xff");
						printf("reset2.txt=\"重置缩放\"\xff\xff\xff");
                        
                        // 清除标定数据
                        clear_calibration_data();
                    
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 恢复保存的dis参数和Y轴强度范围（使用保存的值）
                        extern uint16_t saved_dis_value;
                        extern uint32_t saved_y_axis_values[6];
                        printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
                        for(int i = 0; i < 6; i++) {
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
                        }
                    
                        // 设置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.zoom_level = 0;
                        display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                        view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                    
                        // 设置t8-t15的显示颜色
                        for(int i = 8; i <= 15; i++) {
                            printf("t%d.pco=0\xff\xff\xff", i);
                            printf("t%d.bco=50779\xff\xff\xff", i);
                        }
                        
                        // 重新绘制波形
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        ProcessAndDisplayGroupData(current_group - 1);
                        
                        // 【修改】重置缩放后，更新p0屏幕位置并更新t1显示（无论是否激活查看坐标功能）
                        printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                        // 【修复】无论是否激活查看坐标功能，都要更新t1的文本内容
                        update_coordinate_display();
                        
                        // 重置长按状态
                        reset_button_pressed = 0;
                        reset_button_press_time = 0;
                    } else {
                        // 第一次点击 - 重置缩放范围和横坐标，并进入等待确认状态
                        printf("debug.txt=\"单击重置缩放\"\xff\xff\xff");
                        
                        // 【关键】保存旧的zoom_level和放大范围（用于判断是否需要重置横坐标和p0映射）
                        int old_zoom_level = display_range.zoom_level;
                        int saved_start_pixel = display_range.current_values[0];  // 保存放大范围的起始像素
                        int saved_end_pixel = display_range.current_values[7];    // 保存放大范围的结束像素
                        
                        // 【修改】重置Y轴强度范围、缩放状态和横坐标
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 恢复默认 dis=100 并设置默认 Y 轴强度范围（10000-60000）
                        extern uint16_t saved_dis_value;
                        extern uint32_t saved_y_axis_values[6];
                        saved_dis_value = 100;
                        printf("s0.dis=100\xff\xff\xff");
                        for(int i = 0; i < 6; i++) {
                            uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                            saved_y_axis_values[i] = intensity_value;
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                        }
                        
                        // 【关键修复】如果之前是放大查看状态，重置横坐标为默认0-3648
                        if(old_zoom_level > 0) {
                            // 恢复横坐标为默认值0-3648
                            if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                // 波长显示模式
                                for(int i = 0; i < 8; i++) {
                                    int pixel_val = DEFAULT_T_VALUES[i];
                                    float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                                    printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                    display_range.current_values[i] = DEFAULT_T_VALUES[i];
                                }
                            } else {
                                // 像素位显示模式
                                for(int i = 0; i < 8; i++) {
                                    printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                                    display_range.current_values[i] = DEFAULT_T_VALUES[i];
                                }
                            }
                        }
                    
                        // 设置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.zoom_level = 0; // 设置放大倍数
                        display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                    
                        // 【修复】重置缩放后，重新透传完整的原始数据到屏幕
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        ProcessAndDisplayGroupData(current_group - 1); // current_group是1-12，数组索引是0-11
                        
                        // 【新增】如果之前是放大状态，需要将p0映射回完整曲线
                        if(old_zoom_level > 0) {
                            int pixel_index_to_restore;
                            
                            // 【新需求】检查是否有保存的屏幕坐标（p0之前不在放大范围内）
                            if(view_coord_state.saved_screen_position >= 0) {
                                // 直接恢复到保存的屏幕坐标（无舍入误差）
                                view_coord_state.p0_position = view_coord_state.saved_screen_position;
                                view_coord_state.saved_screen_position = -1; // 清除保存的值
                                
                                // 计算对应的像素索引（用于后续显示）
                                pixel_index_to_restore = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                                
                                // 【关键修复】保存精确的像素索引，避免后续重新计算时出现舍入误差
                                view_coord_state.saved_full_curve_pixel = pixel_index_to_restore;
                            } else {
                                // p0之前在放大范围内，从放大范围映射回完整曲线
                                // 1. 使用之前保存的放大范围的起始和结束像素值
                                int start_pixel = saved_start_pixel;
                                int end_pixel = saved_end_pixel;
                                
                                // 2. 计算p0在放大范围内的相对位置（0.0-1.0）
                                float relative_pos = (float)(view_coord_state.p0_position - 62) / (791 - 62);
                                
                                // 3. 根据相对位置计算在放大范围内对应的像素索引
                                pixel_index_to_restore = start_pixel + (int)(relative_pos * (end_pixel - start_pixel));
                                
                                // 【关键修复】先保存精确的像素索引，避免后续重新计算时出现舍入误差
                                view_coord_state.saved_full_curve_pixel = pixel_index_to_restore;
                                
                                // 4. 将像素索引映射回完整曲线的屏幕位置
                                view_coord_state.p0_position = 62 + (pixel_index_to_restore * (791 - 62)) / 3648;
                            }
                            
                            // 6. 自动显示p0在正确位置
                            printf("vis p0,1\xff\xff\xff"); // 确保p0可见
                            printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                            
                            // 7. 【修复】无论是否激活查看坐标功能，都要更新t1显示
                            if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                // 波长显示模式
                                float wavelength = saved_calib_params.k * pixel_index_to_restore + saved_calib_params.b;
                                printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
                            } else {
                                // 像素位显示模式
                                printf("t1.txt=\"%d\"\xff\xff\xff", pixel_index_to_restore);
                            }
                        } else {
                            // 【关键修复】如果之前不是放大状态，清除保存的像素索引
                            view_coord_state.saved_full_curve_pixel = -1;
                        }
                        
                        // 【关键】如果之前是放大查看状态，需要更新标定标签位置
                        if(old_zoom_level > 0 && wavelength_display_enabled && saved_calib_params.is_valid) {
                            // 更新标定标签的显示（因为横坐标范围改变了）
                            extern void update_calibration_labels_visibility(void);
                            update_calibration_labels_visibility();
                        }
                        
                        // 标记按钮已按下，变色提示用户"再次点击清除标定"
						reset_button_pressed = 1;
						reset_button_press_time = current_time;
						printf("reset2.bco=61277\xff\xff\xff"); // 红色提示
						printf("reset2.txt=\"清除标定\"\xff\xff\xff"); // 修改按钮文本
					}
					break;
                }
                    
                default:
                    break;
            }
            break;
            
        case INT_TIME_SELECT:
            // 选择积分时间按钮
            printf("a%d.bco=50779\xff\xff\xff", cursor_int_time + 1);
            
            // 发送页面切换命令
            printf("page measure\xff\xff\xff");
            printf("s0.x=62\xff\xff\xff");  // 设置曲线从62位置开始
            page = SPECTRUM_MEASURE;
            cursor_spectrum = CURSOR_INT_TIME;  
            
            // 【修复】恢复自动缩放状态（使用保存的缩放参数）
            extern uint16_t saved_dis_value;
            extern uint32_t saved_y_axis_values[6];
            
            // 恢复dis参数
            printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
            
            // 恢复Y轴强度范围（使用保存的值）
            for(int i = 0; i < 6; i++) {
                printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
            }
            
            // 【新增修复】重新发送存储的曲线数据到屏幕
            extern SpectrumGroupInfo spectrum_groups_info[12];
            extern uint8_t current_group;
            extern volatile uint8_t addt_in_progress;
            
            if(current_group >= 1 && current_group <= 12) {
                uint8_t group_index = current_group - 1;
                
                if(spectrum_groups_info[group_index].is_valid && 
                   spectrum_groups_info[group_index].data_length >= 3640 && 
                   !addt_in_progress) {
                    
                    // 延迟确保页面加载完成
                    for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                        __NOP();
                    }
                    
                    extern void ProcessAndDisplayGroupData(uint8_t group_index);
                    ProcessAndDisplayGroupData(group_index);
                }
            }
            
            // 【新增】更新p0位置（无论是否激活查看坐标功能）
            printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
            
            // 【新增】如果查看坐标功能已激活，根据p0位置更新t1显示
            if(view_coord_state.is_active) {
                update_coordinate_display();
            }
            
            // 更新当前选择的积分时间
            current_int_time = (IntegrationTime)cursor_int_time; // 转换为积分时间
            
            // 发送对应的UART3命令
            UART3_Send_Command(INT_TIME_COMMANDS[current_int_time]);
            
            // 等待积分时间指令生效
            for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
                __NOP(); // 等待约30ms
            }
            
            // 设置当前选择的积分时间显示
            printf("a.txt=\"%s\"\xff\xff\xff", INT_TIME_TEXT[current_int_time]);
            printf("a.bco=61277\xff\xff\xff");
            
            // 如果之前是连续采集模式，则恢复采集
            if(previous_collect_mode_before_int_time == COLLECT_MODE_CONTINUOUS) {
                // 设置当前选择的按钮
                printf("a.bco=50779\xff\xff\xff");      // 获取进入页面按钮
                printf("photo2.bco=61277\xff\xff\xff");  // 设置采集按钮
                cursor_spectrum = CURSOR_CONT_COLLECT;    // 设置采集模式
                
                // 设置采集模式
                current_collect_mode = COLLECT_MODE_CONTINUOUS;
                
                // 使用DMA进行传输
                extern uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE];
                
                // 等待UART3响应（足够长时间）
                for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                    __NOP(); // 等待约100ms
                }
                
                // 检查UART状态
                HAL_StatusTypeDef uart_status;
                int retry_count = 0;
                const int max_retries = 3;
                
                do {
                    // 获取当前UART状态
                    HAL_UART_StateTypeDef current_state = HAL_UART_GetState(&huart3);
                    
                    // 如果UART忙于接收或发送，等待一段时间
                    if(current_state == HAL_UART_STATE_BUSY_RX || current_state == HAL_UART_STATE_BUSY_TX_RX) {
                        // 等待一段时间
                        for(volatile uint32_t delay_count = 0; delay_count < 500000; delay_count++) {
                            __NOP(); // 等待约50ms
                        }
                        
                        // 如果UART状态不是READY，重置UART
                        if(HAL_UART_GetState(&huart3) != HAL_UART_STATE_READY) {
                            HAL_UART_AbortReceive(&huart3);
                            // 重置DMA传输
                            for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
                                __NOP();
                            }
                        }
                    }
                    
                    // 清空缓冲区
                    memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
                    
                    // 使用DMA进行传输
                    uart_status = HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                    
                    if(uart_status == HAL_OK) {
                        break; // 成功，退出循环
                    } else {
                        // 重置UART3
                        MX_USART3_UART_Init();
                        // 重置
                        for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
                            __NOP();
                        }
                    }
                    
                    retry_count++;
                } while(retry_count < max_retries && uart_status != HAL_OK);
                
                // 只发送成功后的A2标志
                if(uart_status == HAL_OK) {
                    // 设置A2标志
                    extern volatile uint8_t need_send_a2_flag;
                    need_send_a2_flag = 1;
                    
                    // 设置调试信息
                    printf("debug.txt=\"连续采集已恢复\"\xff\xff\xff");
                } else {
                    // 如果采集失败，设置当前模式为空闲模式
                    current_collect_mode = COLLECT_MODE_IDLE;
                    printf("a.bco=61277\xff\xff\xff");      // 设置进入页面按钮
                    printf("photo2.bco=50779\xff\xff\xff");  // 获取采集按钮
                    cursor_spectrum = CURSOR_INT_TIME;        // 设置进入页面按钮
                    
                    // 设置调试信息
                    printf("debug.txt=\"连续采集恢复失败\"\xff\xff\xff");
                }
            }
            
            // 重置记录的采集模式状态，无论成功还是失败
            previous_collect_mode_before_int_time = COLLECT_MODE_IDLE;
            break;
            
        case CALIBRATION:
            // 校准按钮
            switch(cursor_calibration1) {
                case CURSOR_SAVE_CALIB:
                    // 保存校准 - 保存当前校准参数
                    if(calib_params.is_valid) {
                        // 只保存当前波形的值
                        saved_calib_params.k = calib_params.k;
                        saved_calib_params.b = calib_params.b;
                        saved_calib_params.r_squared = calib_params.r_squared;
                        saved_calib_params.is_valid = 1; // 设置有效性
                        
                        // 【关键修改】不自动启用波长显示，需要点击switch按钮才切换
                        // wavelength_display_enabled 保持为 0
                        
                        // 保存当前波形
                        printf("saving.bco=50779\xff\xff\xff");  // 取消保存按钮
                        printf("saving.bco=61277\xff\xff\xff");   // 高亮保存按钮
                        
                        // 【关键修改】保存标定参数后，横坐标仍然显示像素值
                        // 只有点击switch按钮确认后才切换为波长显示
                        for(int i = 0; i < 8; i++) {
                            int display_val = DEFAULT_T_VALUES[i]; // 显示横坐标值（0, 500, 1000...）
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, display_val);
                            
                            // 【修复】current_values存储正序像素值（与初始化发送一致）
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
                        }
                        
                        // 【关键修改】z1/z2的可见性取决于wavelength_display_enabled
                        // 标定完成后仍然显示像素位（z1显示，z2隐藏）
                        printf("vis z1,1\xff\xff\xff");    // z1显示（像素位）
                        printf("vis z2,0\xff\xff\xff");    // z2隐藏（波长）
                        
                        // 设置成功信息
                        // printf("t0.txt=\"校准成功\"\xff\xff\xff");
                    }
                    break;
                    
                case CURSOR_INPUT_COEFF:
                    // 输入系数 - 从CH376.TXT文件中读取校准参数
//                    printf("正在初始化U盘...\xff\xff\xff");
                    
                    // 检查CH376
                    if (CH376_TestConnection()) {
                        printf("CH376连接成功\xff\xff\xff");
                        
                        // 设置USB模式
                        xWriteCH376Cmd(CMD_SET_USB_MODE);
                        xWriteCH376Data(0x06);
                        if(xReadCH376Data()==0x51) {
                            if(xReadCH376Data()==0x15) {
                                printf("USB模式设置成功\xff\xff\xff");
                                
                                // 连接设备
                                CH376DiskConnect();
                                if(xReadCH376Data()==USB_INT_SUCCESS) {
                                    printf("设备连接成功\xff\xff\xff");
                                    
                                    // 读取设备
                                    if(CH376DiskMount()==USB_INT_SUCCESS) {
                                        printf("设备挂载成功\xff\xff\xff");
                                        
                                        // 读取校准文件
                                        if(ch376_read_calibration()) {
                                            // 校准文件读取成功，使用保存的校准参数
                                            calib_params.k = saved_calib_params.k;
                                            calib_params.b = saved_calib_params.b;
                                            calib_params.r_squared = saved_calib_params.r_squared;
                                            calib_params.is_valid = 1;
                                            
                                            // 设置t8-t15的值
                                            for(int i = 0; i < 8; i++) {
                                                int pixel_val = DEFAULT_T_VALUES[i]; // 使用默认的像素坐标
                                                float wavelength = calib_params.k * pixel_val + calib_params.b;
                                                printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                                display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【关键】存储像素值（用于标定标签位置计算）
                                            }
                                            
                                            // 设置t7的值
                                            printf("t7.txt=\"%.4f\"\xff\xff\xff", calib_params.r_squared);
                                            
                                            // 设置t8的波长显示
                                            int t8_pixel = DEFAULT_T_VALUES[0]; // t8对应的像素坐标（0）
                                            float t8_wavelength = calib_params.k * t8_pixel + calib_params.b;
                                            printf("t8.txt=\"%.1f\"\xff\xff\xff", t8_wavelength);
                                            
                                            // 设置z1和z2的显示
                                            printf("vis z1,0\xff\xff\xff");
                                            printf("vis z2,1\xff\xff\xff");
                                            
                                            printf("校准参数设置成功\xff\xff\xff");
                                        } else {
                                            printf("校准文件读取失败\xff\xff\xff");
                                        }
                                    } else {
                                        printf("设备挂载失败\xff\xff\xff");
                                    }
                                } else {
                                    printf("设备连接失败\xff\xff\xff");
                                }
                            } else {
                                printf("USB模式设置失败2\xff\xff\xff");
                            }
                        } else {
                            printf("USB模式设置失败1\xff\xff\xff");
                        }
                    } else {
                        printf("CH376连接失败\xff\xff\xff");
                    }
                    break;
                    
                case CURSOR_EXPORT_COEFF_CALIB:
                    // 导出系数至U盘 - 与查询导出界面的导出系数功能一致
                    printf("page outputing\xff\xff\xff");
                    page=OUTPUTING;
                    printf("t2.txt=\"initing..\"\xff\xff\xff");
                    
                    // 初始化CH376，检查返回值
                    if(!ch376_init_with_baudrate_change()) {
                        // 初始化失败，直接显示失败页面
                        printf("page outed\xff\xff\xff");
                        page=OUTPUT_COMPLETE;
                        printf("t1.txt=\"初始化失败!\"\xff\xff\xff");
                        break;
                    }
                    
                    printf("t2.txt=\"writing..\"\xff\xff\xff");
                    if(ch376_export_calibration()) {
											  page=OUTPUT_COMPLETE;
                        printf("page outed\xff\xff\xff");
                        printf("page outed\xff\xff\xff");
                        printf("t1.txt=\"导出完成!\"\xff\xff\xff");
										  	printf("t1.txt=\"导出完成!\"\xff\xff\xff");
                    } else {
										   	page=OUTPUT_COMPLETE;
                        printf("page outed\xff\xff\xff");
                        printf("page outed\xff\xff\xff");
                        printf("t1.txt=\"导出失败!\"\xff\xff\xff");
											  printf("t1.txt=\"导出失败!\"\xff\xff\xff");
                    }
                    break;
                    
                case CURSOR_SELECT_PEAK:
                    // 点击选择峰按钮
                    
                    // 【新增】只有完成6点标定后，才允许重新标定
                    if(calib_params.point_count == 6) {
                        // 隐藏所有标定点 t24-t29
                        for(int i = 24; i <= 29; i++) {
                            printf("vis t%d,0\xff\xff\xff", i);
                        }
                        
                        // 重置标定参数
                        calib_params.point_count = 0;
                        calib_params.current_wavelength_index = 0;
                        calib_params.is_valid = 0;
                        calib_params.selected_wavelength_button = 0;
                        
                        // 隐藏z2，显示z1
                        printf("vis z1,1\xff\xff\xff");
                        printf("vis z2,0\xff\xff\xff");
                        
                        // 【重要】恢复t8-t15为默认的像素位坐标（第二次标定必须恢复）
                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]); // 显示横坐标值
                            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【修复】存储正序像素值（与初始化发送一致）
                        }
                    }
                    
                    // 进入波长选择状态，高亮 t31
                    calib_params.state = CALIB_SELECTING_WAVELENGTH;
                    calib_params.selected_wavelength_button = 0; // 初始选择第一个波长 (t31)
                    
                    // 高亮 t31 - 使用黄色让选中更明显
                    printf("t31.bco=61277\xff\xff\xff");
                    
                    // 取消t5按钮高亮，高亮confirm按钮
                    printf("t5.bco=50779\xff\xff\xff");
                    printf("confirm.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_CONFIRM_POINT;
                    
                    break;
                    
                case CURSOR_CONFIRM_POINT:
                    // 确认按钮
                    
                    // 情况1：在波长选择状态 (CALIB_SELECTING_WAVELENGTH)，点击确认进入标定模式
                    if(calib_params.state == CALIB_SELECTING_WAVELENGTH) {
                        // 【新增修复】取消所有 t31-t36 的高亮，但给正在标定的波长标签特殊显示
                        for(int i = 31; i <= 36; i++) {
                            printf("t%d.bco=50779\xff\xff\xff", i);
                        }
                        
                        // 【新增修复】给正在标定的波长标签特殊的选中显示（使用橙色背景 2016，表示正在标定）
                        int current_wavelength_button = 31 + calib_params.selected_wavelength_button;
                        printf("t%d.bco=2016\xff\xff\xff", current_wavelength_button);
                        
                        // 【核心修改】t31-t36 固定对应 t24-t29 的位置
                        // t31(index=0) → t24, t32(index=1) → t25, ..., t36(index=5) → t29
                        int t_display_index = 24 + calib_params.selected_wavelength_button;
                        float selected_wavelength = CALIBRATION_WAVELENGTHS[calib_params.selected_wavelength_button];
                        
                        // 检查该位置是否已经有标定点（通过波长判断）
                        int is_recalibrating = 0;
                        for(int i = 0; i < calib_params.point_count; i++) {
                            if(calib_params.points[i].lambda == selected_wavelength) {
                                is_recalibrating = 1;
                                // 隐藏对应的显示标签
                                printf("vis t%d,0\xff\xff\xff", t_display_index);
                    break;
                            }
                        }
                        
                        // 进入标定模式 (CALIB_SELECTING_PEAK)
                        calib_params.state = CALIB_SELECTING_PEAK;
                        calib_params.move_speed = 1;
                        calib_params.temp_peak_x = 62; // 初始p0位置
                        
                        // 显示p0
                        printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                        
                        // 保持confirm按钮高亮
                        printf("confirm.bco=61277\xff\xff\xff");
                        cursor_calibration1 = CURSOR_CONFIRM_POINT;
                    }
                    // 情况2：在标定模式 (CALIB_SELECTING_PEAK)，点击确认保存当前峰位置
                    else if(calib_params.state == CALIB_SELECTING_PEAK) {
                        // 【核心修改】t31-t36 固定对应 t24-t29 的位置
                        int t_display_index = 24 + calib_params.selected_wavelength_button;
                        float selected_wavelength = CALIBRATION_WAVELENGTHS[calib_params.selected_wavelength_button];
                        
                        // 【关键】将屏幕坐标转换为实际像素坐标
                        // 屏幕X范围：62-791 (729像素)
                        // 根据是否放大，选择正确的像素范围
                        int display_start, display_end;
                        if(display_range.is_zoomed) {
                            // 放大状态：使用当前放大后的像素范围
                            display_start = display_range.current_values[0];
                            display_end = display_range.current_values[7];
                        } else {
                            // 未放大状态：使用实际像素值（全范围）
                            display_start = ACTUAL_PIXEL_VALUES[0];
                            display_end = ACTUAL_PIXEL_VALUES[7];
                        }
                        
                        // 将屏幕坐标(62-791)转换为实际像素坐标
                        float actual_pixel_x = display_start + (calib_params.temp_peak_x - 62) * (display_end - display_start) / 729.0f;
                        
                        // 检查该波长是否已经标定过
                        int existing_point_index = -1;
                        for(int i = 0; i < calib_params.point_count; i++) {
                            if(calib_params.points[i].lambda == selected_wavelength) {
                                existing_point_index = i;
                                break;
                            }
                        }
                        
                        if(existing_point_index >= 0) {
                            // 【重新标定】更新已有的标定点的x坐标（使用实际像素坐标）
                            calib_params.points[existing_point_index].x = actual_pixel_x;
                            // 波长保持不变
                        } else {
                            // 【新增标定】添加新的标定点（使用实际像素坐标）
                            if(calib_params.point_count < 6) {
                                calib_params.points[calib_params.point_count].x = actual_pixel_x;
                                calib_params.points[calib_params.point_count].lambda = selected_wavelength;
                                calib_params.point_count++;
                            }
                        }
                        
                        // 更新显示标签 t24-t29 的位置（使用屏幕坐标）
                        printf("t%d.x=%d-37\xff\xff\xff", t_display_index, (int)calib_params.temp_peak_x);
                        int y_coordinate = ((calib_params.selected_wavelength_button + 1) % 2 == 1) ? 104 : 79;
                        printf("t%d.y=%d\xff\xff\xff", t_display_index, y_coordinate);
                        
                        // 显示 t24-t29
                        printf("vis t%d,1\xff\xff\xff", t_display_index);
                        
                        // 如果已有2个或更多标定点，应用校准
                        if(calib_params.point_count >= 2) {
                            auto_apply_calibration();
                        }
                        
                        // 返回到 IDLE 状态
                        calib_params.state = CALIB_IDLE;
                        
                        // 【新增修复】取消正在标定的波长标签的特殊显示，恢复为普通背景色
                        int current_wavelength_button = 31 + calib_params.selected_wavelength_button;
                        printf("t%d.bco=50779\xff\xff\xff", current_wavelength_button);
                        
                        // 返回到选择峰按钮
                        printf("confirm.bco=50779\xff\xff\xff");
                        printf("t5.bco=61277\xff\xff\xff");
                        cursor_calibration1 = CURSOR_SELECT_PEAK;
                    }
                    break;
                    
                case CURSOR_SWITCH_CALIB:
                    // 点击切换按钮 - 切换横坐标显示模式（像素位 <-> 波长）
                    
                    // 只有标定数据有效时才能切换
                    if(saved_calib_params.is_valid) {
                        // 切换显示模式
                        wavelength_display_enabled = !wavelength_display_enabled;
                        
                        // 【关键修复】更新t8-t15的显示：根据是否放大状态决定使用的像素范围
                        for(int i = 0; i < 8; i++) {
                            int pixel_val;
                            
                            // 【新增】检查是否处于放大状态
                            if(display_range.is_zoomed) {
                                // 放大状态：使用当前放大区域的像素值
                                pixel_val = display_range.current_values[i];
                            } else {
                                // 未放大状态：使用默认的0-3500范围
                                pixel_val = DEFAULT_T_VALUES[i];
                            }
                            
                            if(wavelength_display_enabled) {
                                // 显示波长（使用实际的像素值计算）
                                float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                                printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            } else {
                                // 显示像素位
                                printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, pixel_val);
                            }
                            
                            // 【修复】只有在未放大状态下才更新current_values为默认值
                            if(!display_range.is_zoomed) {
                                display_range.current_values[i] = DEFAULT_T_VALUES[i];
                            }
                            // 放大状态下，current_values保持不变（已经是放大区域的值）
                        }
                        
                        // 更新z1和z2的可见性
                        if(wavelength_display_enabled) {
                            // 波长模式：显示z2，隐藏z1
                            printf("vis z1,0\xff\xff\xff");    // z1隐藏（像素位）
                            printf("vis z2,1\xff\xff\xff");    // z2显示（波长）
                        } else {
                            // 像素位模式：显示z1，隐藏z2
                            printf("vis z1,1\xff\xff\xff");    // z1显示（像素位）
                            printf("vis z2,0\xff\xff\xff");    // z2隐藏（波长）
                        }
                    }
                    break;
                    
                case CURSOR_ZOOM_CALIB:
                    // 标定界面的放大查看功能
                    cursor_calibration1 = CURSOR_ZOOM_CALIB;
                    
                    // 如果已经在选择模式
                    if(display_range.is_selecting) {
                        // 当前光标位置
                        int current_pos = (int)display_range.cursor_pos;
                        
                        // 如果第一个点还未选中
                        if(display_range.first_selected == -1) {
                            // 选中第一个点
                            display_range.first_selected = current_pos;
                            // 【修复】高亮显示选中的标签为红色
                            printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文字（RGB565: 63488）
                        }
                        // 如果第一个点已选中，但第二个点未选中
                        else if(display_range.second_selected == -1) {
                            // 确保选择不同的点
                            if(current_pos != display_range.first_selected) { 
                                // 选中第二个点
                                display_range.second_selected = current_pos;
                                // 【修复】高亮显示选中的标签为红色
                                printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文字（RGB565: 63488）
                                
                                // 获取选择的范围值
                                int first_idx = display_range.first_selected;
                                int second_idx = display_range.second_selected;
                                
                                // 【关键】current_values中存储的是像素值（不是屏幕显示值）
                                int start_pixel, end_pixel;
                                
                                // 确保start_pixel <= end_pixel
                                if(display_range.current_values[first_idx] <= display_range.current_values[second_idx]) {
                                    start_pixel = display_range.current_values[first_idx];
                                    end_pixel = display_range.current_values[second_idx];
                                } else {
                                    start_pixel = display_range.current_values[second_idx];
                                    end_pixel = display_range.current_values[first_idx];
                                }
                                
                                // 生成8个新的横坐标值（像素值和显示值）
                                for(int i = 0; i < 8; i++) {
                                    int new_pixel_val;  // 像素值（用于存储）
                                    
                                    if(i == 7) {
                                        // 最后一个值
                                        new_pixel_val = end_pixel;
                                    } else {
                                        // 线性插值
                                        new_pixel_val = start_pixel + (end_pixel - start_pixel) * i / 7;
                                    }
                                    
                                    // 显示值
                                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                        // 波长显示模式：显示波长，但存储像素值
                                        float wavelength = saved_calib_params.k * new_pixel_val + saved_calib_params.b;
                                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                    } else {
                                        // 像素位显示模式：显示像素值，存储像素值
                                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, new_pixel_val);
                                    }
                                    
                                    // 【关键】存储像素值（用于标定标签位置计算和下次放大）
                                    display_range.current_values[i] = new_pixel_val;
                                }
                                
                                // 增加放大级别
                                if(display_range.zoom_level < 2) {
                                    display_range.zoom_level++;
                                }
                                
                                // 恢复t8-t15的显示颜色
                                for(int i = 8; i <= 15; i++) {
                                    printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                                    printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景色
                                }
                                
                                // 处理缩放数据（重新显示当前光谱数据的缩放部分）
                                ProcessZoomData(start_pixel, end_pixel);
                                
                                // 【关键修复】设置放大状态标志
                                display_range.is_zoomed = 1;
                                
                                // 【修复】标定界面的放大查看不影响p0
                                // 标定界面使用自己的p0坐标系统（calib_params.temp_peak_x: 73-793）
                                // 查看坐标功能仅在测量界面使用，标定界面不需要隐藏p0
                                
                                // 更新标定标签的可见性（根据缩放范围）
                                update_calibration_labels_visibility();
                                
                                // 重置选择状态
                                display_range.is_selecting = 0;
                                display_range.first_selected = -1;
                                display_range.second_selected = -1;
                            }
                            // 如果选择了相同的点，则不执行任何操作
                        }
                    } else {
                        // 进入选择模式
                        printf("t8.bco=61277\xff\xff\xff");  // 高亮第一个标签
                        
                        // 初始化选择状态
                        display_range.cursor_pos = 0;
                        display_range.is_selecting = 1;  // 设置选择模式
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                    }
                    break;
                    
                case CURSOR_RESET_CALIB:
                    // 标定界面的重置缩放功能（支持长按确认）
                    cursor_calibration1 = CURSOR_RESET_CALIB;
                    
                    // 获取当前时间
                    uint32_t current_time_calib = HAL_GetTick();
                    
                    // 判断是否在等待长按确认状态
					if(reset_button_pressed && (current_time_calib - reset_button_press_time < LONG_PRESS_DURATION)) {
						// 长按确认 - 清除标定数据
						printf("debug.txt=\"长按确认，清除标定\"\xff\xff\xff");
						
						// 恢复按钮颜色和文本
						printf("reset2.bco=61277\xff\xff\xff");
						printf("reset2.txt=\"重置缩放\"\xff\xff\xff");
                        
                        // 清除标定数据
                        clear_calibration_data();
                        
                        // 重置缩放状态
                        display_range.zoom_level = 0;
                        display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                        view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                        
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 设置Y轴强度范围（10000-60000）
                        for(int i = 0; i < 6; i++) {
                            uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                        }
                        
                        // 设置t8-t15的显示颜色
                        for(int i = 8; i <= 15; i++) {
                            printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                            printf("t%d.bco=50779\xff\xff\xff", i); // 灰色背景
                        }
                        
                        // 重置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.cursor_pos = 0;
                        
                        // 重新绘制波形（使用完整数据，统一使用 ProcessAndDisplayGroupData）
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        extern SpectrumGroupInfo spectrum_groups_info[12];
                        extern volatile uint8_t addt_in_progress;
                        if(current_group >= 1 && current_group <= 12) {
                            uint8_t group_index = current_group - 1;
                            if(spectrum_groups_info[group_index].is_valid && 
                               spectrum_groups_info[group_index].data_length >= 3640 && 
                               !addt_in_progress) {
                                // 透传完整数据到屏幕，保持与测量页面一致的行为
                                ProcessAndDisplayGroupData(group_index);
                            }
                        }
                        
                        // 【关键修复】重置放大状态标志
                        display_range.is_zoomed = 0;
                        
                        // 【新增】如果查看坐标功能已激活，根据p0位置更新t1显示
                        if(view_coord_state.is_active) {
                            update_coordinate_display();
                        }
                        
                        // 重置长按状态
                        reset_button_pressed = 0;
                        reset_button_press_time = 0;
                    } else {
                        // 第一次点击 - 仅重置缩放范围，保持标定状态，并进入等待确认状态
                        printf("debug.txt=\"单击重置缩放\"\xff\xff\xff");
                        
                        // 【关键】保存旧的zoom_level和放大范围（用于判断是否需要映射p0）
                        int old_zoom_level = display_range.zoom_level;
                        int saved_start_pixel = display_range.current_values[0];  // 保存放大范围的起始像素
                        int saved_end_pixel = display_range.current_values[7];    // 保存放大范围的结束像素
                        
                        // 重置缩放状态
                        display_range.zoom_level = 0;
                        
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 恢复默认 dis=100 并设置默认 Y 轴强度范围（10000-60000）
                        extern uint16_t saved_dis_value;
                        extern uint32_t saved_y_axis_values[6];
                        saved_dis_value = 100;
                        printf("s0.dis=100\xff\xff\xff");
                        for(int i = 0; i < 6; i++) {
                            uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                            saved_y_axis_values[i] = intensity_value;
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                        }
                        
                        // 设置t8-t15的默认值（根据wavelength_display_enabled标志）
                        if(wavelength_display_enabled && saved_calib_params.is_valid) {
                            // 波长显示模式：显示波长，但存储像素值
                            printf("vis z1,0\xff\xff\xff");    // z1隐藏
                            printf("vis z2,1\xff\xff\xff");    // z2显示
                            
                            for(int i = 0; i < 8; i++) {
                                int pixel_val = DEFAULT_T_VALUES[i]; // 默认的像素坐标
                                float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                                printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【关键】存储像素值（用于标定标签位置计算）
                            }
                        } else {
                            // 像素位显示模式：显示像素值，存储像素值
                            printf("vis z1,1\xff\xff\xff");    // z1显示
                            printf("vis z2,0\xff\xff\xff");    // z2隐藏
                            
                            for(int i = 0; i < 8; i++) {
                                printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                                display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                            }
                        }
                        
                        // 设置t8-t15的显示颜色
                        for(int i = 8; i <= 15; i++) {
                            printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                            printf("t%d.bco=50779\xff\xff\xff", i); // 灰色背景
                        }
                        
                        // 重置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.cursor_pos = 0;
                        
                        // 重新绘制波形（使用完整数据，统一使用 ProcessAndDisplayGroupData）
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        extern SpectrumGroupInfo spectrum_groups_info[12];
                        extern volatile uint8_t addt_in_progress;
                        if(current_group >= 1 && current_group <= 12) {
                            uint8_t group_index = current_group - 1;
                            if(spectrum_groups_info[group_index].is_valid && 
                               spectrum_groups_info[group_index].data_length >= 3640 && 
                               !addt_in_progress) {
                                ProcessAndDisplayGroupData(group_index);
                            }
                        }
                        
                        // 【关键修复】重置放大状态标志
                        display_range.is_zoomed = 0;
                        
                        // 【修复】标定界面不需要p0映射处理
                        // 标定界面使用独立的p0坐标系统（calib_params.temp_peak_x: 73-793）
                        // p0在标定过程中由用户手动移动，重置缩放不影响p0位置
                        
                        // 更新标定标签的可见性（重置缩放后显示所有标签）
                        update_calibration_labels_visibility();
                        
                        // 标记按钮已按下，变色提示用户"再次点击清除标定"
						reset_button_pressed = 1;
						reset_button_press_time = current_time_calib;
						printf("reset2.bco=61277\xff\xff\xff"); // 红色提示
						printf("reset2.txt=\"清除标定\"\xff\xff\xff"); // 修改按钮文本
					}
					break;
                    
                default:
                    break;
            }
            break;
            
        case WAVELENGTH_SELECT:
            // 选择波长按钮
            if(calib_params.state == CALIB_SELECTING_WAVE) {
                // 获取选择的波长值
                float selected_wavelength = CALIBRATION_WAVELENGTHS[cursor_wavelength];
                
                // 设置校准信息
                if(calib_params.point_count < 10) { // 如果选择的波段数量小于10
                    calib_params.points[calib_params.point_count].x = calib_params.temp_peak_x;
                    calib_params.points[calib_params.point_count].lambda = selected_wavelength;
                    calib_params.point_count++;
                }
                
                // 设置校准信息
                printf("page calibration\xff\xff\xff");
                page = CALIBRATION;
                
                // 设置状态
                calib_params.state = CALIB_IDLE;
                
                // 设置t0和t1的值
                
                // 如果选择的波段数量大于等于2，则设置校准信息
                if(calib_params.point_count >= 2) {
                    // 计算平均值
                    float sum_x = 0, sum_y = 0, sum_xy = 0, sum_xx = 0;
                    for(int i = 0; i < calib_params.point_count; i++) {
                        sum_x += calib_params.points[i].x;
                        sum_y += calib_params.points[i].lambda;
                        sum_xy += calib_params.points[i].x * calib_params.points[i].lambda;
                        sum_xx += calib_params.points[i].x * calib_params.points[i].x;
                    }
                    
                    float n = calib_params.point_count;
                    calib_params.k = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x);
                    calib_params.b = (sum_y - calib_params.k * sum_x) / n;
                    
                    // 设置校准有效性
                    calib_params.is_valid = 1;
                }
            }
            break; 
            
        case QUERY_EXPORT:
            // query按钮的设置（查询导出界面）
            switch(cursor_spectrum) {
                case CURSOR_EXPORT_USB:
                // 设置输出页面
                printf("page outputing\xff\xff\xff");
                page=OUTPUTING;
                printf("t2.txt=\"initing..\"\xff\xff\xff");
                
                // 初始化CH376，检查返回值
                if(!ch376_init_with_baudrate_change()) {
                    // 初始化失败，直接显示失败页面
                    printf("page outed\xff\xff\xff");
                    page=OUTPUT_COMPLETE;
                    printf("t1.txt=\"初始失败!\"\xff\xff\xff");
                    break;
                }
                
                printf("t2.txt=\"writing..\"\xff\xff\xff");
                ch376_writetest();  // 检查是否连接到设备
                printf("page outed\xff\xff\xff");
                page=OUTPUT_COMPLETE;
                if(output_flag) printf("t1.txt=\"导出完成!\"\xff\xff\xff");
                else printf("t1.txt=\"导出失败!\"\xff\xff\xff");
                    break;
                    
                case CURSOR_EXPORT_COEFF:
                // 设置校准参数按钮
                printf("page outputing\xff\xff\xff");
                page=OUTPUTING;
                printf("t2.txt=\"initing..\"\xff\xff\xff");
                
                // 初始化CH376，检查返回值
                if(!ch376_init_with_baudrate_change()) {
                    // 初始化失败，直接显示失败页面
                    printf("page outed\xff\xff\xff");
                    page=OUTPUT_COMPLETE;
                    printf("t1.txt=\"初始失败!\"\xff\xff\xff");
                    break;
                }
                
                printf("t2.txt=\"writing..\"\xff\xff\xff");
                if(ch376_export_calibration()) {
                    printf("page outed\xff\xff\xff");
                    page=OUTPUT_COMPLETE;
                    printf("t1.txt=\"导出完成!\"\xff\xff\xff");
                } else {
                    printf("page outed\xff\xff\xff");
                    page=OUTPUT_COMPLETE;
                    printf("t1.txt=\"导出失败!\"\xff\xff\xff");
                }
                    break;
                    
                case CURSOR_ZOOM:  // 【查询导出界面】放大查看
                    // 放大查看
                    cursor_spectrum = CURSOR_ZOOM;
                    
                    // 当前选择的模式下，没有选择波段
                    if(display_range.is_selecting) {
                        // 当前选择的波段
                        int current_pos = (int)display_range.cursor_pos;
                        
                        // 当前选择的波段没有选择
                        if(display_range.first_selected == -1) {
                            // 选择第一个波段
                            display_range.first_selected = current_pos;
                            // 设置当前选择的按钮
                            printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 【修复】红色文字（RGB565: 63488）
                        }
                        // 当前选择的波段没有选择
                        else if(display_range.second_selected == -1) {
                            // 选择不同的波段
                            if(current_pos != display_range.first_selected) { 
                                // 选择第二个波段
                                display_range.second_selected = current_pos;
                                // 设置当前选择的按钮
                                printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 【修复】红色文字（RGB565: 63488）
                                
                                // 获取选择的波段值
                                int first_idx = display_range.first_selected;
                                int second_idx = display_range.second_selected;
                                
                                // current_values中存储的是屏幕显示值（标定后是波长，未标定是像素）
                                int start_display_val, end_display_val;
                                int start_idx, end_idx;
                                
                                // 确保start_val <= end_val
                                if(display_range.current_values[first_idx] <= display_range.current_values[second_idx]) {
                                    start_display_val = display_range.current_values[first_idx];
                                    end_display_val = display_range.current_values[second_idx];
                                    start_idx = first_idx;
                                    end_idx = second_idx;
                                } else {
                                    start_display_val = display_range.current_values[second_idx];
                                    end_display_val = display_range.current_values[first_idx];
                                    start_idx = second_idx;
                                    end_idx = first_idx;
                                }
                                
                                // 【关键】current_values存储的是像素值，直接使用
                                int start_pixel = start_display_val;
                                int end_pixel = end_display_val;
                                
                                // 设置放大倍数
                                display_range.zoom_level++;
                                
                                // 生成8个新的横坐标值（像素值和显示值）
                                for(int i = 0; i < 8; i++) {
                                    int new_pixel_val;  // 像素值（用于存储）
                                    
                                    if(i == 7) {
                                        // 最后一个值
                                        new_pixel_val = end_pixel;
                                    } else {
                                        // 线性插值
                                        new_pixel_val = start_pixel + (end_pixel - start_pixel) * i / 7;
                                    }
                                    
                                    // 显示值
                                    if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                        // 波长显示模式：显示波长，但存储像素值
                                        float wavelength = saved_calib_params.k * new_pixel_val + saved_calib_params.b;
                                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                    } else {
                                        // 像素位显示模式：显示像素值，存储像素值
                                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, new_pixel_val);
                                    }
                                    
                                    // 【关键】存储像素值（用于标定标签位置计算和下次放大）
                                    display_range.current_values[i] = new_pixel_val;
                                }
                                
                                // 设置t8-t15的显示颜色
                                for(int i = 8; i <= 15; i++) {
                                    printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                                    printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景色
                                }
                                
                                // 处理缩放数据（传入像素值）
                                ProcessZoomData(start_pixel, end_pixel);
                                
                                // 【关键修复】设置放大状态标志
                                display_range.is_zoomed = 1;
                                
                                // 【修复】查询导出界面没有p0功能和查看坐标功能，不需要处理
                                
                                // 重置选择状态
                                display_range.is_selecting = 0;
                                display_range.first_selected = -1;
                                display_range.second_selected = -1;
                            }
                        }
                    } else {
                        // 初始化t8
                        printf("t8.bco=61277\xff\xff\xff");  // 初始化第一个波段
                        
                        // 当前选择的按钮对应的t8值为0
                        display_range.cursor_pos = 0;
                        display_range.is_selecting = 1;  // 设置选择模式
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                    }
                    break;
                    
                case CURSOR_AUTO_SCALE:
                    // 自动缩放
                    printf("s0.dis=150\xff\xff\xff"); 
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    auto_scale_spectrum();
                    break;
                    
                case CURSOR_RESET_ZOOM:
                    // 重置缩放（支持长按确认）
                    printf("s0.dis=100\xff\xff\xff"); 
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    
                    // 获取当前时间
                    uint32_t current_time_query = HAL_GetTick();
                    
                    // 判断是否在等待长按确认状态
					if(reset_button_pressed && (current_time_query - reset_button_press_time < LONG_PRESS_DURATION)) {
						// 长按确认 - 清除标定数据
						printf("debug.txt=\"长按确认，清除标定\"\xff\xff\xff");
						
						// 恢复按钮颜色和文本
						printf("reset2.bco=61277\xff\xff\xff");
						printf("reset2.txt=\"重置缩放\"\xff\xff\xff");
                        
                        // 清除标定数据
                        clear_calibration_data();
                    
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 设置Y轴强度范围（10000-60000）
                        for(int i = 0; i < 6; i++) {
                            uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                        }
                    
                        // 设置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.zoom_level = 0;
                        display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                        view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                    
                        // 重新绘制波形
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        ProcessAndDisplayGroupData(current_group - 1);
                        
                        // 【修改】重置缩放后，更新p0屏幕位置并更新t1显示（无论是否激活查看坐标功能）
                        printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                        // 【修复】无论是否激活查看坐标功能，都要更新t1的文本内容
                        update_coordinate_display();
                        
                        // 重置长按状态
                        reset_button_pressed = 0;
                        reset_button_press_time = 0;
                    } else {
                        // 第一次点击 - 仅重置缩放范围，不重置横坐标，并进入等待确认状态
                        printf("debug.txt=\"单击重置缩放\"\xff\xff\xff");
                        
                        // 【关键】保存旧的zoom_level和放大范围（用于判断是否需要映射p0）
                        int old_zoom_level_query = display_range.zoom_level;
                        int saved_start_pixel_query = display_range.current_values[0];  // 保存放大范围的起始像素
                        int saved_end_pixel_query = display_range.current_values[7];    // 保存放大范围的结束像素
                        
                        // 【关键】只重置Y轴强度范围和缩放状态，不重置横坐标
                        // 【修复】不修改t8文本内容，保持横坐标不变
                        
                        // 设置Y轴强度范围（10000-60000）
                        for(int i = 0; i < 6; i++) {
                            uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                            printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                        }
                        
                        // 设置选择状态
                        display_range.is_selecting = 0;
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                        display_range.zoom_level = 0;
                        display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                        view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                        
                        // 【修复】重置缩放后，重新透传完整的原始数据到屏幕
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        ProcessAndDisplayGroupData(current_group - 1); // current_group是1-12，数组索引是0-11
                        
                        // 【修复】查询导出界面没有p0功能，不需要处理p0映射
                        
                        // 【新增】如果之前是放大状态，需要恢复横坐标为完整范围
                        if(old_zoom_level_query > 0) {
                            // 恢复横坐标为默认值0-3648
                            if(wavelength_display_enabled && saved_calib_params.is_valid) {
                                // 波长显示模式
                                for(int i = 0; i < 8; i++) {
                                    int pixel_val = DEFAULT_T_VALUES[i];
                                    float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                                    printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                    display_range.current_values[i] = DEFAULT_T_VALUES[i];
                                }
                            } else {
                                // 像素位显示模式
                                for(int i = 0; i < 8; i++) {
                                    printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                                    display_range.current_values[i] = DEFAULT_T_VALUES[i];
                                }
                            }
                        }
                        
                        // 【关键】单击重置缩放不应该调用update_calibration_labels_visibility()
                        // 因为横坐标在这里已经手动恢复了，不需要再调用标签更新函数
                        
                        // 标记按钮已按下，变色提示用户"再次点击清除标定"
						reset_button_pressed = 1;
						reset_button_press_time = current_time_query;
						printf("reset2.bco=61277\xff\xff\xff"); // 红色提示
						printf("reset2.txt=\"清除标定\"\xff\xff\xff"); // 修改按钮文本
					}
					break;
                    
                case CURSOR_CALIBRATION:
                    // 页面切换：设置锁，切换页面，解锁
                    {
                        extern volatile uint8_t page_switching_lock;
                        extern volatile uint8_t data_processing_done;
                        
                        // 1. 设置页面切换锁，阻止新的数据处理
                        page_switching_lock = 1;
                        
                        // 2. 等待当前数据处理完成（最多等待500ms）
                        uint32_t wait_count = 0;
                        while(!data_processing_done && wait_count < 5000000) {
                            __NOP();
                            wait_count++;
                        }
                        
                        // 3. 短暂延迟确保数据处理完全结束
                        for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                            __NOP();
                        }
                        
                        // 4. 切换到标定界面
                        printf("page calibration\xff\xff\xff");
                        page = CALIBRATION;
                        
                        // 5. 初始化calibration页面
                        calibration_page_init();
                        
                        // 6. 延迟确保页面初始化完成
                        for(volatile uint32_t delay_count = 0; delay_count < 500000; delay_count++) {
                            __NOP();
                        }
                        
                        // 7. 解除页面切换锁，允许数据处理继续
                        page_switching_lock = 0;
                    }
                    break;
                    
                default:
                    break;
            }
            break;
            
        case OUTPUT_COMPLETE:
            // 显示当前页面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
            
        default:
            break;
    }
}

// 取消按钮
void cancel_button(void) {
    switch(page) {
        case MAIN:
            // 取消水印功能
            break;
            
        case SPECTRUM_MEASURE:
            // 如果处于查看坐标状态，退出查看坐标状态
            if(view_coord_state.is_active) {
                // 退出查看坐标状态（但不隐藏p0和t1控件）
                view_coord_state.is_active = 0;
                
                // 更新t7文本为"关"
                printf("t7.txt=\"关\"\xff\xff\xff");
                
                return; // 处理完毕，直接返回
            }
            
            // 如果选择了波段和模式，则取消选择
            if(display_range.is_selecting && cursor_spectrum == CURSOR_ZOOM) {
                // 取消选择
                display_range.is_selecting = 0;
                display_range.first_selected = -1;
                display_range.second_selected = -1;
                
                // 重置t8-t16按钮的显示
                for(int i = 8; i <= 16; i++) {
                    printf("t%d.bco=50779\xff\xff\xff", i);
                    printf("t%d.pco=0\xff\xff\xff", i); // 重置t8-t16按钮的颜色
                }
                
                // 重置zoom按钮
                printf("zoom.bco=61277\xff\xff\xff");
            } else {
                // 如果没有选择任何按钮，则取消选择
                switch(cursor_spectrum) {
                    // CURSOR_GROUP case
                    case CURSOR_INT_TIME:
                        printf("a.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_SINGLE_COLLECT:
                        printf("photo1.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_CONT_COLLECT:
                        printf("photo2.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_PAUSE_COLLECT:
                        printf("pause.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_SAVE_SPECTRUM:
                        printf("data_record.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_CALIBRATION:
                        printf("paging.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_ZOOM:
                        printf("zoom.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_AUTO_SCALE:
                        printf("reset1.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_RESET_ZOOM:
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为灰色
                            printf("reset2.bco=50779\xff\xff\xff");
                        }
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_EXPORT_COEFF:
                        printf("coeff.bco=50779\xff\xff\xff");
                        break;
                    default:
                        break;
                }
                
                // 重置页面
                printf("page main\xff\xff\xff");
                page = MAIN;
                cursor_main = CALIBO;  // 默认选择进入页面
                printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            }
            break;
            
        case CALIBRATION:
            // 【新增】如果在zoom选择模式，取消选择
            if(cursor_calibration1 == CURSOR_ZOOM_CALIB && display_range.is_selecting) {
                // 取消选择
                display_range.is_selecting = 0;
                display_range.first_selected = -1;
                display_range.second_selected = -1;
                
                // 重置t8-t15按钮的显示
                for(int i = 8; i <= 15; i++) {
                    printf("t%d.bco=50779\xff\xff\xff", i);
                    printf("t%d.pco=0\xff\xff\xff", i); // 重置颜色
                }
                
                // 保持zoom按钮高亮
                printf("zoom.bco=61277\xff\xff\xff");
                return; // 直接返回，不继续执行
            }
            
            // 【新增】如果在波长选择状态，返回到IDLE状态
            if(calib_params.state == CALIB_SELECTING_WAVELENGTH) {
                // 取消所有 t31-t36 的高亮
                for(int i = 31; i <= 36; i++) {
                    printf("t%d.bco=50779\xff\xff\xff", i);
                }
                
                // 退出波长选择状态
                calib_params.state = CALIB_IDLE;
                
                // 切换回选择峰按钮
                printf("confirm.bco=50779\xff\xff\xff");  // 取消确认按钮高亮
                printf("t5.bco=61277\xff\xff\xff");       // 高亮选择峰按钮
                cursor_calibration1 = CURSOR_SELECT_PEAK;
                return; // 直接返回
            }
            
            // 如果正在选择峰（无论光标在哪个按钮），都应该退出选择峰状态
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 【修改】如果已经标定了2个或更多点，自动应用校准
                if(calib_params.point_count >= 2) {
                    auto_apply_calibration();
                }
                
                // 退出选择峰状态
                calib_params.state = CALIB_IDLE;
                
                // 【新增修复】取消正在标定的波长标签的特殊显示，恢复为普通背景色
                int current_wavelength_button = 31 + calib_params.selected_wavelength_button;
                printf("t%d.bco=50779\xff\xff\xff", current_wavelength_button);
                
                // 如果当前在确认按钮，切换回选择峰按钮
                if(cursor_calibration1 == CURSOR_CONFIRM_POINT) {
                    printf("confirm.bco=50779\xff\xff\xff");  // 取消确认按钮高亮
                    printf("t5.bco=61277\xff\xff\xff");       // 高亮选择峰按钮
                    cursor_calibration1 = CURSOR_SELECT_PEAK;
                }
                // 如果已经在选择峰按钮，保持不变
            } else {
                // 不在选择峰状态，则返回主页面
                // 取消当前按钮的高亮
                switch(cursor_calibration1) {
                    case CURSOR_SAVE_CALIB:
                        printf("saving.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_INPUT_COEFF:
                        printf("input.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_EXPORT_COEFF_CALIB:
                        printf("coeff.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_SELECT_PEAK:
                        printf("t5.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_CONFIRM_POINT:
                        printf("confirm.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_SWITCH_CALIB:
                        printf("switch.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_ZOOM_CALIB:
                        printf("zoom.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_RESET_CALIB:
                        printf("reset2.bco=50779\xff\xff\xff");
                        break;
                    default:
                        break;
                }
                
                // 切换回测量页面
                printf("page measure\xff\xff\xff");
                printf("s0.x=62\xff\xff\xff");  // 设置曲线从62位置开始
                page = SPECTRUM_MEASURE;
                cursor_spectrum = CURSOR_CALIBRATION;
                printf("paging.bco=61277\xff\xff\xff");
                
                // 【修复】恢复p0位置（保证即使退出过标定也能查看坐标）
                printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                
                // 【修复】恢复自动缩放状态（使用保存的缩放参数）
                extern uint16_t saved_dis_value;
                extern uint32_t saved_y_axis_values[6];
                
                // 恢复dis参数
                printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
                
                // 恢复Y轴强度范围（使用保存的值）
                for(int i = 0; i < 6; i++) {
                    printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
                }
                
                // 【关键修复】如果之前进行过放大操作，重置放大状态
                if(display_range.zoom_level > 0) {
                    // 重置选择状态和放大级别
                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    display_range.zoom_level = 0;
                    display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
                    view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
                    
                    // 重置current_values为默认值
                    for(int i = 0; i < 8; i++) {
                        display_range.current_values[i] = DEFAULT_T_VALUES[i];
                    }
                    
                    // 恢复t8-t15的标签颜色
                    for(int i = 8; i <= 15; i++) {
                        printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                        printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景色
                    }
                }
                
                // 【关键修复】无论是否进行过放大操作，都应该根据wavelength_display_enabled标志更新横坐标
                // 这样点击switch按钮确认后返回，横坐标就能保持正确显示
                if(wavelength_display_enabled && saved_calib_params.is_valid) {
                    // 波长显示模式
                    printf("vis z1,0\xff\xff\xff");    // z1不可见
                    printf("vis z2,1\xff\xff\xff");    // z2可见
                    
                    // 更新t8-t15为波长值
                    for(int i = 0; i < 8; i++) {
                        int pixel_val = DEFAULT_T_VALUES[i]; // 使用默认的像素坐标
                        float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                        display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【关键】存储像素值（用于标定标签位置计算）
                    }
                    
                    // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                    // 计算并更新t1显示的波长值（基于当前p0位置）
                    int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                    if(pixel_index < 0) pixel_index = 0;
                    if(pixel_index > 3648) pixel_index = 3648;
                    
                    float wavelength = saved_calib_params.k * pixel_index + saved_calib_params.b;
                    printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
                    
                    // 如果正在查看坐标状态，显示t1/p0控件
                    if(view_coord_state.is_active) {
                        printf("vis p0,1\xff\xff\xff");
                        printf("vis t1,1\xff\xff\xff");
                    }
                } else {
                    // 像素位显示模式
                    printf("vis z1,1\xff\xff\xff");    // z1可见
                    printf("vis z2,0\xff\xff\xff");    // z2不可见
                    
                    // 更新t8-t15为像素值
                    for(int i = 0; i < 8; i++) {
                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                        display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                    }
                    
                    // 【修复】无论是否激活查看坐标，都更新t1的数值状态
                    // 计算并更新t1显示的像素值（基于当前p0位置）
                    int pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
                    if(pixel_index < 0) pixel_index = 0;
                    if(pixel_index > 3648) pixel_index = 3648;
                    
                    printf("t1.txt=\"%d\"\xff\xff\xff", pixel_index);
                    
                    // 如果正在查看坐标状态，显示t1/p0控件
                    if(view_coord_state.is_active) {
                        printf("vis p0,1\xff\xff\xff");
                        printf("vis t1,1\xff\xff\xff");
                    }
                }
                
                // 重新显示当前组的数据
                extern SpectrumGroupInfo spectrum_groups_info[12];
                extern uint8_t current_group;
                extern volatile uint8_t addt_in_progress;
                
                if(current_group >= 1 && current_group <= 12) {
                    uint8_t group_index = current_group - 1;
                    
                    if(spectrum_groups_info[group_index].is_valid && 
                       spectrum_groups_info[group_index].data_length >= 3640 && 
                       !addt_in_progress) {
                        
                        // 延迟确保页面加载完成
                        for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                            __NOP();
                        }
                        
                        ProcessAndDisplayGroupData(group_index);
                    }
                }
            }
            break;
            
        case QUERY_EXPORT:
            // 如果选择了波段和模式，则取消选择
            if(display_range.is_selecting && cursor_spectrum == CURSOR_ZOOM) {
                // 取消选择
                display_range.is_selecting = 0;
                display_range.first_selected = -1;
                display_range.second_selected = -1;
                
                // 重置t8-t15按钮的显示
                for(int i = 8; i <= 15; i++) {
                    printf("t%d.bco=50779\xff\xff\xff", i);
                    printf("t%d.pco=0\xff\xff\xff", i); // 重置t8-t15按钮的颜色
                }
                
                // 重置zoom按钮
                printf("zoom.bco=61277\xff\xff\xff");
            } else {
                // 如果没有选择任何按钮，则取消选择
                switch(cursor_spectrum) {
                    case CURSOR_CALIBRATION:
                        printf("paging.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_ZOOM:
                        printf("zoom.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_AUTO_SCALE:
                        printf("reset1.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_RESET_ZOOM:
                        // 【修复】检查是否在红色等待状态
                        if(reset_button_pressed && (HAL_GetTick() - reset_button_press_time < LONG_PRESS_DURATION)) {
                            // 在红色等待状态，保持红色
                            printf("reset2.bco=48634\xff\xff\xff");
                        } else {
                            // 不在等待状态，设为灰色
                            printf("reset2.bco=50779\xff\xff\xff");
                        }
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_EXPORT_COEFF:
                        printf("coeff.bco=50779\xff\xff\xff");
                        break;
                    default:
                        break;
                }
                
                // 重置页面
                printf("page measure\xff\xff\xff");
                printf("s0.x=62\xff\xff\xff");  // 设置曲线从62位置开始
                page = SPECTRUM_MEASURE;
                cursor_spectrum = CURSOR_INT_TIME;  // 设置为默认的采集时间
                printf("a.bco=61277\xff\xff\xff");  // 设置进入页面按钮
                printf("a1.bco=61277\xff\xff\xff");     // 设置a1按钮
                printf("a7.bco=61277\xff\xff\xff");     // 设置a7按钮
                
                // 【修复】恢复自动缩放状态（使用保存的缩放参数）
                extern uint16_t saved_dis_value;
                extern uint32_t saved_y_axis_values[6];
                
                // 恢复dis参数
                printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
                
                // 恢复Y轴强度范围（使用保存的值）
                for(int i = 0; i < 6; i++) {
                    printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
                }
                
                // 【新增修复】重新发送存储的曲线数据到屏幕
                extern SpectrumGroupInfo spectrum_groups_info[12];
                extern uint8_t current_group;
                extern volatile uint8_t addt_in_progress;
                
                if(current_group >= 1 && current_group <= 12) {
                    uint8_t group_index = current_group - 1;
                    
                    if(spectrum_groups_info[group_index].is_valid && 
                       spectrum_groups_info[group_index].data_length >= 3640 && 
                       !addt_in_progress) {
                        
                        // 延迟确保页面加载完成
                        for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                            __NOP();
                        }
                        
                        extern void ProcessAndDisplayGroupData(uint8_t group_index);
                        ProcessAndDisplayGroupData(group_index);
                    }
                }
            }
            break;
            
        case OUTPUTING:
            // 取消发送按钮 - 返回主界面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
            
        case OUTPUT_COMPLETE:
            // 重置页面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
            
        case INT_TIME_SELECT:
            // 取消积分时间选择，返回measure页面
            printf("page measure\xff\xff\xff");
            printf("s0.x=62\xff\xff\xff");  // 设置曲线从62位置开始
            page = SPECTRUM_MEASURE;
            cursor_spectrum = CURSOR_INT_TIME;  // 设置为默认的采集时间
            printf("a.bco=61277\xff\xff\xff");  // 设置进入页面按钮
            
            // 【修复】恢复自动缩放状态（使用保存的缩放参数）
            extern uint16_t saved_dis_value;
            extern uint32_t saved_y_axis_values[6];
            
            // 恢复dis参数
            printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
            
            // 恢复Y轴强度范围（使用保存的值）
            for(int i = 0; i < 6; i++) {
                printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
            }
            
            // 【新增修复】重新发送存储的曲线数据到屏幕
            extern SpectrumGroupInfo spectrum_groups_info[12];
            extern uint8_t current_group;
            extern volatile uint8_t addt_in_progress;
            
            if(current_group >= 1 && current_group <= 12) {
                uint8_t group_index = current_group - 1;
                
                if(spectrum_groups_info[group_index].is_valid && 
                   spectrum_groups_info[group_index].data_length >= 3640 && 
                   !addt_in_progress) {
                    
                    // 延迟确保页面加载完成
                    for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                        __NOP();
                    }
                    
                    extern void ProcessAndDisplayGroupData(uint8_t group_index);
                    ProcessAndDisplayGroupData(group_index);
                }
            }
            
            // 【新增】更新p0位置（无论是否激活查看坐标功能）
            printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
            
            // 【新增】如果查看坐标功能已激活，根据p0位置更新t1显示
            if(view_coord_state.is_active) {
                update_coordinate_display();
            }
            
            // 如果之前是连续采集模式，需要恢复连续采集
            if(previous_collect_mode_before_int_time == COLLECT_MODE_CONTINUOUS) {
                // 设置调试信息
                printf("debug.txt=\"取消积分时间修改，恢复连续采集\"\xff\xff\xff");
                
                // 恢复连续采集界面状态
                printf("a.bco=50779\xff\xff\xff");      // 取消积分时间按钮高亮
                printf("photo2.bco=61277\xff\xff\xff");  // 设置连续采集按钮高亮
                cursor_spectrum = CURSOR_CONT_COLLECT;    // 设置光标到连续采集
                
                // 恢复连续采集模式
                current_collect_mode = COLLECT_MODE_CONTINUOUS;
                
                // 启动DMA接收
                extern uint8_t UART3_DataBuffer[DATA_BUFFER_SIZE];
                extern volatile uint8_t need_send_a2_flag;
                
                // 清空缓冲区
                memset(UART3_DataBuffer, 0, DATA_BUFFER_SIZE);
                
                // 启动DMA接收
                HAL_StatusTypeDef uart_status = HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                if(uart_status == HAL_OK) {
                    // 设置A2标志
                    need_send_a2_flag = 1;
                    printf("debug.txt=\"连续采集已恢复\"\xff\xff\xff");
                } else {
                    // 如果启动失败，回退到空闲模式
                    current_collect_mode = COLLECT_MODE_IDLE;
                    printf("a.bco=61277\xff\xff\xff");      // 恢复积分时间按钮高亮
                    printf("photo2.bco=50779\xff\xff\xff");  // 取消连续采集按钮高亮
                    cursor_spectrum = CURSOR_INT_TIME;        // 设置光标到积分时间
                    printf("debug.txt=\"连续采集恢复失败\"\xff\xff\xff");
                }
            }
            
            // 重置记录的采集模式状态
            previous_collect_mode_before_int_time = COLLECT_MODE_IDLE;
            break;
            
        case WAVELENGTH_SELECT:
            // 重置页面
            printf("page calibration\xff\xff\xff");
            page = CALIBRATION;
            break;
            
  
            
        default:
            break;
    }
}








// 自动应用校准参数（当有2个或更多标定点时）
void auto_apply_calibration(void) {
    if(calib_params.point_count >= 2) {
        // 计算平均值
        float sum_x = 0, sum_y = 0, sum_xy = 0, sum_x2 = 0;
        int n = calib_params.point_count;
        
        // 计算总和
        for(int i = 0; i < n; i++) {
            float x = calib_params.points[i].x;      // 位置
            float y = calib_params.points[i].lambda; // 值
            sum_x += x;
            sum_y += y;
            sum_xy += x * y;
            sum_x2 += x * x;
        }
        
        // 线性回归公式 y = kx + b
        float denominator = n * sum_x2 - sum_x * sum_x;
        if(denominator != 0) {
            calib_params.k = (n * sum_xy - sum_x * sum_y) / denominator;
            calib_params.b = (sum_y - calib_params.k * sum_x) / n;
            
            // 计算R^2
            float mean_y = sum_y / n;
            float ss_tot = 0, ss_res = 0;
            for(int i = 0; i < n; i++) {
                float y_pred = calib_params.k * calib_params.points[i].x + calib_params.b;
                ss_res += (calib_params.points[i].lambda - y_pred) * (calib_params.points[i].lambda - y_pred);
                ss_tot += (calib_params.points[i].lambda - mean_y) * (calib_params.points[i].lambda - mean_y);
            }
            calib_params.r_squared = (ss_tot != 0) ? (1 - ss_res / ss_tot) : 0;
            
            // 校准有效性
            calib_params.is_valid = 1;
            
            // 【关键修复】同时更新saved_calib_params（标定计算完成后立即生效）
            // 这样返回光谱测量界面时，横坐标就能显示为波长
            saved_calib_params.k = calib_params.k;
            saved_calib_params.b = calib_params.b;
            saved_calib_params.r_squared = calib_params.r_squared;
            saved_calib_params.is_valid = 1;
            saved_calib_params.point_count = calib_params.point_count;
            
            // 【关键修复】设置t8-t15的值
            // 【关键修改】标定计算完成后，横坐标显示取决于当前状态
            
            // 【新增修复】检查是否处于放大状态
            if(display_range.is_zoomed) {
                // 处于放大状态：保持当前放大区域的横坐标，根据显示模式决定显示内容
                for(int i = 0; i < 8; i++) {
                    int pixel_val = display_range.current_values[i]; // 使用当前放大区域的像素值
                    
                    if(wavelength_display_enabled) {
                        // 波长显示模式：实时更新为新的标定波长
                        float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                    } else {
                        // 像素位显示模式：保持像素值显示（不变）
                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, pixel_val);
                    }
                    // display_range.current_values[i] 不需要改变，保持放大区域的值
                }
            } else {
                // 未放大状态：使用默认的0-3500范围
                for(int i = 0; i < 8; i++) {
                    int pixel_val = DEFAULT_T_VALUES[i]; // 使用默认的像素坐标
                    
                    if(wavelength_display_enabled) {
                        // 波长显示模式：显示新的标定波长
                        float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
                        printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                    } else {
                        // 像素位显示模式：显示像素值
                        printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, pixel_val);
                    }
                    display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 存储像素值
                }
            }
            
            // 设置t7的值（R?）
            printf("t7.txt=\"%.4f\"\xff\xff\xff", calib_params.r_squared);
            
            // 【关键修改】z1/z2的可见性取决于wavelength_display_enabled
            if(wavelength_display_enabled) {
                // 波长显示模式
                printf("vis z1,0\xff\xff\xff");    // z1隐藏（像素位）
                printf("vis z2,1\xff\xff\xff");    // z2显示（波长）
            } else {
                // 像素位显示模式
                printf("vis z1,1\xff\xff\xff");    // z1显示（像素位）
                printf("vis z2,0\xff\xff\xff");    // z2隐藏（波长）
            }
        }
    }
}

// 重置波段数据
void reset_group_data(void) {
    // 重置波段数量
    current_group = 1;
    saved_groups = 0;
    
    // 重置group按钮的文本
    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
}

// 初始化calibration页面
void calibration_page_init(void) {
    // 初始化calibration页面
    calib_params.point_count = 0;
    calib_params.is_valid = 0;
    calib_params.state = CALIB_IDLE;
    calib_params.temp_peak_x = 0;
    calib_params.cursor_pos = 0;
    calib_params.is_selecting = 0;
    calib_params.select_start = 0;
    calib_params.select_end = 0;
    calib_params.current_wavelength_index = 0; // 从第一个波长开始
    calib_params.move_speed = 1; // 初始移动速度为1
    calib_params.selected_wavelength_button = 0; // 初始选择第一个波长按钮
    
    // 设置校准参数
    calib_params.k = 0;
    calib_params.b = 0;
    calib_params.r_squared = 0;
    
    // 每次进入校准页面都默认高亮"选择峰"按钮（t5）
    cursor_calibration1 = CURSOR_SELECT_PEAK;
    
    // 初始化所有按钮为未高亮状态
    printf("saving.bco=50779\xff\xff\xff");  // 设置为saving
    printf("input.bco=50779\xff\xff\xff");   // 设置input按钮
    printf("coeff.bco=50779\xff\xff\xff");   // 设置coeff按钮
    printf("t5.bco=50779\xff\xff\xff");
    printf("confirm.bco=50779\xff\xff\xff");
    
    // 根据当前光标位置高亮对应按钮
    switch(cursor_calibration1) {
        case CURSOR_SAVE_CALIB:
            printf("saving.bco=61277\xff\xff\xff");  // 设置为saving
            break;
        case CURSOR_INPUT_COEFF:
            printf("input.bco=61277\xff\xff\xff");   // 设置input按钮
            break;
        case CURSOR_EXPORT_COEFF_CALIB:
            printf("coeff.bco=61277\xff\xff\xff");   // 设置coeff按钮
            break;
        case CURSOR_SELECT_PEAK:
            printf("t5.bco=61277\xff\xff\xff");
            break;
        case CURSOR_CONFIRM_POINT:
            printf("confirm.bco=61277\xff\xff\xff");
            break;
        case CURSOR_SWITCH_CALIB:
            printf("switch.bco=61277\xff\xff\xff");
            break;
        default:
            // 默认的calibration按钮
            printf("saving.bco=61277\xff\xff\xff");
            cursor_calibration1 = CURSOR_SAVE_CALIB;
            break;
    }
    
    // 设置t8为固定的"0"（最底部刻度）
    printf("t8.txt=\"0\"\xff\xff\xff");
    
    // 【修复】恢复自动缩放状态（使用主界面保存的缩放参数）
    extern uint16_t saved_dis_value;
    extern uint32_t saved_y_axis_values[6];
    
    // 恢复dis参数
    printf("s0.dis=%d\xff\xff\xff", saved_dis_value);
    
    // 恢复Y轴强度范围（使用保存的值）
    for(int i = 0; i < 6; i++) {
        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
    }
    
    // 隐藏 t24-t29（标定点标记）
    for(int i = 24; i <= 29; i++) {
        printf("vis t%d,0\xff\xff\xff", i);
    }
    
    // 显示 t31-t36（波长选择按钮），并设置文本和取消高亮
    for(int i = 0; i < 6; i++) {
        int t_index = 31 + i;
        printf("vis t%d,1\xff\xff\xff", t_index); // 设置为可见
        printf("t%d.txt=\"%.3fnm\"\xff\xff\xff", t_index, CALIBRATION_WAVELENGTHS[i]); // 显示波长
        printf("t%d.bco=50779\xff\xff\xff", t_index); // 取消高亮
    }
    
    // 设置t8-t15的默认值
    extern SpectrumGroupInfo spectrum_groups_info[12];
    extern uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
    extern volatile uint8_t addt_in_progress;
    
    // 【修复】每次进入标定页面都发送波形数据
        // 标记addt正在进行，防止冲突
        addt_in_progress = 1;
        
        // 发送addt透传指令，将数据显示到s0波形控件
        printf("addt s0.id,0,729\xff\xff\xff");
        
        // 基于循环计数的延迟（等待屏幕响应）
        for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
            __NOP(); // 空操作，防止编译器优化
        }
        
        // 透传729个数据点（从3648字节的原始数据中等间隔采样）
        // 【修复】标定界面：正序发送数据（与ProcessZoomData保持一致）
        uint8_t* source_data = spectrum_data_ram[0];
        for(int i = 0; i < 729; i++) {
            // 等间隔采样：从3648个数据点中采样729个点，正序发送
            int src_index = i * 5; // 3648/729 ≈ 5
            if(src_index < DATA_BUFFER_SIZE) {
                putchar(source_data[src_index]);
            }
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
    
    // 【新增】设置t8-t15的默认值（根据wavelength_display_enabled标志）
    // 【修复】标定界面现在使用正序发送，所以current_values应该使用正序的像素值
    // 重置缩放状态
    display_range.zoom_level = 0;
    display_range.is_zoomed = 0;  // 【修复】重置放大状态标志
    view_coord_state.saved_full_curve_pixel = -1; // 清除保存的像素索引
    
    if(wavelength_display_enabled && saved_calib_params.is_valid) {
        // 波长显示模式：显示波长，存储像素值
        for(int i = 0; i < 8; i++) {
            int pixel_val = DEFAULT_T_VALUES[i]; // 【修复】使用正序的像素值（与初始化发送一致）
            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【关键】存储正序的像素值
        }
        
        // 显示z2（波长模式）
        printf("vis z1,0\xff\xff\xff");    // z1隐藏
        printf("vis z2,1\xff\xff\xff");    // z2显示
        
        // 显示R?值
        printf("t7.txt=\"%.4f\"\xff\xff\xff", saved_calib_params.r_squared);
    } else {
        // 像素位显示模式：显示像素值，存储像素值
        for(int i = 0; i < 8; i++) {
            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]); // 显示横坐标值
            display_range.current_values[i] = DEFAULT_T_VALUES[i]; // 【修复】存储正序的像素值（与初始化发送一致）
        }
        
        // 显示z1（像素模式）
        printf("vis z1,1\xff\xff\xff");    // z1显示
        printf("vis z2,0\xff\xff\xff");    // z2隐藏
    }
    
    // 【新增】如果查看坐标功能已激活，根据p0位置更新t1显示
    if(view_coord_state.is_active) {
        update_coordinate_display();
    }
    
    // 设置t0和t1的颜色
}



// 获取最近的标签索引
int get_nearest_label_index(float position) {
    // t8-t15对应的范围是62, 62+729/7*1, 62+729/7*2, ..., 791
    // 每个标签对应的索引
    float label_positions[8];
    for(int i = 0; i < 8; i++) {
        label_positions[i] = 62 + (791 - 62) * i / 7.0f;
    }
    
    // 找到最接近position的标签
    int nearest_index = 0;
    float min_distance = fabs(position - label_positions[0]);
    
    for(int i = 1; i < 8; i++) {
        float distance = fabs(position - label_positions[i]);
        if(distance < min_distance) {
            min_distance = distance;
            nearest_index = i;
        }
    }
    
    return nearest_index;
}

// 更新坐标标签
void update_coordinate_labels(void) {
    if(!display_range.is_zoomed) {
        return; // 没有放大，不需要更新
    }
    
    // 放大范围内的8个值
    float range = display_range.x_max - display_range.x_min;
    
    for(int i = 0; i < 8; i++) {
        int pixel_val = DEFAULT_T_VALUES[i]; // 使用默认的像素坐标
        
        if(wavelength_display_enabled && saved_calib_params.is_valid) {
            // 波长显示模式：显示波长，但存储像素值
            float wavelength = saved_calib_params.k * pixel_val + saved_calib_params.b;
            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
            display_range.current_values[i] = pixel_val; // 【关键】存储像素值（用于标定标签位置计算）
        } else {
            // 像素位显示模式：显示像素值，存储像素值
            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, pixel_val);
            display_range.current_values[i] = pixel_val; // 存储像素值
        }
    }
}

// 功能按钮
// 更新查看坐标t1控件的显示
void update_coordinate_display(void) {
    // p0位置范围：62-791（屏幕X坐标）
    // 计算当前p0对应的像素位
    int pixel_index;
    
    // 【关键修复】优先使用保存的完整曲线像素索引（如果有）
    if(view_coord_state.saved_full_curve_pixel >= 0) {
        // 直接使用保存的像素索引，避免整数除法累积误差
        pixel_index = view_coord_state.saved_full_curve_pixel;
    }
    // 【新增】判断是否处于放大查看状态
    else if(display_range.is_zoomed) {
        // 放大状态：p0的位置62-791对应放大后的范围[start_pixel, end_pixel]
        int start_pixel = display_range.current_values[0];
        int end_pixel = display_range.current_values[7];
        
        // 映射公式：pixel_index = start_pixel + (p0位置 - 62) * (范围大小) / (屏幕宽度)
        pixel_index = start_pixel + ((view_coord_state.p0_position - 62) * (end_pixel - start_pixel)) / (791 - 62);
    } else {
        // 未放大状态：p0的位置62-791对应完整的像素范围0-3648
        pixel_index = ((view_coord_state.p0_position - 62) * 3648) / (791 - 62);
    }
    
    // 限制像素位范围
    if(pixel_index < 0) pixel_index = 0;
    if(pixel_index > 3648) pixel_index = 3648;
    
    // 根据当前显示格式显示坐标
    if(wavelength_display_enabled && saved_calib_params.is_valid) {
        // 波长显示模式：使用校准参数将像素位转换为波长
        float wavelength = saved_calib_params.k * pixel_index + saved_calib_params.b;
        
        // 显示波长数值
        printf("t1.txt=\"%.2f\"\xff\xff\xff", wavelength);
        
        // 显示z2控件（波长）
        printf("vis z2,1\xff\xff\xff");
        printf("vis z1,0\xff\xff\xff");
    } else {
        // 像素位显示模式：只显示像素位数值
        printf("t1.txt=\"%d\"\xff\xff\xff", pixel_index);
        
        // 隐藏z2控件，显示z1（像素位）
        printf("vis z2,0\xff\xff\xff");
        printf("vis z1,1\xff\xff\xff");
    }
}

void fun_button(void) {
    switch(page) {
        case MAIN:
            // 设置功能按钮
            break;
            
        case SPECTRUM_MEASURE:
            // 光谱测量界面：查看坐标状态控制
            if(!view_coord_state.is_active) {
                // 进入查看坐标状态
                view_coord_state.is_active = 1;
                
                // p0_position保持当前值（初始为62，或上次退出时的位置）
                
                view_coord_state.move_speed = 1;    // 重置移动速度为1
                
                // 显示p0控件
                printf("vis p0,1\xff\xff\xff");
                printf("p0.x=%d\xff\xff\xff", view_coord_state.p0_position);
                
                // 显示t1控件并更新坐标信息
                printf("vis t1,1\xff\xff\xff");
                update_coordinate_display();
                
                // 更新t7文本为"开"
                printf("t7.txt=\"开\"\xff\xff\xff");
            } else {
                // 已经处于查看坐标状态，切换移动速度：1 -> 2 -> 4 -> 1
                if(view_coord_state.move_speed == 1) {
                    view_coord_state.move_speed = 2;
                } else if(view_coord_state.move_speed == 2) {
                    view_coord_state.move_speed = 4;
                } else {
                    view_coord_state.move_speed = 1;
                }
            }
            break;
            
        case CALIBRATION:
            // 设置calibration按钮
            // 在calibration模式下，设置移动速度
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 循环移动速度：1 -> 2 -> 4 -> 1
                if(calib_params.move_speed == 1) {
                    calib_params.move_speed = 2;
                } else if(calib_params.move_speed == 2) {
                    calib_params.move_speed = 4;
                } else {
                    calib_params.move_speed = 1;
                }
            }
            break;
            
        case QUERY_EXPORT:
            // 设置查询导出按钮
            break;
            
        case OUTPUT_COMPLETE:
            // 显示当前页面
            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = CALIBO;  // 默认选择进入页面
            printf("calibo.bco=61277\xff\xff\xff");  // 设置进入页面
            break;
            
        default:
            break;
    }
}

// UART3发送命令
void UART3_Send_Command(uint8_t cmd)
{
    // 使用HAL_UART_Transmit函数发送命令
    HAL_StatusTypeDef status = HAL_UART_Transmit(&huart3, &cmd, 1, 100);
    if (status != HAL_OK) {
        // 如果发送失败，重置UART3
        MX_USART3_UART_Init();
        // 重新发送命令
        HAL_UART_Transmit(&huart3, &cmd, 1, 100);
    }
}

// 自动缩放 - 使用dis参数进行计算
void auto_scale_spectrum(void) {
    extern uint8_t ProcessedDataBuffer[]; // 处理后的数据缓冲区
    uint8_t max_intensity = 0;
    
    // 遍历729个数据点，找到最大强度
    for(uint16_t i = 0; i < 729; i++) {
        if(ProcessedDataBuffer[i] > max_intensity) {
            max_intensity = ProcessedDataBuffer[i];
        }
    }
    
    // 防止除零错误和过小的值
    if(max_intensity < 10) {
        max_intensity = 10;
    }
    
    // ========== 核心算法说明 ==========
    // dis参数工作原理：
    //   1. 曲线控件接收的数据范围：0x00-0xFF (0-255)
    //   2. dis是缩放百分比参数，范围10-1000
    //   3. 缩放公式：显示值 = 原始数据值 × (dis / 100)
    //   4. Y轴坐标映射：纵坐标 = 显示值 × (60000 / 255)
    //
    // 自动缩放目标：
    //   - 让最大数据值显示在约90%的高度（0xFF的90% ≈ 230）
    //   - 这样可以留出10%的上方空间，避免曲线顶格
    //
    // 计算方法：
    //   dis = (目标显示值 / 原始最大值) × 100
    //   dis = (230 / max_intensity) × 100
    //   dis = 23000 / max_intensity
    //
    // 验证：
    //   示例1：max=69  → dis=23000/69≈333  (接近你测试的350)
    //   示例2：max=139 → dis=23000/139≈165 (接近你测试的170)
    // ==================================
    
    // 计算dis值（让峰值显示在90%高度，留10%上方空间）
    uint16_t dis_value = 23000 / max_intensity;
    
    // 限制dis值在合理范围内
    if(dis_value < 10) dis_value = 10;       // 最小值保护
    if(dis_value > 1000) dis_value = 1000;   // 最大值保护（dis范围10-1000）
    
    // 计算缩放后的最大数据值（用于计算Y轴刻度）
    // scaled_max = max_intensity × (dis / 100)，但不能超过255
    uint16_t scaled_max = ((uint32_t)max_intensity * dis_value) / 100;
    if(scaled_max > 255) {
        scaled_max = 255;
        // 如果超过255，需要重新调整dis值
        dis_value = 25500 / max_intensity;  // 25500 = 255 × 100
        if(dis_value < 10) dis_value = 10;
    }
    
    // ========== Y轴刻度计算说明 ==========
    // 【关键修复】Y轴刻度应该显示原始强度值，而不是缩放后的显示值
    // 
    // 数据流说明：
    //   1. 原始ADC数据：0-255 (uint8_t)
    //   2. dis缩放：用于在屏幕上放大/缩小曲线显示
    //   3. Y轴物理坐标：0-60000
    //   4. 坐标映射公式：Y坐标 = 数据值 × (60000 / 255)
    //
    // Y轴刻度含义：
    //   - Y轴刻度显示的是"原始强度值映射到0-60000范围的值"
    //   - 例如：ADC原始值50 → Y轴刻度 = 50 × (60000/255) ≈ 11765
    //   - dis参数只影响曲线在屏幕上的显示位置，不影响Y轴刻度值
    //
    // 正确的Y轴最大值计算：
    //   y_max = max_intensity × (60000 / 255)
    //   这样可以准确反映原始数据的实际强度范围
    // =====================================
    
    // 计算Y轴最大刻度值（基于原始强度值，而不是缩放后的值）
    uint32_t y_max = ((uint32_t)max_intensity * 60000) / 255;
    
    // 为了显示效果更好，留出10%的上方空间
    // 由于dis已经让峰值显示在90%高度，Y轴刻度也相应调整
    y_max = (y_max * 255) / 230;  // 调整系数：255/230 ≈ 1.11
    
    // 限制Y轴最大值在合理范围
    if(y_max > 60000) y_max = 60000;
    if(y_max < 1000) y_max = 1000;  // 降低最小值限制，允许显示小强度数据
    
    // 保存自动缩放参数（用于页面切换时恢复状态）
    extern uint16_t saved_dis_value;
    extern uint32_t saved_y_axis_values[6];
    
    saved_dis_value = dis_value;
    for(int i = 0; i < 6; i++) {
        saved_y_axis_values[i] = (y_max * (i + 1)) / 6;
    }
    
    // 发送dis参数到屏幕
    printf("s0.dis=%d\xff\xff\xff", dis_value);
    
    // 【修复】不修改t8文本内容，保持横坐标不变
    // t8的值应该由当前的显示模式（标定/未标定，放大/完整）决定
    
    // 设置Y轴6个刻度值（t17-t22，从y_max/6到y_max均匀分布）
    // i=0对应t17（第1个刻度），i=5对应t22（第6个刻度，即最大值）
    for(int i = 0; i < 6; i++) {
        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, saved_y_axis_values[i]);
    }
}

// 检查重置按钮超时（在定时器中断中调用，每10ms检查一次）
void check_reset_button_timeout(void) {
	// 如果按钮已按下，检查是否超时
	if(reset_button_pressed) {
		uint32_t current_time = HAL_GetTick();
		// 如果超过1秒，自动恢复按钮颜色和文本并重置状态
		if(current_time - reset_button_press_time >= LONG_PRESS_DURATION) {
			reset_button_pressed = 0;
			reset_button_press_time = 0;
			// 恢复按钮颜色和文本
			printf("reset2.bco=61277\xff\xff\xff");
			printf("reset2.txt=\"重置缩放\"\xff\xff\xff");
		}
	}
}


