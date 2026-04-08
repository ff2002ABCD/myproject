#include "key.h"
#include "tim.h"
#include "function.h"
#include "menu.h"  // 添加menu.h以访问PAGE和CalibrationParams
#include "encoder.h"  // 添加编码器头文件
//#include "iwdg.h"
KEY_STATE KeyState;
KEY_VALUE g_Key;
KEY_TYPE g_KeyActionFlag;
extern int fputc(int ch, FILE* file);
_Bool flag_10s;

// 添加Key_Init初始化函数实现
void Key_Init(void)
{
   KeyState = KEY_CHECK;
   g_Key = KEY_NULL;
   g_KeyActionFlag = NULL_KEY;
}

void Key_Scan(void)
{	
		static uint32_t TimeCnt = 0;
    static uint8_t lock = 0;
		static uint16_t long_counter=0;
		static uint8_t Cnt;
    switch (KeyState)
    {
        case   KEY_CHECK:    
            if(!Key)   
            {
                KeyState =  KEY_COMFIRM;  
            }
						TimeCnt = 0;                
            lock = 0;
            break;
        case   KEY_COMFIRM:
            if(!Key)            
            {
                if(0 == KEYUP)
                    g_Key = KEY_UP;
								else if(0 == KEYCONFIRM)
                    g_Key = KEY_CONFIRM;
                else if(0 == KEYDOWN)
                    g_Key = KEY_DOWN;
                
								else if(0 == KEYCANCEL)
                    g_Key = KEY_CANCEL;
								else if(0 == KEYRIGHT)
                    g_Key = KEY_RIGHT;
								else if(0 == KEYLEFT)
                    g_Key = KEY_LEFT;
                else if(0 == KEYFUN)
                    g_Key = KEY_FUN;
				if(!lock)   lock = 1;
								TimeCnt++;  
								Cnt=10;
								if(long_counter==0)//第一次检测
								{				
										if(TimeCnt>Cnt*5)         
										{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
											long_counter++;
										}
								}
                if(long_counter!=0)
								{								
									if(TimeCnt>Cnt*5)         
									{
											g_KeyActionFlag = LONG_KEY;	
											TimeCnt = 0;  
											lock = 0; 
										long_counter++;								 
									}        
								} 
								if(long_counter>=15)
								{
									flag_10s=1;
									long_counter=0;
								}
            }   
            else                      
            {							
                if(1==lock&&long_counter==0)           
                {
                    g_KeyActionFlag = SHORT_KEY;      
                    KeyState =  KEY_RELEASE;   
                }
                
                else         
                {		
										
                    KeyState =  KEY_CHECK;  
                }
								long_counter=0;
            } 
            break;
        
         case  KEY_RELEASE:
             if(Key)                
             { 
								
                 KeyState =  KEY_CHECK;
             } 
             break;
         default: break;
    }
}

void do_key()
{
	switch(g_Key)
   {
			case KEY_UP:
				
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						up_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			
			case KEY_DOWN:
					 
						if(g_KeyActionFlag==SHORT_KEY) 
						{
							down_button();
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
						else if(g_KeyActionFlag==LONG_KEY) 
						{
							
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
						}
			break;
			
			case KEY_CONFIRM:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						confirm_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					} 
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_CANCEL:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						cancel_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			case KEY_RIGHT:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						right_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						right_button();
					// 在峰选择模式或坐标查看模式下不重置g_KeyActionFlag，实现加速移动
						extern PAGE page;
						extern CalibrationParams calib_params;
					extern ViewCoordinateState view_coord_state;
					if((page == CALIBRATION && calib_params.state == CALIB_SELECTING_PEAK) ||
					   (page == SPECTRUM_MEASURE && view_coord_state.is_active)) {
							g_Key=KEY_NULL; // 不重置g_KeyActionFlag，保持长按状态
						} else {
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY; // 正常重置
						}
					}
			break;
            case KEY_LEFT:
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						left_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
                    else if(g_KeyActionFlag==LONG_KEY) 
					{
						left_button();
					// 在峰选择模式或坐标查看模式下不重置g_KeyActionFlag，实现加速移动
						extern PAGE page;
						extern CalibrationParams calib_params;
					extern ViewCoordinateState view_coord_state;
					if((page == CALIBRATION && calib_params.state == CALIB_SELECTING_PEAK) ||
					   (page == SPECTRUM_MEASURE && view_coord_state.is_active)) {
							g_Key=KEY_NULL; // 不重置g_KeyActionFlag，保持长按状态
						} else {
							g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY; // 正常重置
						}
					}
			break;
            case KEY_FUN:
                    if(g_KeyActionFlag==SHORT_KEY) 
                    {
                        fun_button();
                        g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
                    }
                    else if(g_KeyActionFlag==LONG_KEY) 
                    {
                        fun_button();
                        g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
                    }
            break;
		default: break;}
}
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if(htim->Instance==htim3.Instance)//10ms
	{	
		static int cnt1=0,cnt2=0,cnt3=0,cnt4=0,cnt5=0;
		
		// 每10ms扫描一次按键
		Key_Scan();
		do_key();
		
		// 每10ms扫描一次编码器
		get_encoder();
		
		// 每10ms检查重置按钮超时
		check_reset_button_timeout();
		
		cnt1++;
		cnt2++;
		cnt3++;
		cnt4++;
		cnt5++;
		
		if(cnt1>=50)//500ms
		{
			cnt1=0;
			switch(page)//控制继电器开断
			{
				case MAIN:
					if(cursor_main==CALIBO)
					{
						// HAL_GPIO_WritePin(CANCEL_GPIO_Port,CANCEL_Pin,GPIO_PIN_SET);  // 注释掉GPIO控制，避免与按键功能冲突
						Current=100;
					}
					else
					{
						// HAL_GPIO_WritePin(CANCEL_GPIO_Port,CANCEL_Pin,GPIO_PIN_RESET);  // 注释掉GPIO控制，避免与按键功能冲突
						Current=0;
					}
					break;
				default:
					break;
			}
			Current_control();
		}
	}
}
