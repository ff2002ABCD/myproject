#include "menu.h"
#include "function.h"
#include "usart.h"   // 添加usart.h以使用UART相关函数
#include "ch376.h"   // 添加ch376.h以使用CH376相关函数
#include <stdio.h>
#include <stdlib.h>  // 添加stdlib.h以使用rand()函数
#include "delay.h"   // 添加delay.h以使用delay_ms()函数
#include "key.h"     // 添加key.h以使用按键相关定�?extern int fputc(int ch, FILE* file);

// 函数声明
void UART3_Send_Command(uint8_t cmd);

// 添加外部声明
extern KEY_TYPE g_KeyActionFlag;

PAGE page = MAIN;
CURSOR_MAIN cursor_main = CALIBO;  // 初始化为CALIBO
CURSOR_SPECTRUM cursor_spectrum;
CURSOR_CALIBRATION1 cursor_calibration1;
CALIB_STATE calib_state;
DisplayRange display_range;
SpectrumData spectrum_data;
IntegrationTime current_int_time = INT_TIME_1MS;
uint8_t cursor_int_time = 1; // 默认选中1ms (a1)
uint8_t cursor_wavelength = 0; // 默认选中第一个波�?uint8_t current_group = 1; // 当前组别数，初始�?
uint8_t saved_groups = 0; // 已保存的组数，初始为0

// 添加缺失的标定参数结构体实例
CalibrationParams calib_params;
CalibrationParams saved_calib_params = {0}; // 保存的标定参�?
CALIBO_STATE calibo_state=NONE;
_Bool output_flag;//1成功 0失败

unsigned int cursor_sheet_num;

// 默认的t8-t15数值（减少重复定义�?const int DEFAULT_T_VALUES[8] = {0, 500, 1000, 1500, 2000, 2500, 3000, 3500};

// 积分时间值（单位：微秒）
const uint32_t INTEGRATION_TIMES[INT_TIME_COUNT] = {
    10,     // 10μs
    20,     // 20μs
    50,     // 50μs
    100,    // 100μs
    200,    // 200μs
    500,    // 500μs
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

// 积分时间显示文本
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

// 积分时间对应的UART3指令�?const uint8_t INT_TIME_COMMANDS[INT_TIME_COUNT] = {
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

// 标定波长值（单位：nm�?const float CALIBRATION_WAVELENGTHS[WAVELENGTH_COUNT] = {
    365.016,  // 365.016nm
    404.656,  // 404.656nm
    435.833,  // 435.833nm
    546.075,  // 546.075nm
    576.961,  // 576.961nm
    579.067   // 579.067nm
};

// 初始化显示范�?void spectrum_page_init(void) {
    display_range.x_min = DEFAULT_X_MIN;
    display_range.x_max = DEFAULT_X_MAX;
    display_range.y_min = DEFAULT_Y_MIN;
    display_range.y_max = DEFAULT_Y_MAX;
    display_range.is_zoomed = 0;
    display_range.is_selecting = 0;
    display_range.cursor_pos = DEFAULT_X_MIN;
    display_range.first_selected = -1;
    display_range.second_selected = -1;
    display_range.zoom_level = 0; // 初始化放大级�?    
    // 初始化current_values为默认值（t8-t15对应0-3500�?    for(int i = 0; i < 8; i++) {
        display_range.current_values[i] = DEFAULT_T_VALUES[i];
    }
    
    cursor_spectrum = CURSOR_INT_TIME;
    current_int_time = INT_TIME_1MS;
    current_group = 1; // 初始化组别数�?
    saved_groups = 0; // 初始化已保存组数�?
    
    // 初始化group按钮文本和高�?    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
    printf("group.bco=61277\xff\xff\xff");  // 高亮组别按钮
    printf("a1.bco=61277\xff\xff\xff");     // 高亮a1控件   
    printf("a7.bco=61277\xff\xff\xff");     // 高亮a7控件
    
    // 初始化横坐标标签：z1（像素位）可见，z2（波长）不可�?    printf("vis z1,1\xff\xff\xff");    // z1可见
    printf("vis z2,0\xff\xff\xff");    // z2不可�?}


