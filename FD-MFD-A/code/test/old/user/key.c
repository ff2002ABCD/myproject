#include "key.h"
#include "tim.h"
//#include "iwdg.h"
KEY_STATE KeyState;
KEY_VALUE g_Key;
KEY_TYPE g_KeyActionFlag;
extern int fputc(int ch, FILE* file);
uint16_t Count=10000,last_Count=10000;
uint16_t Diretion=0;
_Bool flag_10s;

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
			case KEY_FUN:
					 
					if(g_KeyActionFlag==SHORT_KEY) 
					{
						func_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
					else if(g_KeyActionFlag==LONG_KEY) 
					{
						func_button();
						g_Key=KEY_NULL;g_KeyActionFlag=NULL_KEY;
					}
			break;
			default: break;
	}
}

void get_encoder()
{
//		last_Count=Count;
		Diretion =  __HAL_TIM_IS_TIM_COUNTING_DOWN(&htim2);     
		Count = __HAL_TIM_GET_COUNTER(&htim2);
//		printf("转动方向:%d  脉冲数:%d \r\n",Diretion,Count);
		if(Count>30000) 
		{
	//		printf("正转\r\n");
			clockwise();
		}
		else if(Count<30000)
		{
	//		printf("反转\r\n");
			counter_clockwise();
		}
		TIM2->CNT=30000;
//		if(Diretion==0) if(Count-last_Count<0) last_Count=Count-1;
//		if(Diretion==1) if(Count-last_Count>0) last_Count=Count+1;
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if(htim->Instance==htim3.Instance)//10ms
	{	
		
		static int cnt1=0,cnt2=0,cnt3=0,cnt4=0,cnt5=0;
		Key_Scan();
		do_key();
		cnt1++;
		cnt2++;
		cnt3++;
		cnt4++;
		cnt5++;
		if(cnt1>=50)//500ms
		{
//			if(Current==100)Current=-100;
//			else if(Current==-100)Current=100;
			cnt1=0;
			switch(page)//控制继电器开断
			{
				case MAIN:
					if(cursor_main==CAL)
					{
						HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
						Current=100;
					}
					else
					{
						HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
						Current=0;
					}
					break;
				case XY_CALIBO:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
				break;
				case Z_CALIBO:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
				break;
				case XY_CALIBO_1:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					Current=100;
				break;
				case Z_CALIBO_1:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					Current=100;
				break;
				case PLACE:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					Current=100;
				break;
				case PLACE_RIGHT:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
				break;
				case PLACE_RIGHT_1:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					Current=100;
				break;
				case PLACE_UP:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
				break;
				case MEASURE_GROUND:
					Current=0;
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
					break;
				case MEASURE_COIL:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					break;
				case MEASUER_START:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					break;
				case MEASUER_START_1:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_SET);
					break;
				default:
					HAL_GPIO_WritePin(SW_GPIO_Port,SW_Pin,GPIO_PIN_RESET);
					break;
			}
			Current_control();
			
			if(page==MAIN)//输出结果
			{
				if(cursor_main!=CAL)
				{
					printf("vis k,0\xff\xff\xff");
				}
				else
				{
					printf("vis k,1\xff\xff\xff");
					printf("k.txt=\"%.2f\"\xff\xff\xff",k);
				}
			}
			else if(page==MEASURE_GROUND)
			{		
				get_averdata();
				printf("mod.txt=\"%.1f\"\xff\xff\xff",strength*100);
				printf("x.txt=\"%.1f\"\xff\xff\xff",GaX*100);
				printf("y.txt=\"%.1f\"\xff\xff\xff",GaY*100);
				printf("z.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
//				printf("x.txt=\"%.1f\"\xff\xff\xff",rawGaX*100);
//				printf("y.txt=\"%.1f\"\xff\xff\xff",rawGaY*100);
//				printf("z.txt=\"%.1f\"\xff\xff\xff",rawGaZ*100);
			}
			else if(page==MEASURE_COIL)
			{
				get_averdata();
				set_zero();
				printf("a.txt=\"%.1f\"\xff\xff\xff",Current);
//				printf("a1.txt=\"%d\"\xff\xff\xff",(int)Current/100);
//				printf("a2.txt=\"%d\"\xff\xff\xff",(int)Current/10%10);
//				printf("a3.txt=\"%d\"\xff\xff\xff",(int)Current%10);
//				printf("a4.txt=\"%d\"\xff\xff\xff",(int)Current*10%10);
				printf("mod.txt=\"%.1f\"\xff\xff\xff",strength*100);
				printf("x.txt=\"%.1f\"\xff\xff\xff",GaX*100);
				printf("y.txt=\"%.1f\"\xff\xff\xff",GaY*100);
				printf("z.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
				if(beishu==1){printf("move p0,111,277,111,277,0,0\xff\xff\xff");}
					else if(beishu==10){printf("move p0,80,277,80,277,0,0\xff\xff\xff");}
						else if(beishu==100){printf("move p0,59,277,59,277,0,0\xff\xff\xff");}
			}
			else if(page==MEASUER_START)
			{
				get_averdata();
				set_zero();
				printf("group.txt=\"第%d组\"\xff\xff\xff",group_num+1);
				printf("number.txt=\"第%d个\"\xff\xff\xff",number_now+1);
				if(pos_measure_start>=9000) pos_measure_start=9000;
				if(pos_measure_start<=0) pos_measure_start=0;
				printf("p1.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/1000);	
				printf("p2.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/100%10);	
				printf("p3.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)/10%10);	
				printf("p4.txt=\"%d\"\xff\xff\xff",(int)(pos_measure_start)%10);
				printf("a.txt=\"%.1f\"\xff\xff\xff",Current);
//				printf("a1.txt=\"%d\"\xff\xff\xff",(int)Current/100);
//				printf("a2.txt=\"%d\"\xff\xff\xff",(int)Current/10%10);
//				printf("a3.txt=\"%d\"\xff\xff\xff",(int)Current%10);
//				printf("a4.txt=\"%d\"\xff\xff\xff",(int)Current*10%10);
				printf("mod.txt=\"%.1f\"\xff\xff\xff",strength*100);
				printf("x.txt=\"%.1f\"\xff\xff\xff",GaX*100);
				printf("y.txt=\"%.1f\"\xff\xff\xff",GaY*100);
				printf("z.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
				
			}
			else if(page==MEASUER_START_1)
			{
				get_averdata();
				set_zero();
				printf("group.txt=\"第%d组\"\xff\xff\xff",group_num+1);
				printf("number.txt=\"第%d个\"\xff\xff\xff",number_now+1);
				printf("t4.txt=\"%.2f\"\xff\xff\xff",test_position[number_now]);
				
				printf("a.txt=\"%.1f\"\xff\xff\xff",Current);
				printf("mod.txt=\"%.1f\"\xff\xff\xff",strength*100);
				printf("x.txt=\"%.1f\"\xff\xff\xff",GaX*100);
				printf("y.txt=\"%.1f\"\xff\xff\xff",GaY*100);
				printf("z.txt=\"%.1f\"\xff\xff\xff",GaZ*100);
				
			}
			else if(page==GENERATE_COORDINATES)
			{
				if(start_position_int>=9000) start_position_int=9000;
				if(start_position_int<=0) start_position_int=0;
				if(end_position_int>=9000)end_position_int=9000;
				if(end_position_int<=0) end_position_int=0;
				if(position_step_int>=9000) position_step_int=9000;
				if(position_step_int<=0) position_step_int=0;
				printf("s1.txt=\"%d\"\xff\xff\xff",start_position_int/1000);
				printf("s2.txt=\"%d\"\xff\xff\xff",start_position_int/100%10);
				printf("s3.txt=\"%d\"\xff\xff\xff",start_position_int/10%10);
				printf("s4.txt=\"%d\"\xff\xff\xff",start_position_int%10);
				printf("e1.txt=\"%d\"\xff\xff\xff",end_position_int/1000);
				printf("e2.txt=\"%d\"\xff\xff\xff",end_position_int/100%10);
				printf("e3.txt=\"%d\"\xff\xff\xff",end_position_int/10%10);
				printf("e4.txt=\"%d\"\xff\xff\xff",end_position_int%10);
				printf("u1.txt=\"%d\"\xff\xff\xff",position_step_int/1000);
				printf("u2.txt=\"%d\"\xff\xff\xff",position_step_int/100%10);
				printf("u3.txt=\"%d\"\xff\xff\xff",position_step_int/10%10);
				printf("u4.txt=\"%d\"\xff\xff\xff",position_step_int%10);
				printf("group_num.txt=\"第%d组:\"\xff\xff\xff",group_now+1);
			}
			else if(page==DATA_OUTPUT)
			{
				for(int i=0;i<group_num;i++)
				{
					printf("t%d.txt=\"第%d组\"\xff\xff\xff",i,i+1);
				}
			}
			else if(page==AUTO_SETZERO)
			{
				measure_ground();
			}
			else if(page==PLACE|page==PLACE_UP|page==PLACE_RIGHT|page==PLACE_UP_1|page==PLACE_RIGHT_1)
			{
				strength=sqrt(rawGaX*rawGaX+rawGaY*rawGaY+rawGaZ*rawGaZ);
				printf("mod.txt=\"%.1f\"\xff\xff\xff",strength*100);
			}
		}
		else if(cnt2>=25)
		{
			//HAL_IWDG_Refresh(&hiwdg);
			cnt2=0;
			get_encoder();
		}
		else if(cnt3>=50)
		{
			cnt3=0;
			switch(page)
			{
				case XY_CALIBO:calibo_x0y0();break;
				case Z_CALIBO:calibo_z0();break;
				case XY_CALIBO_1:calibo_x1y1();break;
				case Z_CALIBO_1:calibo_z1();break;
				default:GaXmax=0,GaXmin=0,GaYmax=0,GaYmin=0,GaZmax=0,GaZmin=0;break;
			}
		}
		else if(cnt4>=100)
		{
			cnt4=0;
//			if(HAL_I2C_IsDeviceReady(&hi2c1, HMC5883L_Addr, 3, 100)!=HAL_OK) 
//			{if(GaX_array[i]<GaXmin) GaXmin=GaX_array[i];
//				HAL_I2C_DeInit(&hi2c1);
//				MX_I2C1_Init();
//			}
//				Init_HMC5883L_HAL(&hi2c1);
//			}
			
		}
		else if(cnt5>=2)
		{
			cnt5=0;
			if(page!=XY_CALIBO&&page!=Z_CALIBO&&page!=XY_CALIBO_1&&page!=Z_CALIBO_1)
			start_measure();
		}
	}
}