void up_button(void) {
    switch(page) {
        default:break;
  	case MAIN://main �?			switch(cursor_main)
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
            switch(cursor_spectrum)
            {
                case CURSOR_CALIBRATION: // calibration
                    // 上一项：放大查看
                    printf("paging.bco=50779\xff\xff\xff"); // 取消高亮
                    printf("a.bco=61277\xff\xff\xff");   // 高亮放大查看
                    cursor_spectrum = CURSOR_INT_TIME;
                    break;
                case CURSOR_ZOOM: // 放大查看
                    // 上一项：单次采集
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("photo1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SINGLE_COLLECT;
                    break;
                case CURSOR_AUTO_SCALE: // 自动缩放
                    // 上一项：连续采集
                    printf("reset1.bco=50779\xff\xff\xff");
                    printf("photo2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    break;
                case CURSOR_RESET_ZOOM: // 重置缩放
                    // 上一项：暂停采集
                    printf("reset2.bco=50779\xff\xff\xff");
                    printf("pause.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_PAUSE_COLLECT;
                    break;

                case CURSOR_INT_TIME:
                    printf("paging.bco=61277\xff\xff\xff"); // 取消高亮
                    printf("a.bco=50779\xff\xff\xff");   // 高亮放大查看
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
                    printf("reset2.bco=61277\xff\xff\xff");
                    printf("pause.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    break;
                    default:break;
            }
    break;
    
        case INT_TIME_SELECT:
            // 积分时间选择界面上按钮处�?            printf("a%d.bco=50779\xff\xff\xff", cursor_int_time + 1);
            if(cursor_int_time > 0) {
                cursor_int_time--;
            } else {
                cursor_int_time = INT_TIME_COUNT - 1; // 循环到最后一�?            }
            printf("a%d.bco=61277\xff\xff\xff", cursor_int_time + 1);
            break;
            
     case QUERY_EXPORT://选择查看�?�?            // 组别选择功能已删�?    break;

	case OUTPUTING:
			
	break;

    case OUTPUT_COMPLETE:
			
	break;

    case CALIBRATION:

    break;
    
    case WAVELENGTH_SELECT:
        // 波长选择界面上按钮处�?        printf("t%d.bco=50779\xff\xff\xff", cursor_wavelength); // 取消当前波长选项的高�?        if(cursor_wavelength > 0) {
            cursor_wavelength--; // 向上移动到前一个波长选项
        } else {
            cursor_wavelength = WAVELENGTH_COUNT - 1; // 循环到最后一个波长选项
        }
        printf("t%d.bco=61277\xff\xff\xff", cursor_wavelength); // 高亮新选择的波长选项
        break;
    }
}

// 下按键处�?void down_button(void) {
    switch(page) {
        default:break;
       	case MAIN://main �?			switch(cursor_main)
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
            switch(cursor_spectrum)
            {
                case CURSOR_CALIBRATION: // calibration
                    // 上一项：放大查看
                    printf("paging.bco=50779\xff\xff\xff"); // 取消高亮
                    printf("a.bco=61277\xff\xff\xff");   // 高亮放大查看
                    cursor_spectrum = CURSOR_INT_TIME;
                    break;
                case CURSOR_ZOOM: // 放大查看
                    // 上一项：单次采集
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("photo1.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SINGLE_COLLECT;
                    break;
                case CURSOR_AUTO_SCALE: // 自动缩放
                    // 上一项：连续采集
                    printf("reset1.bco=50779\xff\xff\xff");
                    printf("photo2.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    break;
                case CURSOR_RESET_ZOOM: // 重置缩放
                    // 上一项：暂停采集
                    printf("reset2.bco=50779\xff\xff\xff");
                    printf("pause.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_PAUSE_COLLECT;
                    break;

                case CURSOR_INT_TIME:
                    printf("paging.bco=61277\xff\xff\xff"); // 取消高亮
                    printf("a.bco=50779\xff\xff\xff");   // 高亮放大查看
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
                    printf("reset2.bco=61277\xff\xff\xff");
                    printf("pause.bco=50779\xff\xff\xff");
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    break;
                    default:break;
            }
            break;
            
        case INT_TIME_SELECT:
            // 积分时间选择界面下按钮处�?            printf("a%d.bco=50779\xff\xff\xff", cursor_int_time + 1);
            if(cursor_int_time < INT_TIME_COUNT - 1) {
                cursor_int_time++;
            } else {
                cursor_int_time = 0; // 循环到第一�?            }
            printf("a%d.bco=61277\xff\xff\xff", cursor_int_time + 1);
            break;
            
     case QUERY_EXPORT://选择查看�?�?            // 组别选择功能已删�?    break;

	case OUTPUTING:
			
	break;

    case OUTPUT_COMPLETE:
			
	break;

    case CALIBRATION:

    break;
    
    case WAVELENGTH_SELECT:
        // 波长选择界面下按钮处�?        printf("t%d.bco=50779\xff\xff\xff", cursor_wavelength); // 取消当前波长选项的高�?        if(cursor_wavelength < WAVELENGTH_COUNT - 1) {
            cursor_wavelength++; // 向下移动到下一个波长选项
        } else {
            cursor_wavelength = 0; // 循环到第一个波长选项
        }
        printf("t%d.bco=61277\xff\xff\xff", cursor_wavelength); // 高亮新选择的波长选项
        break;
    }
}
// 左按键处�?void left_button(void) {
    static uint8_t long_press_counter = 0;
    
    switch(page) {
        case MAIN:
            // main的左按键处理，不做操�?        break;

        case SPECTRUM_MEASURE:
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
                    // 如果在选择模式下，处理t8-t16标签之间的切�?                    if(display_range.is_selecting) {
                        // 当前选中的是t8（索�?），已经是最左边，不做处�?                        if(display_range.cursor_pos > 0) {
                            // 取消当前标签高亮
                            printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                            
                            // 向左移动一个标�?                            display_range.cursor_pos--;
                            
                            // 高亮新选中的标�?                            printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                        }
                    } else {
                        // 不在选择模式下，正常处理按钮切换
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
                    printf("reset2.bco=50779\xff\xff\xff");
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
            
            // 如果在峰选择模式下，调整p0的x值，不管当前光标位置
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 根据长按时间增加移动速度
                int step = 1; // 默认步长�?
                
                // 检测是否为长按（通过g_KeyActionFlag判断�?                if(g_KeyActionFlag == LONG_KEY) {
                    long_press_counter++;
                    
                    // 根据长按时间增加步长
                    if(long_press_counter > 10) {
                        step = 10; // 长按超过10次，步长�?0
                    } else if(long_press_counter > 5) {
                        step = 5; // 长按超过5次，步长�?
                    } else if(long_press_counter > 2) {
                        step = 2; // 长按超过2次，步长�?
                    }
                } else {
                    // 短按重置计数�?                    long_press_counter = 0;
                }
                
                // 减小p0.x值，最小为73
                if(calib_params.temp_peak_x > 73 + step - 1) {
                    calib_params.temp_peak_x -= step;
                } else {
                    calib_params.temp_peak_x = 73; // 确保不小�?3
                }
                
                // 更新显示
                printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                
                return; // 直接返回，不执行后续的按钮切换逻辑
            } else {
                // 不在峰选择模式下，重置计数�?                long_press_counter = 0;
            }
            
            // 正常的按钮切换逻辑
            switch(cursor_calibration1)
            {
                case CURSOR_IMPORT_CALIB:
                    printf("load.bco=50779\xff\xff\xff");
                    printf("confirm.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_CONFIRM_POINT;
                    break;
                case CURSOR_SAVE_CALIB:
                    printf("saving.bco=50779\xff\xff\xff");
                    printf("load.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_IMPORT_CALIB;
                    break;
                case CURSOR_SELECT_PEAK:
                    printf("t5.bco=50779\xff\xff\xff");
                    printf("saving.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SAVE_CALIB;
                    break;
                case CURSOR_SELECT_WAVE:
                    printf("b.bco=50779\xff\xff\xff");
                    printf("t5.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SELECT_PEAK;
                    break;
                case CURSOR_CONFIRM_POINT:
                    printf("confirm.bco=50779\xff\xff\xff");
                    printf("b.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_SELECT_WAVE;
                    break;
                case CURSOR_ZOOM_CALIB:
                    printf("zoom.bco=50779\xff\xff\xff");
                    printf("confirm.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_CONFIRM_POINT;
                    break;
                case CURSOR_RESET_CALIB:
                    printf("reset2.bco=50779\xff\xff\xff");
                    printf("zoom.bco=61277\xff\xff\xff");
                    cursor_calibration1 = CURSOR_ZOOM_CALIB;
                    break;
                default:break;
            }
        break;
  
        case QUERY_EXPORT:
            // 左按键：在功能按钮间反向切换
            if(cursor_spectrum == CURSOR_CALIBRATION || cursor_spectrum == CURSOR_ZOOM || 
               cursor_spectrum == CURSOR_AUTO_SCALE || cursor_spectrum == CURSOR_RESET_ZOOM || 
               cursor_spectrum == CURSOR_EXPORT_USB) {
                // 当前在功能按钮上，在功能按钮间反向切�?                switch(cursor_spectrum)
                {   
                    case CURSOR_CALIBRATION:
                        // 从calibration往左到export_usb
                        printf("paging.bco=50779\xff\xff\xff");
                        printf("output.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_USB;
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
                        printf("reset2.bco=50779\xff\xff\xff");
                        printf("reset1.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_AUTO_SCALE;
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        printf("reset2.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_RESET_ZOOM;
                        break;
                    default:
                        break;
                }
            }
        break;
        
        case OUTPUTING:
            // 导出中界面的左按键处理，不做操作
        break;

        case OUTPUT_COMPLETE:
            // 导出完成界面的左按键处理，不做操�?        break;
    }
}
// 右按键处�?void right_button(void) {
    static uint8_t long_press_counter = 0;
    
     switch(page) {
        default:break;
        case MAIN:
            // main的右按键处理
        break;

        case SPECTRUM_MEASURE:
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
                  // 如果在选择模式下，处理t8-t15标签之间的切�?                  if(display_range.is_selecting) {
                      // 检查是否已经是最右边的标�?t15对应索引7)
                      if(display_range.cursor_pos < 7) {
                          // 取消当前标签高亮
                          printf("t%d.bco=50779\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                          
                          // 向右移动一个标�?                          display_range.cursor_pos++;
                          
                          // 高亮新选中的标�?                          printf("t%d.bco=61277\xff\xff\xff", (int)(display_range.cursor_pos) + 8);
                      }
                  } else {
                      // 不在选择模式下，正常处理按钮切换
                      printf("zoom.bco=50779\xff\xff\xff");
                      printf("reset1.bco=61277\xff\xff\xff");
                      cursor_spectrum = CURSOR_AUTO_SCALE;
                  }
                  break;
                case CURSOR_AUTO_SCALE:
                  printf("reset1.bco=50779\xff\xff\xff");
                  printf("reset2.bco=61277\xff\xff\xff");
                  cursor_spectrum = CURSOR_RESET_ZOOM;
                  break;
                case CURSOR_RESET_ZOOM:
                  printf("reset2.bco=50779\xff\xff\xff");
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
            
            // 如果在峰选择模式下，调整p0的x值，不管当前光标位置
            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 根据长按时间增加移动速度
                int step = 1; // 默认步长�?
                
                // 检测是否为长按（通过g_KeyActionFlag判断�?                if(g_KeyActionFlag == LONG_KEY) {
                    long_press_counter++;
                    
                    // 根据长按时间增加步长
                    if(long_press_counter > 10) {
                        step = 10; // 长按超过10次，步长�?0
                    } else if(long_press_counter > 5) {
                        step = 5; // 长按超过5次，步长�?
                    } else if(long_press_counter > 2) {
                        step = 2; // 长按超过2次，步长�?
                    }
                } else {
                    // 短按重置计数�?                    long_press_counter = 0;
                }
                
                // 增加p0.x值，最大为793
                if(calib_params.temp_peak_x < 793 - step + 1) {
                    calib_params.temp_peak_x += step;
                } else {
                    calib_params.temp_peak_x = 793; // 确保不超�?93
                }
                
                // 更新显示
                printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                
                return; // 直接返回，不执行后续的按钮切换逻辑
            } else {
                // 不在峰选择模式下，重置计数�?                long_press_counter = 0;
            }
            
            // 正常的按钮切换逻辑
           switch(cursor_calibration1)
         {
           case CURSOR_IMPORT_CALIB:
              printf("load.bco=50779\xff\xff\xff");
              printf("saving.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_SAVE_CALIB;
              break;
           case CURSOR_SAVE_CALIB:
              printf("saving.bco=50779\xff\xff\xff");
                    printf("t5.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_SELECT_PEAK;
              break;
           case CURSOR_SELECT_PEAK:
                    // 正常的按钮切�?                    printf("t5.bco=50779\xff\xff\xff");
                    printf("b.bco=61277\xff\xff\xff");
                    cursor_calibration1 =  CURSOR_SELECT_WAVE;
                    break;
                case CURSOR_SELECT_WAVE:
              printf("b.bco=50779\xff\xff\xff");
              printf("confirm.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_CONFIRM_POINT;
              break;
           case CURSOR_CONFIRM_POINT:
              printf("confirm.bco=50779\xff\xff\xff");
              printf("zoom.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_ZOOM_CALIB;
              break;
           case CURSOR_ZOOM_CALIB:
              printf("zoom.bco=50779\xff\xff\xff");
              printf("reset2.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_RESET_CALIB;
              break;
           case CURSOR_RESET_CALIB:
              printf("reset2.bco=50779\xff\xff\xff");
              printf("load.bco=61277\xff\xff\xff");
              cursor_calibration1 =  CURSOR_IMPORT_CALIB;
              break;
              default:break;
         }
        break;
  
        case QUERY_EXPORT:
            // 右按键：直接操作功能按钮
            // 组别选择功能已删除，直接处理功能按钮逻辑
            if(cursor_spectrum == CURSOR_CALIBRATION || cursor_spectrum == CURSOR_ZOOM || 
                     cursor_spectrum == CURSOR_AUTO_SCALE || cursor_spectrum == CURSOR_RESET_ZOOM || 
                     cursor_spectrum == CURSOR_EXPORT_USB) {
                // 当前在功能按钮上，在功能按钮间切�?                switch(cursor_spectrum)
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
                        printf("reset2.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_RESET_ZOOM;
                        break;
                    case CURSOR_RESET_ZOOM:
                        printf("reset2.bco=50779\xff\xff\xff");
                        printf("output.bco=61277\xff\xff\xff");
                        cursor_spectrum = CURSOR_EXPORT_USB;
                        break;
                    case CURSOR_EXPORT_USB:
                        // 从导出按钮往右到第一�?                        printf("output.bco=50779\xff\xff\xff");
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
			
	     break;
    }
}


// 确认按键处理
void confirm_button(void) {
    switch(page) {
        case MAIN:
           switch(cursor_main)
			{
			        	case CALIBO:
                    // 取消主界面按钮高�?                    printf("calibo.bco=50779\xff\xff\xff");
                    
                    printf("page measure\xff\xff\xff");
                    page = SPECTRUM_MEASURE;
                    // 初始化measure页面光标和高�?                    cursor_spectrum = CURSOR_INT_TIME;
                    printf("a.bco=61277\xff\xff\xff");  // 高亮积分时间按钮
 
                    
                    // 初始化横坐标标签：z1（像素位）可见，z2（波长）不可�?                    printf("vis z1,1\xff\xff\xff");    // z1可见
                    printf("vis z2,0\xff\xff\xff");    // z2不可�?                    break;
                    
                case DATA:
                    // 取消主界面按钮高�?                    printf("data.bco=50779\xff\xff\xff");
                    
                    printf("page query\xff\xff\xff");
                    page = QUERY_EXPORT;
                    
                    // 默认选中标定按钮
                    cursor_spectrum = CURSOR_CALIBRATION;
                    printf("paging.bco=61277\xff\xff\xff");  // 高亮标定按钮
                    break;
                    
                default:
                    break;
            }
            break;
            
        case SPECTRUM_MEASURE:
            switch(cursor_spectrum) {
                case CURSOR_INT_TIME:
                    // 切换到积分时间选择界面
                    printf("page timer1\xff\xff\xff");
                    page = INT_TIME_SELECT;
                    printf("a1.bco=61277\xff\xff\xff");
                    cursor_int_time = 0; // 设置为最小积分时间选项
                    break;
                    
                case CURSOR_CALIBRATION:
                    // 切换到标定界�?                    printf("page calibration\xff\xff\xff");
                    page = CALIBRATION;
                    
                    // 初始化标定界�?                    calibration_page_init();
                    break;
                    
                case CURSOR_SINGLE_COLLECT:
                {
                   // 设置按钮状�?                   printf("photo1.bco=61277\xff\xff\xff"); // 保持单次采集按钮高亮
                   cursor_spectrum = CURSOR_SINGLE_COLLECT;
                   
                   // 恢复t8-t15的默认文本�?                   printf("t8.txt=\"0\"\xff\xff\xff");
                   printf("t9.txt=\"500\"\xff\xff\xff");
                   printf("t10.txt=\"1000\"\xff\xff\xff");
                   printf("t11.txt=\"1500\"\xff\xff\xff");
                   printf("t12.txt=\"2000\"\xff\xff\xff");
                   printf("t13.txt=\"2500\"\xff\xff\xff");
                   printf("t14.txt=\"3000\"\xff\xff\xff");
                   printf("t15.txt=\"3500\"\xff\xff\xff");
                   
                   // 恢复所有标签的正常颜色（t8-t15�?                   for(int i = 8; i <= 15; i++) {
                       printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                       printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景�?                   }
                   
                   // 重置放大相关状�?                   display_range.is_selecting = 0;
                   display_range.first_selected = -1;
                   display_range.second_selected = -1;
                   display_range.zoom_level = 0; // 重置放大级别
                   
                   // 重置current_values为默认值（t8-t15对应0-3500�?                   for(int i = 0; i < 8; i++) {
                       display_range.current_values[i] = DEFAULT_T_VALUES[i];
                   }
                   
                   // 设置单次采集模式
                   current_collect_mode = COLLECT_MODE_SINGLE;
                   
                   // 启动DMA接收（如果未启动�?                   if(HAL_UART_GetState(&huart3) == HAL_UART_STATE_READY) {
                       HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                   }
                   
                   // 设置标志位，让主循环发送A2指令
                   extern volatile uint8_t need_send_a2_flag;
                   need_send_a2_flag = 1;
                   break;
                }
                    
                case CURSOR_CONT_COLLECT:
                {
                    // 设置按钮状�?                    printf("photo2.bco=61277\xff\xff\xff"); // 保持连续采集按钮高亮
                    cursor_spectrum = CURSOR_CONT_COLLECT;
                    
                    // 恢复t8-t15的默认文本�?                    printf("t8.txt=\"0\"\xff\xff\xff");
                    printf("t9.txt=\"500\"\xff\xff\xff");
                    printf("t10.txt=\"1000\"\xff\xff\xff");
                    printf("t11.txt=\"1500\"\xff\xff\xff");
                    printf("t12.txt=\"2000\"\xff\xff\xff");
                    printf("t13.txt=\"2500\"\xff\xff\xff");
                    printf("t14.txt=\"3000\"\xff\xff\xff");
                    printf("t15.txt=\"3500\"\xff\xff\xff");
                    
                    // 恢复所有标签的正常颜色（t8-t15�?                    for(int i = 8; i <= 15; i++) {
                        printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                        printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景�?                    }
                    
                    // 重置放大相关状�?                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    display_range.zoom_level = 0; // 重置放大级别
                    
                    // 重置current_values为默认值（t8-t15对应0-3500�?                    for(int i = 0; i < 8; i++) {
                        display_range.current_values[i] = DEFAULT_T_VALUES[i];
                    }
                    
                    // 重置缩放时，根据是否有标定参数决定显示哪个横坐标标签
                    if(saved_calib_params.is_valid) {
                        // 有标定参数时显示波长
                        printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                        printf("z2.vis=1\xff\xff\xff");    // z2可见
                        
                        // 更新t8-t15为波长�?                        for(int i = 0; i < 8; i++) {
                            float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                            float wavelength = saved_calib_params.k * x_pixel + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            display_range.current_values[i] = (int)wavelength;
                        }
                    } else {
                        // 无标定参数时显示像素�?                        printf("z1.vis=1\xff\xff\xff");    // z1可见
                        printf("z2.vis=0\xff\xff\xff");    // z2不可�?                        
                        // 更新t8-t15为像素�?                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                        }
                    }
                    
                    // 设置连续采集模式
                    current_collect_mode = COLLECT_MODE_CONTINUOUS;
                    
                    // 启动DMA接收（如果未启动�?                    if(HAL_UART_GetState(&huart3) == HAL_UART_STATE_READY) {
                        HAL_UART_Receive_DMA(&huart3, UART3_DataBuffer, DATA_BUFFER_SIZE);
                    }
                    
                    // 设置标志位，让主循环发送A2指令
                    extern volatile uint8_t need_send_a2_flag;
                    need_send_a2_flag = 1;
                    break;
                }
                    
                case CURSOR_PAUSE_COLLECT:
                    // 处理暂停采集
                    // 设置空闲模式并中止DMA接收
                    current_collect_mode = COLLECT_MODE_IDLE;
                    HAL_UART_AbortReceive(&huart3);
                    
                    // 清除A2指令发送标志，停止连续发�?                    extern volatile uint8_t need_send_a2_flag;
                    need_send_a2_flag = 0;
                    break;
                
                case CURSOR_SAVE_SPECTRUM:
                    // 处理保存光谱
                    // 调用保存函数
                    //save_spectrum_to_flash(); // 删除此行
                    
                    // 增加已保存的组数，最大为12
                    if(saved_groups < 12) {
                        saved_groups++;
                    }
                    
                    // 增加组别数，最大为12
                    if(current_group < 12) {
                        current_group++;
                    } else {
                        current_group = 1; // 如果达到最大值，则循环回�?
                    }
                    
                    // 只更新光谱测量界面的group按钮文本�?                    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
                    
                    // 如果有保存的标定参数，同时更新t8-t15横坐�?                    if(saved_calib_params.is_valid) {
                        for(int i = 0; i < 8; i++) {
                            float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                            float wavelength = saved_calib_params.k * x_pixel + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            
                            // 更新display_range.current_values为波长�?                            display_range.current_values[i] = (int)wavelength;
                        }
                        
                        // 有标定参数时切换横坐标标签：z2（波长）可见，z1（像素位）不可见
                        printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                        printf("z2.vis=1\xff\xff\xff");    // z2可见
                    }
                    
                    // 保持按钮高亮
                    printf("data_record.bco=61277\xff\xff\xff");
                    cursor_spectrum = CURSOR_SAVE_SPECTRUM;
                    break;
                    
                case CURSOR_ZOOM:
                    // 处理放大查看
                    cursor_spectrum = CURSOR_ZOOM;
                    
                    // 如果已经在选择模式�?                    if(display_range.is_selecting) {
                        // 当前光标位置
                        int current_pos = (int)display_range.cursor_pos;
                        
                        // 如果第一个点还未选中
                        if(display_range.first_selected == -1) {
                            // 选中第一个点
                            display_range.first_selected = current_pos;
                            // 高亮显示选中的标�?                            printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文本
                        }
                        // 如果第一个点已选中，但第二个点未选中
                        else if(display_range.second_selected == -1) {
                            // 如果选择了不同的�?                            if(current_pos != display_range.first_selected) { 
                                // 选中第二个点
                                display_range.second_selected = current_pos;
                                // 高亮显示选中的标�?                                printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文本
                                
                                // 获取选中点的索引和�?                                int first_idx = display_range.first_selected;
                                int second_idx = display_range.second_selected;
                                
                                // 根据当前放大级别选择数值来�?                                const int *values_source;
                                
                                if(display_range.zoom_level == 0) {
                                    // 第一次放大，使用默认�?                                    values_source = DEFAULT_T_VALUES;
                                } else {
                                    // 第二次放大，使用当前显示的�?                                    values_source = display_range.current_values;
                                }
                                
                                int start_val, end_val;
                                int start_idx, end_idx;
                                
                                // 确保start_val <= end_val
                                if(values_source[first_idx] <= values_source[second_idx]) {
                                    start_val = values_source[first_idx];
                                    end_val = values_source[second_idx];
                                    start_idx = first_idx;
                                    end_idx = second_idx;
                                } else {
                                    start_val = values_source[second_idx];
                                    end_val = values_source[first_idx];
                                    start_idx = second_idx;
                                    end_idx = first_idx;
                                }
                                
                                // 先更新控件文本，保存新的值到current_values供下次放大使用（t8-t15�?个控件）
                                for(int i = 0; i < 8; i++) {
                                    int val;
                                    if(i == 7) {
                                        // 最后一个点确保等于end_val
                                        val = end_val;
                                    } else {
                                        // �?个点按比例计�?                                        val = start_val + (end_val - start_val) * i / 7;
                                    }
                                    printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, val);
                                    display_range.current_values[i] = val; // 保存当前值供下次放大使用
                                }
                                
                                // 更新放大级别
                                if(display_range.zoom_level < 2) {
                                    display_range.zoom_level++;
                                }
                                
                                // 调试输出，显示放大操作详细信�?                                printf("debug.txt=\"放大: t%d(%d) �?t%d(%d), 范围:%d, 级别:%d\"\xff\xff\xff", 
                                       start_idx + 8, start_val, 
                                       end_idx + 8, end_val,
                                       end_val - start_val,
                                       display_range.zoom_level);
                                
                                // 恢复所有标签的正常颜色（t8-t15�?                                for(int i = 8; i <= 15; i++) {
                                    printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                                    printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景�?                                }
                                
                                // 最后调用放大数据处理函数进行同步放大数据透传
                                // 确保所有控件更新指令都在透传之前完成
                                ProcessZoomData(start_val, end_val);
                                
                                // 退出选择模式
                                display_range.is_selecting = 0;
                                display_range.first_selected = -1;
                                display_range.second_selected = -1;
                            }
                            // 如果选择了相同的点，不做任何处理
                        }
                    } else {
                        // 初始高亮t8
                        printf("t8.bco=61277\xff\xff\xff");  // 高亮第一个选项
                        
                        // 设置当前选中的标签索引（t8对应索引0�?                        display_range.cursor_pos = 0;
                        display_range.is_selecting = 1;  // 进入选择模式
                        display_range.first_selected = -1;
                        display_range.second_selected = -1;
                    }
                    break;
                    
                                case CURSOR_AUTO_SCALE:
                    printf("s0.dis=150\xff\xff\xff"); 
                    cursor_spectrum = CURSOR_AUTO_SCALE;
                    
                    // 处理自动缩放 - 找到当前光谱数据的最大值并设置为纵坐标上限
                    // 简化实现以节省内存
                    auto_scale_spectrum();
                    break;
                    
                case CURSOR_RESET_ZOOM:
                {
                    printf("s0.dis=100\xff\xff\xff"); 
                
                    cursor_spectrum = CURSOR_RESET_ZOOM;
                    // 处理重置缩放
                    // reset_zoom();
                    
                    // 恢复t8-t15的默认文本�?                    printf("t8.txt=\"0\"\xff\xff\xff");
                    printf("t9.txt=\"500\"\xff\xff\xff");
                    printf("t10.txt=\"1000\"\xff\xff\xff");
                    printf("t11.txt=\"1500\"\xff\xff\xff");
                    printf("t12.txt=\"2000\"\xff\xff\xff");
                    printf("t13.txt=\"2500\"\xff\xff\xff");
                    printf("t14.txt=\"3000\"\xff\xff\xff");
                    printf("t15.txt=\"3500\"\xff\xff\xff");
                    
                    // 恢复所有标签的正常颜色（t8-t15�?                    for(int i = 8; i <= 15; i++) {
                        printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                        printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景�?                    }
                    
                    // 重置选择状态和放大级别
                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    display_range.zoom_level = 0; // 重置放大级别
                    
                    // 重置current_values为默认值（t8-t15对应0-3500�?                    for(int i = 0; i < 8; i++) {
                        display_range.current_values[i] = DEFAULT_T_VALUES[i];
                    }
                    
                    // 重置缩放时，根据是否有标定参数决定显示哪个横坐标标签
                    if(saved_calib_params.is_valid) {
                        // 有标定参数时显示波长
                        printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                        printf("z2.vis=1\xff\xff\xff");    // z2可见
                        
                        // 更新t8-t15为波长�?                        for(int i = 0; i < 8; i++) {
                            float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                            float wavelength = saved_calib_params.k * x_pixel + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            display_range.current_values[i] = (int)wavelength;
                        }
                    } else {
                        // 无标定参数时显示像素�?                        printf("z1.vis=1\xff\xff\xff");    // z1可见
                        printf("z2.vis=0\xff\xff\xff");    // z2不可�?                        
                        // 更新t8-t15为像素�?                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                        }
                    }
                    
                    // 【修复】重置缩放后，重新透传完整的原始数据到屏幕
                    extern void ProcessAndDisplayGroupData(uint8_t group_index);
                    ProcessAndDisplayGroupData(current_group - 1); // current_group是1-12，数组索引是0-11
                    break;
                }
                    
                default:
                    break;
            }
            break;
            
        case INT_TIME_SELECT:
            // 从积分时间选择界面返回measure界面
            printf("page measure\xff\xff\xff");
            page = SPECTRUM_MEASURE;
            cursor_spectrum = CURSOR_INT_TIME;  
            
            // 更新当前选中的积分时�?            current_int_time = (IntegrationTime)cursor_int_time; // 类型转换，避免枚举类型混合警�?            
            // 向UART3发送对应的积分时间指令
            UART3_Send_Command(INT_TIME_COMMANDS[current_int_time]);
            
            // 更新积分时间显示文本
            printf("a.txt=\"%s\"\xff\xff\xff", INT_TIME_TEXT[current_int_time]);
            printf("a.bco=61277\xff\xff\xff");
            break;
            
        case CALIBRATION:
            // 标定界面的确认按钮处�?            switch(cursor_calibration1) {
                                case CURSOR_IMPORT_CALIB:
                     // 导入标定 - 优先使用保存的标定参数，否则基于已选择的峰进行标定计算
                     if(saved_calib_params.is_valid) {
                         // 使用保存的标定参�?                         calib_params.k = saved_calib_params.k;
                         calib_params.b = saved_calib_params.b;
                         calib_params.r_squared = saved_calib_params.r_squared;
                         calib_params.is_valid = 1;
                         
                         // 更新t8-t15的文本值为对应的波�?                         // 曲线x坐标范围73-793，对�?个控件t8-t15
                         for(int i = 0; i < 8; i++) {
                             float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                             float wavelength = calib_params.k * x_pixel + calib_params.b;
                             printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                             
                             // 更新display_range.current_values为波长�?                             display_range.current_values[i] = (int)wavelength;
                         }
                         
                         // 显示方差到t7控件
                         printf("t7.txt=\"%.4f\"\xff\xff\xff", calib_params.r_squared);
                         
                         // 标定后切换横坐标标签：z2（波长）可见，z1（像素位）不可见
                         printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                         printf("z2.vis=1\xff\xff\xff");    // z2可见
                         
                     } else if(calib_params.point_count >= 2) {
                         // 如果没有保存的参数，则基于已选择的峰进行标定计算
                         // 执行线性回归计算标定系�?                         float sum_x = 0, sum_y = 0, sum_xy = 0, sum_x2 = 0;
                         int n = calib_params.point_count;
                         
                         // 计算各种和�?                         for(int i = 0; i < n; i++) {
                             float x = calib_params.points[i].x;      // 像素位置
                             float y = calib_params.points[i].lambda; // 波长�?                             sum_x += x;
                             sum_y += y;
                             sum_xy += x * y;
                             sum_x2 += x * x;
                         }
                         
                         // 计算线性回归系�?y = kx + b (波长 = k * 像素位置 + b)
                         float denominator = n * sum_x2 - sum_x * sum_x;
                         if(denominator != 0) {
                             calib_params.k = (n * sum_xy - sum_x * sum_y) / denominator;
                             calib_params.b = (sum_y - calib_params.k * sum_x) / n;
                             
                             // 计算方差(R²)
                             float mean_y = sum_y / n;
                             float ss_tot = 0, ss_res = 0;
                             
                             for(int i = 0; i < n; i++) {
                                 float x = calib_params.points[i].x;
                                 float y_actual = calib_params.points[i].lambda;
                                 float y_predicted = calib_params.k * x + calib_params.b;
                                 
                                 ss_tot += (y_actual - mean_y) * (y_actual - mean_y);
                                 ss_res += (y_actual - y_predicted) * (y_actual - y_predicted);
                             }
                             
                             if(ss_tot != 0) {
                                 calib_params.r_squared = 1.0f - (ss_res / ss_tot);
                             } else {
                                 calib_params.r_squared = 0.0f;
                             }
                             
                             // 标定有效
                             calib_params.is_valid = 1;
                             
                             // 更新t8-t15的文本值为对应的波�?                             // 曲线x坐标范围73-793，对�?个控件t8-t15
                             for(int i = 0; i < 8; i++) {
                                 float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                                 float wavelength = calib_params.k * x_pixel + calib_params.b;
                                 printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                                 
                                 // 更新display_range.current_values为波长�?                                 display_range.current_values[i] = (int)wavelength;
                             }
                             
                             // 显示方差到t7控件
                             printf("t7.txt=\"%.4f\"\xff\xff\xff", calib_params.r_squared);
                             
                             // 标定后切换横坐标标签：z2（波长）可见，z1（像素位）不可见
                             printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                             printf("z2.vis=1\xff\xff\xff");    // z2可见
                             
                             // 标定有效，不修改t0内容
                             calib_params.is_valid = 1;
                         }
                     }
                     break;
                    
                case CURSOR_SAVE_CALIB:
                    // 保存标定 - 将当前标定参数保存起�?                    if(calib_params.is_valid) {
                        // 只保存关键的标定参数
                        saved_calib_params.k = calib_params.k;
                        saved_calib_params.b = calib_params.b;
                        saved_calib_params.r_squared = calib_params.r_squared;
                        saved_calib_params.is_valid = 1; // 标记保存的参数有�?                        
                        // 保存完成后取消当前按钮高亮，切换到导入标�?                        printf("saving.bco=50779\xff\xff\xff");  // 取消保存按钮高亮（正确标签）
                        printf("load.bco=61277\xff\xff\xff");   // 高亮导入按钮
                        cursor_calibration1 = CURSOR_IMPORT_CALIB; // 切换光标到导入标�?                        
                        // 同时更新光谱测量页面的t8-t15横坐标为保存的波长�?                        for(int i = 0; i < 8; i++) {
                            float x_pixel = 73 + (793 - 73) * i / 7.0f; // 等分73-793范围
                            float wavelength = saved_calib_params.k * x_pixel + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            
                            // 更新display_range.current_values为波长�?                            display_range.current_values[i] = (int)wavelength;
                        }
                        
                        // 保存标定后切换横坐标标签：z2（波长）可见，z1（像素位）不可见
                        printf("vis z1,0\\xff\\xff\\xff");    // z1不可�?                        printf("z2.vis=1\xff\xff\xff");    // z2可见
                        
                        // 可选：显示保存成功信息
                        // printf("t0.txt=\"标定已保存\"\xff\xff\xff");
                    }
                    break;
                    
                case CURSOR_SELECT_PEAK:
                    // 选择�?                    // 进入峰选择模式
                    calib_params.state = CALIB_SELECTING_PEAK;
                    
                    // 初始化p0的x值为73（最小值）
                    calib_params.temp_peak_x = 73;
                    
                    // 显示当前选中的峰值位�?                    printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                    
                    // 高亮confirm按钮并切换光�?                    printf("t5.bco=50779\xff\xff\xff"); // 取消t5高亮
                    printf("confirm.bco=61277\xff\xff\xff"); // 高亮confirm按钮
                    cursor_calibration1 = CURSOR_CONFIRM_POINT; // 切换光标到confirm
                    
                    // 不修改t0的文本内�?                    break;
                    
                case CURSOR_SELECT_WAVE:    
                    // 选择波长按钮功能
                    // b按钮文本已在确认点时更新
                    
                    // 进入峰选择模式
                    calib_params.state = CALIB_SELECTING_PEAK;
                    
                    // 初始化p0的x值为73（最小值）
                    calib_params.temp_peak_x = 73;
                    
                    // 显示当前选中的峰值位�?                    printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
                    
                    // 高亮confirm按钮并切换光�?                    printf("b.bco=50779\xff\xff\xff"); // 取消b高亮
                    printf("confirm.bco=61277\xff\xff\xff"); // 高亮confirm按钮
                    cursor_calibration1 = CURSOR_CONFIRM_POINT; // 切换光标到confirm
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
                            // 高亮显示选中的标签
                            printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文本
                        }
                        // 如果第一个点已选中，但第二个点未选中
                        else if(display_range.second_selected == -1) {
                            // 确保选择不同的点
                            if(current_pos != display_range.first_selected) { 
                                // 选中第二个点
                                display_range.second_selected = current_pos;
                                // 高亮显示选中的标签
                                printf("t%d.pco=63488\xff\xff\xff", current_pos + 8); // 红色文本
                                
                                // 获取选择的范围值
                                int first_idx = display_range.first_selected;
                                int second_idx = display_range.second_selected;
                                
                                // 获取数据源
                                const int *values_source;
                                
                                if(display_range.zoom_level == 0) {
                                    // 首次缩放，使用当前显示的值
                                    if(saved_calib_params.is_valid) {
                                        // 有标定参数时使用当前值
                                        values_source = display_range.current_values;
                                    } else {
                                        // 无标定参数时使用默认值
                                        values_source = DEFAULT_T_VALUES;
                                    }
                                } else {
                                    // 已缩放状态，使用当前值
                                    values_source = display_range.current_values;
                                }
                                
                                int start_val, end_val;
                                int start_idx, end_idx;
                                
                                // 确保start_val <= end_val
                                if(values_source[first_idx] <= values_source[second_idx]) {
                                    start_val = values_source[first_idx];
                                    end_val = values_source[second_idx];
                                    start_idx = first_idx;
                                    end_idx = second_idx;
                                } else {
                                    start_val = values_source[second_idx];
                                    end_val = values_source[first_idx];
                                    start_idx = second_idx;
                                    end_idx = first_idx;
                                }
                                
                                // 更新t8-t15的值
                                for(int i = 0; i < 8; i++) {
                                    int val;
                                    if(i == 7) {
                                        // 最后一个值为end_val
                                        val = end_val;
                                    } else {
                                        // 前7个值为start_val和end_val之间的线性插值
                                        val = start_val + (end_val - start_val) * i / 7;
                                    }
                                    printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, val);
                                    display_range.current_values[i] = val; // 更新当前值
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
                                extern void ProcessZoomData(int start_val, int end_val);
                                ProcessZoomData(start_val, end_val);
                                
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
                    // 标定界面的重置缩放功能
                    cursor_calibration1 = CURSOR_RESET_CALIB;
                    
                    // 重置缩放状态
                    display_range.zoom_level = 0;
                    
                    // 设置Y轴强度范围（10000-60000）
                    for(int i = 0; i < 6; i++) {
                        uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                    }
                    
                    // 设置t8-t15的默认值（根据是否有标定参数）
                    if(saved_calib_params.is_valid) {
                        // 如果有标定参数，使用波长显示
                        for(int i = 0; i < 8; i++) {
                            float wavelength = saved_calib_params.k * DEFAULT_T_VALUES[i] + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
                        }
                    } else {
                        // 如果没有标定参数，使用像素值显示
                        printf("t8.txt=\"0\"\xff\xff\xff");
                        printf("t9.txt=\"500\"\xff\xff\xff");
                        printf("t10.txt=\"1000\"\xff\xff\xff");
                        printf("t11.txt=\"1500\"\xff\xff\xff");
                        printf("t12.txt=\"2000\"\xff\xff\xff");
                        printf("t13.txt=\"2500\"\xff\xff\xff");
                        printf("t14.txt=\"3000\"\xff\xff\xff");
                        printf("t15.txt=\"3500\"\xff\xff\xff");
                        
                        // 更新当前值数组
                        for(int i = 0; i < 8; i++) {
                            display_range.current_values[i] = DEFAULT_T_VALUES[i];
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
                    
                    // 重新绘制波形（使用完整数据）
                    extern void ProcessZoomData(int start_val, int end_val);
                    ProcessZoomData(0, 3648);
                    break;
                    
                case CURSOR_CONFIRM_POINT:
                    // 确认标定�?                    // 如果当前正在选择�?                    if(calib_params.state == CALIB_SELECTING_PEAK) {
                        // 切换到选择波长状�?                        calib_params.state = CALIB_SELECTING_WAVE;
                        
                        // 根据当前标定点计数设置对应t24-t29的x坐标�?                        if(calib_params.point_count < 6) {
                            int t_index = 24 + calib_params.point_count;
                            
                            // 设置对应t标签的x坐标为p0的x�?                            printf("t%d.x=%d-37\xff\xff\xff", t_index, (int)calib_params.temp_peak_x);
                            
                            // 设置对应t标签的y坐标�?00
                            printf("t%d.y=99\xff\xff\xff", t_index);
                            
                            // 显示文本
                            printf("vis t%d,1\xff\xff\xff", t_index);
                            
                            // 保存标定点信�?                            calib_params.points[calib_params.point_count].x = calib_params.temp_peak_x;
                            calib_params.points[calib_params.point_count].lambda = CALIBRATION_WAVELENGTHS[calib_params.current_wavelength_index];
                            
                            // 增加标定点计�?                            calib_params.point_count++;
                            
                            // 切换到下一个波长选项并更新b按钮文本（循环模式）
                            calib_params.current_wavelength_index++;
                            if(calib_params.current_wavelength_index >= WAVELENGTH_COUNT) {
                                // 如果已经是最后一个波长，循环回到第一个波�?                                calib_params.current_wavelength_index = 0;
                            }
                            printf("b.txt=\"%.3fnm\"\xff\xff\xff", CALIBRATION_WAVELENGTHS[calib_params.current_wavelength_index]);
                            
                            // 如果所有点都已确认，进行标定计�?                            if(calib_params.point_count >= 6) {
                                // 可以进行标定计算
                                calib_params.state = CALIB_FITTING;
                                
                                // 计算标定参数
                                // 简单线性回�?                                float sum_x = 0, sum_y = 0, sum_xy = 0, sum_xx = 0;
                                for(int i = 0; i < calib_params.point_count; i++) {
                                    sum_x += calib_params.points[i].x;
                                    sum_y += calib_params.points[i].lambda;
                                    sum_xy += calib_params.points[i].x * calib_params.points[i].lambda;
                                    sum_xx += calib_params.points[i].x * calib_params.points[i].x;
                                }
                                
                                float n = calib_params.point_count;
                                calib_params.k = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x);
                                calib_params.b = (sum_y - calib_params.k * sum_x) / n;
                                
                                // 标记标定有效
                                calib_params.is_valid = 1;
                            }
                            
                            // 准备下一次选择
                            calib_params.state = CALIB_IDLE;
                            
                            // 重新进入峰选择模式
                            calib_params.state = CALIB_SELECTING_PEAK;
                            
                            // 不重置p0的x值，保留上一次设置的位置
                            
                            // 保持confirm按钮高亮
                            printf("confirm.bco=61277\xff\xff\xff");
                            cursor_calibration1 = CURSOR_CONFIRM_POINT;
                        }
                    }
                    break;
                    
                default:
                    break;
            }
            break;
            
        case WAVELENGTH_SELECT:
            // 波长选择界面的确认按钮处�?            if(calib_params.state == CALIB_SELECTING_WAVE) {
                // 获取选中的波长�?                float selected_wavelength = CALIBRATION_WAVELENGTHS[cursor_wavelength];
                
                // 保存标定�?                if(calib_params.point_count < 10) { // 最�?0个标定点
                    calib_params.points[calib_params.point_count].x = calib_params.temp_peak_x;
                    calib_params.points[calib_params.point_count].lambda = selected_wavelength;
                    calib_params.point_count++;
                }
                
                // 返回标定界面
                printf("page calibration\xff\xff\xff");
                page = CALIBRATION;
                
                // 重置状�?                calib_params.state = CALIB_IDLE;
                
                // 不修改t0和t1的文本内�?                
                // 如果有足够的标定点，可以计算标定参数
                if(calib_params.point_count >= 2) {
                    // 计算线性拟合参数（简单的线性回归）
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
                    
                    // 标记标定有效
                    calib_params.is_valid = 1;
                }
            }
            break; 
            
        case QUERY_EXPORT:
            // query界面的确认按钮处�?            if(cursor_spectrum == CURSOR_EXPORT_USB) {
                // 导出光谱按钮被按�?                printf("page outputing\xff\xff\xff");
                page=OUTPUTING;
                printf("t2.txt=\"initing..\"\xff\xff\xff");
                ch376_init_with_baudrate_change();
                printf("t2.txt=\"writing..\"\xff\xff\xff");
                ch376_writetest();  // 函数内部会自动处理进度条
                printf("page outed\xff\xff\xff");
                page=OUTPUT_COMPLETE;
                if(output_flag) printf("t1.txt=\"导出完成!\"\xff\xff\xff");
                else printf("t1.txt=\"导出失败!\"\xff\xff\xff");
            } else {
                // 组别功能已删除，这里可以处理其他逻辑
            }
            break;
            
        default:
            break;
    }
}

// 返回按键处理
void cancel_button(void) {
    switch(page) {
        case MAIN:
            // 主界面按返回键无效果
            break;
            
        case SPECTRUM_MEASURE:
            // 如果在放大查看的选择模式下，先退出选择模式
            if(display_range.is_selecting && cursor_spectrum == CURSOR_ZOOM) {
                // 退出选择模式
                display_range.is_selecting = 0;
                display_range.first_selected = -1;
                display_range.second_selected = -1;
                
                // 恢复所有标签的正常颜色
                for(int i = 8; i <= 16; i++) {
                    printf("t%d.bco=50779\xff\xff\xff", i);
                    printf("t%d.pco=0\xff\xff\xff", i); // 恢复黑色文本
                }
                
                // 保持在放大查看按钮上
                printf("zoom.bco=61277\xff\xff\xff");
            } else {
                // 取消当前按钮的高�?                switch(cursor_spectrum) {
                    // CURSOR_GROUP case已删�?                    case CURSOR_INT_TIME:
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
                        printf("reset2.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_EXPORT_USB:
                        printf("output.bco=50779\xff\xff\xff");
                        break;
                    default:
                        break;
                }
                
                // 返回主界�?                printf("page main\xff\xff\xff");
                page = MAIN;
                cursor_main = CALIBO;  // 默认选中校准按钮
                printf("calibo.bco=61277\xff\xff\xff");  // 高亮校准按钮
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
            
            // 特殊处理：如果在选择峰模式下按取消，不返回主界面
            if(cursor_calibration1 == CURSOR_CONFIRM_POINT && calib_params.state == CALIB_SELECTING_PEAK) {
                // 取消确认按钮高亮，重新高亮选择峰按�?                printf("confirm.bco=50779\xff\xff\xff");  // 取消确认按钮高亮
                printf("t5.bco=61277\xff\xff\xff");       // 高亮选择峰按�?                cursor_calibration1 = CURSOR_SELECT_PEAK;  // 切换光标到选择�?                
                // 退出峰选择模式
                calib_params.state = CALIB_IDLE;
            } else {
                // 其他情况：取消当前按钮的高亮并返回measure界面
                switch(cursor_calibration1) {
                    case CURSOR_IMPORT_CALIB:
                        printf("load.bco=50779\xff\xff\xff");
                        break;
                                    case CURSOR_SAVE_CALIB:
                    printf("saving.bco=50779\xff\xff\xff");  // 修正为saving
                    break;
                    case CURSOR_SELECT_PEAK:
                        printf("t5.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_SELECT_WAVE:
                        printf("b.bco=50779\xff\xff\xff");
                        break;
                    case CURSOR_CONFIRM_POINT:
                        printf("confirm.bco=50779\xff\xff\xff");
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
                
                // 标定界面返回measure界面
                printf("page measure\xff\xff\xff");
                page = SPECTRUM_MEASURE;
                cursor_spectrum = CURSOR_CALIBRATION;  // 默认选中calibration按钮
                printf("paging.bco=61277\xff\xff\xff");  // 高亮显示calibration按钮
                
                // 【修复】如果之前进行过放大操作，重置缩放状态和横坐标
                if(display_range.zoom_level > 0) {
                    // 重置Y轴强度范围到10000-60000
                    for(int i = 0; i < 6; i++) {
                        uint32_t intensity_value = 10000 + (60000 - 10000) * i / 5;
                        printf("t%d.txt=\"%lu\"\xff\xff\xff", i + 17, intensity_value);
                    }
                    
                    // 重置选择状态和放大级别
                    display_range.is_selecting = 0;
                    display_range.first_selected = -1;
                    display_range.second_selected = -1;
                    display_range.zoom_level = 0;
                    
                    // 重置current_values为默认值
                    for(int i = 0; i < 8; i++) {
                        display_range.current_values[i] = DEFAULT_T_VALUES[i];
                    }
                    
                    // 恢复t8-t15的标签颜色
                    for(int i = 8; i <= 15; i++) {
                        printf("t%d.pco=0\xff\xff\xff", i); // 黑色文本
                        printf("t%d.bco=50779\xff\xff\xff", i); // 正常背景色
                    }
                    
                    // 根据是否有标定参数决定显示哪个横坐标
                    if(saved_calib_params.is_valid) {
                        // 有标定参数时显示波长
                        printf("z1.vis=0\xff\xff\xff");    // z1不可见
                        printf("z2.vis=1\xff\xff\xff");    // z2可见
                        
                        // 更新t8-t15为波长值
                        for(int i = 0; i < 8; i++) {
                            float x_pixel = 73 + (793 - 73) * i / 7.0f;
                            float wavelength = saved_calib_params.k * x_pixel + saved_calib_params.b;
                            printf("t%d.txt=\"%.1f\"\xff\xff\xff", i + 8, wavelength);
                            display_range.current_values[i] = (int)wavelength;
                        }
                    } else {
                        // 无标定参数时显示像素值
                        printf("z1.vis=1\xff\xff\xff");    // z1可见
                        printf("z2.vis=0\xff\xff\xff");    // z2不可见
                        
                        // 更新t8-t15为像素值
                        for(int i = 0; i < 8; i++) {
                            printf("t%d.txt=\"%d\"\xff\xff\xff", i + 8, DEFAULT_T_VALUES[i]);
                        }
                    }
                    
                    // 重新显示当前组的完整数据
                    extern uint8_t current_group;
                    extern void ProcessAndDisplayGroupData(uint8_t group_index);
                    if(current_group >= 1 && current_group <= 12) {
                        // 延迟确保页面加载完成
                        for(volatile uint32_t delay_count = 0; delay_count < 1000000; delay_count++) {
                            __NOP();
                        }
                        ProcessAndDisplayGroupData(current_group - 1);
                    }
                }
            }
            break;
            
        case QUERY_EXPORT:
            // 取消query界面当前按钮的高�?            // 组别功能已删�?            // 取消功能按钮高亮
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
                    printf("reset2.bco=50779\xff\xff\xff");
                    break;
                case CURSOR_EXPORT_USB:
                    printf("output.bco=50779\xff\xff\xff");
                    break;
                default:
                    break;
            }
            
            // query界面返回光谱测量界面
            printf("page measure\xff\xff\xff");
            page = SPECTRUM_MEASURE;
            cursor_spectrum = CURSOR_INT_TIME;  // 默认选中积分时间
            printf("a.bco=61277\xff\xff\xff");  // 高亮积分时间按钮
            printf("a1.bco=61277\xff\xff\xff");     // 高亮a1控件
            printf("a7.bco=61277\xff\xff\xff");     // 高亮a7控件
            break;
            
        case OUTPUTING:
            // 导出中界面不响应取消按钮
            break;
            
        case OUTPUT_COMPLETE:
            // 导出完成界面返回主界�?            printf("page main\xff\xff\xff");
            page = MAIN;
            cursor_main = DATA;  // 默认选中数据查询按钮
            printf("data.bco=61277\xff\xff\xff");  // 高亮显示数据查询按钮
            break;
            
        case INT_TIME_SELECT:
            // 积分时间选择界面返回measure界面
            printf("page measure\xff\xff\xff");
            page = SPECTRUM_MEASURE;
            cursor_spectrum = CURSOR_INT_TIME;  // 默认选中积分时间按钮
            printf("a.bco=61277\xff\xff\xff");  // 高亮显示积分时间按钮
            break;
            
        case WAVELENGTH_SELECT:
            // 波长选择界面返回标定界面
            printf("page calibration\xff\xff\xff");
            page = CALIBRATION;
            break;
            
        default:
            break;
    }
}








// 重置所有组别数�?void reset_group_data(void) {
    // 重置组别计数
    current_group = 1;
    saved_groups = 0;
    
    // 更新group按钮的文�?    printf("group.txt=\"%d\"\xff\xff\xff", current_group);
}

// 初始化标定界�?void calibration_page_init(void) {
    // 初始化标定参�?    calib_params.point_count = 0;
    calib_params.is_valid = 0;
    calib_params.state = CALIB_IDLE;
    calib_params.temp_peak_x = 0;
    calib_params.cursor_pos = 0;
    calib_params.is_selecting = 0;
    calib_params.select_start = 0;
    calib_params.select_end = 0;
    calib_params.current_wavelength_index = 0; // 从第一个波长开�?    
    // 重置标定系数
    calib_params.k = 0;
    calib_params.b = 0;
    calib_params.r_squared = 0;
    
    // 只在首次进入时设置默认光标，保持用户之前的选择
    if(cursor_calibration1 == 0) { // 如果光标未初始化
        cursor_calibration1 = CURSOR_IMPORT_CALIB; // 设置默认为导入标�?    }
    
    // 根据当前光标位置高亮对应按钮
    // 先取消所有按钮高�?    printf("load.bco=50779\xff\xff\xff");
    printf("saving.bco=50779\xff\xff\xff");  // 修正为saving
    printf("t5.bco=50779\xff\xff\xff");
    printf("b.bco=50779\xff\xff\xff");
    printf("confirm.bco=50779\xff\xff\xff");
    
    // 根据当前光标高亮对应按钮
    switch(cursor_calibration1) {
        case CURSOR_IMPORT_CALIB:
            printf("load.bco=61277\xff\xff\xff");
            break;
        case CURSOR_SAVE_CALIB:
            printf("saving.bco=61277\xff\xff\xff");  // 修正为saving
            break;
        case CURSOR_SELECT_PEAK:
            printf("t5.bco=61277\xff\xff\xff");
            break;
        case CURSOR_SELECT_WAVE:
            printf("b.bco=61277\xff\xff\xff");
            break;
        case CURSOR_CONFIRM_POINT:
            printf("confirm.bco=61277\xff\xff\xff");
            break;
        default:
            // 默认高亮导入标定按钮
            printf("load.bco=61277\xff\xff\xff");
            cursor_calibration1 = CURSOR_IMPORT_CALIB;
            break;
    }
    
    // 初始化b按钮的文本内容为第一个波�?    printf("b.txt=\"%.3fnm\"\xff\xff\xff", CALIBRATION_WAVELENGTHS[calib_params.current_wavelength_index]);
    
    
    for(int i = 24; i <= 29; i++) {
        printf("vis t%d,0\xff\xff\xff", i); // 设置为隐�?    }
    
    // 进入标定界面时自动执行addt透传，显示存储的曲线
    extern SpectrumGroupInfo spectrum_groups_info[12];
    extern uint8_t spectrum_data_ram[1][DATA_BUFFER_SIZE];
    extern volatile uint8_t addt_in_progress;
    
    // 检查第一组RAM数据是否有效
    if(spectrum_groups_info[0].is_valid && spectrum_groups_info[0].data_length >= 3640 && !addt_in_progress) {
        // 标记addt正在进行，防止冲�?        addt_in_progress = 1;
        
        // 发送addt透传指令，将数据显示到s0波形控件
        printf("addt s0.id,0,729\xff\xff\xff");
        
        // 基于循环计数的延迟（等待屏幕响应�?        for(volatile uint32_t delay_count = 0; delay_count < 2000000; delay_count++) {
            __NOP(); // 空操作，防止编译器优�?        }
        
        // 透传729个数据点（从3648字节的原始数据中等间隔采样）
        uint8_t* source_data = spectrum_data_ram[0];
        for(int i = 0; i < 729; i++) {
            // 等间隔采样：�?648个数据点中采�?29个点
            int src_index = i * 5; // 3648/729 �?5
            if(src_index < DATA_BUFFER_SIZE) {
                putchar(source_data[src_index]);
            }
        }
        
        // 短延迟确保数据传输完�?        for(volatile uint32_t delay_count = 0; delay_count < 200000; delay_count++) {
            __NOP();
        }
        
        // 发送结束标�?        printf("\x01\xff\xff\xff");
        
        // 最终延迟确保传输完全结�?        for(volatile uint32_t delay_count = 0; delay_count < 300000; delay_count++) {
            __NOP();
        }
        
        // 完成后重置标�?        addt_in_progress = 0;
    }
    
    // 不修改t0和t1的文本内�?}

// 功能按钮处理
void fun_button(void) {
    switch(page) {
        case MAIN:
            // 主界面的功能按钮处理
            break;
            
        case SPECTRUM_MEASURE:
            // 光谱测量页面的功能按钮处�?            break;
            
        case CALIBRATION:
            // 标定界面的功能按钮处�?            // 如果在峰选择模式下，可以重置p0的位置到中间�?            if(calib_params.state == CALIB_SELECTING_PEAK) {
                // 重置p0的位置到中间�?                calib_params.temp_peak_x = (73 + 793) / 2; // 中间�?                // 更新显示
                printf("p0.x=%d\xff\xff\xff", (int)calib_params.temp_peak_x);
            }
            break;
            
        case QUERY_EXPORT:
            // 查询导出页面的功能按钮处�?            break;
            
        default:
            break;
    }
}

// UART3发送测试函数，确保发送正常工�?void UART3_Send_Command(uint8_t cmd)
{
    // 使用轮询模式发送单个命�?    HAL_StatusTypeDef status = HAL_UART_Transmit(&huart3, &cmd, 1, 100);
    if (status != HAL_OK) {
        // 如果发送失败，重新初始化UART3
        MX_USART3_UART_Init();
        // 再次尝试发�?        HAL_UART_Transmit(&huart3, &cmd, 1, 100);
    }
}

// 自动缩放光谱函数 - 使用dis属性简化实�?void auto_scale_spectrum(void) {
    extern uint8_t ProcessedDataBuffer[]; // 引用处理后的光谱数据
    uint8_t max_intensity = 0;
    
    // 遍历729个数据点，找到最大强度�?    for(uint16_t i = 0; i < 729; i++) {
        if(ProcessedDataBuffer[i] > max_intensity) {
            max_intensity = ProcessedDataBuffer[i];
        }
    }
    
    // 根据最大强度计算缩放比�?    uint16_t dis_value;
    if(max_intensity == 0) {
        dis_value = 100; // 默认比例
    } else {
        // 计算缩放比例：max_intensity/255 * 1000，范�?0-1000
        dis_value = (uint16_t)(((uint32_t)max_intensity * 1000) / 255);
        if(dis_value < 10) dis_value = 10;   // 最小�?        if(dis_value > 1000) dis_value = 1000; // 最大�?    }
    
    // 使用dis属性调整显示缩�?    printf("s0.dis=%d\xff\xff\xff", dis_value);
}


