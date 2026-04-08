#include "menu.h"
#include "stdio.h"
#include "function.h"
#include "main.h"
#include "adc.h"
#include "gui.h"
#include "ch376.h"

extern int fputc(int ch, FILE* file);
PAGE page=0;
CURSOR_MAIN cursor_main=1;
CURSOR_MEA_JOURNEY cursor_mea_journey=0;
CURSOR_MEA_ANGLE cursor_mea_angle=0;
CURSOR_MEA_TIME cursor_mea_time=0;
CURSOR_QUERY_JOURNEY cursor_query_journey=0;
CURSOR_QUERY_ANGLE cursor_query_angle=0;
CURSOR_QUERY_TIME cursor_query_time=0;
MEA_STATE mea_state=2;
OFFSET_MOVE x_offset_move=1;
_Bool button_called=0;

STEP step=_10s;

void up_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MAIN:
		{
			if(cursor_main==1) cursor_main=7;
			cursor_main--;
		}break;
		case MEA_JOURNEY:
		{
			switch(cursor_mea_journey)
			{
				default:
				{
					cursor_mea_journey--;
					if(cursor_mea_journey==0) cursor_mea_journey=4;
				}break;
				case MEA_JOURNEY_NONE:
				{
					if(ygrid_multiple_journey_index!=ygrid_multiple_journey_index_max-1)
					ygrid_multiple_journey_index++;
				}break;
			}
		}break;
		case MEA_ANGLE:
		{
			switch(cursor_mea_angle)
			{
				default:
				{
					cursor_mea_angle--;
					if(cursor_mea_angle==0) cursor_mea_angle=4;
				}break;
				case MEA_ANGLE_NONE:
				{
					if(ygrid_multiple_angle_index!=ygrid_multiple_angle_index_max-1)
					ygrid_multiple_angle_index++;
				}break;
			}
		
		}break;
		case MEA_TIME:
		{
			switch(cursor_mea_time)
			{
				default:
				{
					cursor_mea_time--;
					if(cursor_mea_time==0) cursor_mea_time=4;
				}break;
				case MEA_TIME_NONE:
				{
					printf("cle 1,0\xff\xff\xff");
					if(ygrid_multiple_time_index!=ygrid_multiple_time_index_max-1)
					ygrid_multiple_time_index++;
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			switch(cursor_query_journey)
			{
				default:
				{
					cursor_query_journey--;
					if(cursor_query_journey==0) cursor_query_journey=2;
				}break;
				case QUERY_JOURNEY_NONE:
				{
					if(ygrid_multiple_journey_index!=ygrid_multiple_journey_index_max-1)
					ygrid_multiple_journey_index++;
					
				}break;
			}
		}break;
		case QUERY_ANGLE:
		{
			switch(cursor_query_angle)
			{
				default:
				{
					cursor_query_angle--;
					if(cursor_query_angle==0) cursor_query_angle=2;
				}break;
				case QUERY_ANGLE_NONE:
				{
					if(ygrid_multiple_angle_index!=ygrid_multiple_angle_index_max-1)
					ygrid_multiple_angle_index++;
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			switch(cursor_query_time)
			{
				default:
				{
					
					cursor_query_time--;
					if(cursor_query_time==0) cursor_query_time=2;
				}break;
				case QUERY_TIME_NONE:
				{
					renew_screen_flag=1;
					printf("cle 1,0\xff\xff\xff");
					if(ygrid_multiple_time_index!=ygrid_multiple_time_index_max-1)
					ygrid_multiple_time_index++;
				}break;
			}
		}break;
		case SET_STEP:
		{
			sample_interval+=step;
			if(sample_interval>=600)sample_interval=600;
		}break;
					
	}
}

void down_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MAIN:
		{
			if(cursor_main==6) cursor_main=0;
			cursor_main++;
		}break;
		case MEA_JOURNEY:
		{
			switch(cursor_mea_journey)
			{
				default:
				{
					cursor_mea_journey++;
					if(cursor_mea_journey==5) cursor_mea_journey=1;
				}break;
				case MEA_JOURNEY_NONE:
				{
					if(ygrid_multiple_journey_index!=0)
					ygrid_multiple_journey_index--;
				}break;
			}
		}break;
		case MEA_ANGLE:
		{
			switch(cursor_mea_angle)
			{
				default:
				{
					cursor_mea_angle++;
					if(cursor_mea_angle==5) cursor_mea_angle=1;
				}break;
				case MEA_ANGLE_NONE:
				{
					if(ygrid_multiple_angle_index!=0)
					ygrid_multiple_angle_index--;
				}break;
			}
		
		}break;
		case MEA_TIME:
		{
			switch(cursor_mea_time)
			{
				default:
				{
					cursor_mea_time++;
					if(cursor_mea_time==5) cursor_mea_time=1;
				}break;
				case MEA_TIME_NONE:
				{
					printf("cle 1,0\xff\xff\xff");
					if(ygrid_multiple_time_index!=0)
					ygrid_multiple_time_index--;
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			switch(cursor_query_journey)
			{
				default:
				{
					cursor_query_journey++;
					if(cursor_query_journey==3) cursor_query_journey=1;
				}break;
				case QUERY_JOURNEY_NONE:
				{
					if(ygrid_multiple_journey_index!=0)
					ygrid_multiple_journey_index--;
				}break;
			}
		}break;
		case QUERY_ANGLE:
		{
			switch(cursor_query_angle)
			{
				default:
				{
					cursor_query_angle++;
					if(cursor_query_angle==3) cursor_query_angle=1;
				}break;
				case QUERY_ANGLE_NONE:
				{
					if(ygrid_multiple_angle_index!=0)
					ygrid_multiple_angle_index--;
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			switch(cursor_query_time)
			{
				default:
				{
					
					cursor_query_time++;
					if(cursor_query_time==3) cursor_query_time=1;
				}break;
				case QUERY_TIME_NONE:
				{
					renew_screen_flag=1;
					printf("cle 1,0\xff\xff\xff");
					if(ygrid_multiple_time_index!=0)
					ygrid_multiple_time_index--;
				}break;
			}
		}break;
		case SET_STEP:
		{
			if(sample_interval<=step) sample_interval=1;
			else sample_interval-=step;
		}break;
	}
}

void left_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MAIN:
		{
			if(cursor_main>3) cursor_main-=3;
			else cursor_main+=3;
		}break;
		case MEA_JOURNEY:
		{
			switch(cursor_mea_journey)
			{
				default:
				{
					if(cursor_mea_journey>2) cursor_mea_journey-=2;
					else cursor_mea_journey+=2;
				}break;
				case MEA_JOURNEY_NONE:
				{
					if(xgrid_multiple_journey_index!=0)
					xgrid_multiple_journey_index--;
					
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			switch(cursor_query_journey)
			{
				default:
				{
				
				}break;
				case QUERY_JOURNEY_NONE:
				{
					if(xgrid_multiple_journey_index!=0)
					xgrid_multiple_journey_index--;
					if(x_offset_journey<=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index])
						x_offset_journey=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index];
//					x_offset_journey=0;
				}break;
			}
		}break;
		case MEA_ANGLE:
		{
			switch(cursor_mea_angle)
			{
				default:
				{
					if(cursor_mea_angle>2) cursor_mea_angle-=2;
					else cursor_mea_angle+=2;
				}break;
				case MEA_ANGLE_NONE:
				{
					if(xgrid_multiple_angle_index!=0)
					xgrid_multiple_angle_index--;
				}break;
			}
		}break;
		case QUERY_ANGLE:
		{
			switch(cursor_query_angle)
			{
				default:
				{
	
				}break;
				case QUERY_ANGLE_NONE:
				{
					if(xgrid_multiple_angle_index!=0)
					xgrid_multiple_angle_index--;
				}break;
			}
		}break;
		case MEA_TIME:
		{
			switch(cursor_mea_time)
			{
				default:
				{
					if(cursor_mea_time>2) cursor_mea_time-=2;
					else cursor_mea_time+=2;
				}break;
				case MEA_ANGLE_NONE:
				{
				
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			switch(cursor_query_time)
			{
				default:break;
				case QUERY_TIME_NONE:
				{
					renew_screen_flag=1;
					if(xgrid_multiple_time_index!=0)
					xgrid_multiple_time_index--;
				}break;
			}
		}break;	
		case SET_STEP:
		{
			switch(step)
			{
				case _10s:
				{
					step=_01s;
				}break;
				case _01s:
				{
					step=_1s;
				}break;
				case _1s:
				{
					step=_10s;
				}break;
			}
		}break;
	}
	
}

void right_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MAIN:
		{
			if(cursor_main>3) cursor_main-=3;
			else cursor_main+=3;
		}break;
		case MEA_JOURNEY:
		{
			switch(cursor_mea_journey)
			{
				default:
				{
					if(cursor_mea_journey>2) cursor_mea_journey-=2;
					else cursor_mea_journey+=2;
				}break;
				case MEA_JOURNEY_NONE:
				{
					if(xgrid_multiple_journey_index!=xgrid_multiple_journey_index_max-1)
					xgrid_multiple_journey_index++;
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			switch(cursor_query_journey)
			{
				default:
				{
					
				}break;
				case QUERY_JOURNEY_NONE:
				{
					if(xgrid_multiple_journey_index!=xgrid_multiple_journey_index_max-1)
					xgrid_multiple_journey_index++;
//					x_offset_journey=0;
				}break;
			}
		}break;
		case MEA_ANGLE:
		{
			switch(cursor_mea_angle)
			{
				default:
				{
					if(cursor_mea_angle>2) cursor_mea_angle-=2;
					else cursor_mea_angle+=2;
				}break;
				case MEA_ANGLE_NONE:
				{
					if(xgrid_multiple_angle_index!=xgrid_multiple_angle_index_max-1)
					xgrid_multiple_angle_index++;
				}break;
			}
		
		}break;
		case QUERY_ANGLE:
		{
			switch(cursor_query_angle)
			{
				default:
				{
					
				}break;
				case QUERY_ANGLE_NONE:
				{
					if(xgrid_multiple_angle_index!=xgrid_multiple_angle_index_max-1)
					xgrid_multiple_angle_index++;
				}break;
			}
		
		}break;
		case MEA_TIME:
		{
			switch(cursor_mea_time)
			{
				default:
				{
					if(cursor_mea_time>2) cursor_mea_time-=2;
					else cursor_mea_time+=2;
				}break;
				case MEA_TIME_NONE:
				{
				
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			switch(cursor_query_time)
			{
				default:break;
				case QUERY_TIME_NONE:
				{
					renew_screen_flag=1;
					if(xgrid_multiple_time_index!=xgrid_multiple_time_index_max-1)
					xgrid_multiple_time_index++;
				}break;
			}
		}break;			
		case SET_STEP:
		{
			switch(step)
			{
				case _10s:
				{
					step=_1s;
				}break;
				case _01s:
				{
					step=_10s;
				}break;
				case _1s:
				{
					step=_01s;
				}break;
			}
		}break;
	}
}

void confirm_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MAIN:
		{
			renew_screen_flag=1;
			switch(cursor_main)
			{
				case MAIN_MEA_JOURNEY:
				{
					page=MEA_JOURNEY;
					cursor_mea_journey=MEA_JOURNEY_NONE;
					printf("page mea_journey\xff\xff\xff");
					HAL_ADC_Start(&hadc_lightstrength);
					adc_value=HAL_ADC_GetValue(&hadc_lightstrength);
					printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*(adc_value-32768))*1000);
				}break;
				case MAIN_MEA_ANGLE:
				{
					page=MEA_ANGLE;
					cursor_mea_angle=MEA_ANGLE_NONE;
					printf("page mea_angle\xff\xff\xff");
					HAL_ADC_Start(&hadc_lightstrength);
					adc_value=HAL_ADC_GetValue(&hadc_lightstrength);	
					printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*(adc_value-32768))*1000);
				}break;
				case MAIN_MEA_TIME:
				{
					page=SET_STEP;
					printf("page set_step\xff\xff\xff");
				}break;
				case MAIN_QUERY_JOURNEY:
				{
					page=QUERY_JOURNEY;
					cursor_query_journey=QUERY_JOURNEY_NONE;
					printf("page query_journey\xff\xff\xff");
					
				}break;
				case MAIN_QUERY_ANGLE:
				{
					page=QUERY_ANGLE;
					cursor_query_angle=QUERY_ANGLE_NONE;
					printf("page query_angle\xff\xff\xff");
				}break;
				case MAIN_QUERY_TIME:
				{
					page=QUERY_TIME;
					cursor_query_time=QUERY_TIME_NONE;
					printf("page query_time\xff\xff\xff");
					renew_screen_time();
				}break;
			}
		}break;
		case MEA_JOURNEY:
		{
			switch(cursor_mea_journey)
			{
				default:break;
				case MEA_JOURNEY_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
					measure_journey_pause();
					mea_state=MEA_STOP;
				}break;
				case MEA_JOURNEY_DATA_CLEAR:
				{
					journey_data_clear();
				}break;
				case MEA_JOURNEY_START:
				{
					switch(mea_state)
					{
						case MEA_STOP:
						{
							measure_journey_start();
						}break;
						case MEA_START:
						{
							measure_journey_pause();
						}break;
						case MEA_PAUSE:
						{
							measure_journey_continue();
						}break;
					}
					
				}break;
				case MEA_JOURNEY_SET_ZERO:
				{
					HAL_ADC_Start(&hadc_lightstrength);
					adc_value_setzero=HAL_ADC_GetValue(&hadc_lightstrength)-65536/6;	
					printf("vol.txt=\"0μW\"\xff\xff\xff");
				}break;
			}
		}break;
		case MEA_ANGLE:
		{
			switch(cursor_mea_angle)
			{
				default:break;
				case MEA_ANGLE_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
					measure_angle_pause();
					mea_state=MEA_STOP;
				}break;
				case MEA_ANGLE_DATA_CLEAR:
				{
					angle_data_clear();
				}break;
				case MEA_ANGLE_START:
				{
					switch(mea_state)
					{
						case MEA_STOP:
						{
							measure_angle_start();
						}break;
						case MEA_START:
						{
							measure_angle_pause();
						}break;
						case MEA_PAUSE:
						{
							measure_angle_continue();
						}break;
					}
					
				}break;
				case MEA_ANGLE_SET_ZERO:
				{
					HAL_ADC_Start(&hadc_lightstrength);
					adc_value_setzero=HAL_ADC_GetValue(&hadc_lightstrength)-65536/6;	
					printf("vol.txt=\"0μW\"\xff\xff\xff");
				}break;
			}
		}break;
		case MEA_TIME:
		{
			switch(cursor_mea_time)
			{
				default:break;
				case MEA_TIME_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
					measure_time_pause();
					mea_state=MEA_STOP;
				}break;
				case MEA_TIME_DATA_CLEAR:
				{
					time_data_clear();
				}break;
				case MEA_TIME_START:
				{
					switch(mea_state)
					{
						case MEA_STOP:
						{
							measure_time_start();
						}break;
						case MEA_START:
						{
							measure_time_pause();
						}break;
						case MEA_PAUSE:
						{
							measure_time_continue();
						}break;
					}
					
				}break;
				case MEA_TIME_SET_ZERO:
				{
					HAL_ADC_Start(&hadc_lightstrength);
					adc_value_setzero=HAL_ADC_GetValue(&hadc_lightstrength)-65536/6;	
					printf("vol.txt=\"0μW\"\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			switch(cursor_query_journey)
			{
				default:break;
				case QUERY_JOURNEY_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
				}break;
				case QUERY_JOURNEY_DATA_OUPUT:
				{
					printf("page outputing\xff\xff\xff");
					page=OUTPUTING;
					output_flag=0;
					//__disable_irq();
					printf("output_state.txt=\"initing..\"\xff\xff\xff");
					ch376_init();
					if(init_flag==1)
					{
						printf("output_state.txt=\"writing..\"\xff\xff\xff");
				//	printf("progress.val=50\xff\xff\xff");
						ch376_writetest();
					}
					//CH376_SetBaudRate(115200);
					HAL_Delay(10);
				//	printf("progress.val=100\xff\xff\xff");
					printf("page outputok\xff\xff\xff");
					page=OUTPUT_OK;
					if(output_flag) printf("output_result.txt=\"导出完成!\"\xff\xff\xff");
					else printf("output_result.txt=\"导出失败!\"\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_ANGLE:
		{
			switch(cursor_query_angle)
			{
				default:break;
				case QUERY_ANGLE_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
				}break;
				case QUERY_ANGLE_DATA_OUPUT:
				{
					printf("page outputing\xff\xff\xff");
					page=OUTPUTING;
					output_flag=0;
					//__disable_irq();
					printf("output_state.txt=\"initing..\"\xff\xff\xff");
					ch376_init();
				//	CH376_SetBaudRate(921600);
					if(init_flag==1)
					{
						printf("output_state.txt=\"writing..\"\xff\xff\xff");
					//printf("progress.val=50\xff\xff\xff");
						ch376_writetest_angle();
				//	printf("progress.val=100\xff\xff\xff");
					}
					HAL_Delay(10);
					printf("page outputok\xff\xff\xff");
					page=OUTPUT_OK;
					if(output_flag) printf("output_result.txt=\"导出完成!\"\xff\xff\xff");
					else printf("output_result.txt=\"导出失败!\"\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			switch(cursor_query_time)
			{
				default:break;
				case QUERY_TIME_EXIT:
				{
					page=MAIN;
					printf("page main\xff\xff\xff");
				}break;
				case QUERY_TIME_DATA_OUPUT:
				{
					printf("page outputing\xff\xff\xff");
					page=OUTPUTING;
					output_flag=0;
					//__disable_irq();
					printf("output_state.txt=\"initing..\"\xff\xff\xff");
					ch376_init();
				//	CH376_SetBaudRate(921600);
					if(init_flag==1)
					{
						printf("output_state.txt=\"writing..\"\xff\xff\xff");
				//	printf("progress.val=50\xff\xff\xff");
						ch376_writetest_time();
					}
					
				//	printf("progress.val=100\xff\xff\xff");
					HAL_Delay(10);
					printf("page outputok\xff\xff\xff");
					page=OUTPUT_OK;
					if(output_flag) printf("output_result.txt=\"导出完成!\"\xff\xff\xff");
					else printf("output_result.txt=\"导出失败!\"\xff\xff\xff");
				}break;
			}
		}break;
		case SET_STEP:
		{
			page=MEA_TIME;
			cursor_mea_time=MEA_TIME_NONE;
			printf("page mea_time\xff\xff\xff");
			renew_screen_time();
		}break;			
	}
}

void cancel_button()
{
	button_called=1;
	switch(page)
	{
		default:break;
		case OUTPUT_OK:
		{
			page=MAIN;
			printf("page main\xff\xff\xff");
		}break;
		case MEA_JOURNEY:
		{
			cursor_mea_journey=!cursor_mea_journey;
		}break;
		case MEA_ANGLE:
		{
			cursor_mea_angle=!cursor_mea_angle;
		}break;
		case MEA_TIME:
		{
			cursor_mea_time=!cursor_mea_time;
		}break;
		case QUERY_JOURNEY:
		{
			cursor_query_journey=!cursor_query_journey;
		}break;
		case QUERY_ANGLE:
		{
			cursor_query_angle=!cursor_query_angle;
		}break;
		case QUERY_TIME:
		{
			cursor_query_time=!cursor_query_time;
		}break;
	}
}

void fun_button()
{
	if(page==QUERY_JOURNEY|page==QUERY_ANGLE|page==QUERY_TIME)
	{
		switch(x_offset_move)
		{
			case 1:
				x_offset_move=10;
				break;
			case 10:
				x_offset_move=100;
				break;
			case 100:
				x_offset_move=1;
				break;
		}
	}
}

//刷新当前页面的菜单栏目
void renew_menu()
{
	switch(page)
	{
		default:break;
		case MAIN:
		{
			printf("mea_journey1.bco=50779\xff\xff\xff");
		//	printf("mea_journey2.bco=50779\xff\xff\xff");
			printf("mea_angle1.bco=50779\xff\xff\xff");
		//	printf("mea_angle2.bco=50779\xff\xff\xff");
			printf("mea_time1.bco=50779\xff\xff\xff");
		//	printf("mea_time2.bco=50779\xff\xff\xff");
			printf("query_journey.bco=50779\xff\xff\xff");
			printf("query_angle.bco=50779\xff\xff\xff");
			printf("query_time.bco=50779\xff\xff\xff");
			switch(cursor_main)
			{
				case MAIN_MEA_JOURNEY:
				{
					printf("mea_journey1.bco=61277\xff\xff\xff");
				//	printf("mea_journey2.bco=61277\xff\xff\xff");
				}break;
				case MAIN_MEA_ANGLE:
				{
					printf("mea_angle1.bco=61277\xff\xff\xff");
		//			printf("mea_angle2.bco=61277\xff\xff\xff");
				}break;
				case MAIN_MEA_TIME:
				{
					printf("mea_time1.bco=61277\xff\xff\xff");
			//		printf("mea_time2.bco=61277\xff\xff\xff");
				}break;
				case MAIN_QUERY_JOURNEY:
				{
					printf("query_journey.bco=61277\xff\xff\xff");
				}break;
				case MAIN_QUERY_ANGLE:
				{
					printf("query_angle.bco=61277\xff\xff\xff");
				}break;
				case MAIN_QUERY_TIME:
				{
					printf("query_time.bco=61277\xff\xff\xff");
				}break;
			}
		}break;
		case MEA_JOURNEY:
		{
			printf("set_zero1.bco=50779\xff\xff\xff");
		//	printf("set_zero2.bco=50779\xff\xff\xff");
			printf("data_clear.bco=50779\xff\xff\xff");
			printf("start.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			switch(cursor_mea_journey)
			{
				default:break;
				case MEA_JOURNEY_SET_ZERO:
				{
					printf("set_zero1.bco=61277\xff\xff\xff");
		//			printf("set_zero2.bco=61277\xff\xff\xff");
				}break;
				case MEA_JOURNEY_DATA_CLEAR:
				{
					printf("data_clear.bco=61277\xff\xff\xff");
				}break;
				case MEA_JOURNEY_START:
				{
					printf("start.bco=61277\xff\xff\xff");
				}break;
				case MEA_JOURNEY_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;	
		case MEA_ANGLE:
		{
			printf("set_zero1.bco=50779\xff\xff\xff");
			printf("data_clear.bco=50779\xff\xff\xff");
			printf("start.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			switch(cursor_mea_angle)
			{
				default:break;
				case MEA_ANGLE_SET_ZERO:
				{
					printf("set_zero1.bco=61277\xff\xff\xff");
		//			printf("set_zero2.bco=61277\xff\xff\xff");
				}break;
				case MEA_ANGLE_DATA_CLEAR:
				{
					printf("data_clear.bco=61277\xff\xff\xff");
				}break;
				case MEA_ANGLE_START:
				{
					printf("start.bco=61277\xff\xff\xff");
				}break;
				case MEA_ANGLE_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;	
		case MEA_TIME:
		{
			printf("set_zero1.bco=50779\xff\xff\xff");
			printf("data_clear.bco=50779\xff\xff\xff");
			printf("start.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			switch(cursor_mea_time)
			{
				default:break;
				case MEA_TIME_SET_ZERO:
				{
					printf("set_zero1.bco=61277\xff\xff\xff");
	//				printf("set_zero2.bco=61277\xff\xff\xff");
				}break;
				case MEA_TIME_DATA_CLEAR:
				{
					printf("data_clear.bco=61277\xff\xff\xff");
				}break;
				case MEA_TIME_START:
				{
					printf("start.bco=61277\xff\xff\xff");
				}break;
				case MEA_TIME_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_JOURNEY:
		{
			printf("out1.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			printf("mul.txt=\"X%d\"\xff\xff\xff",x_offset_move);
			switch(cursor_query_journey)
			{
				default:break;
				case QUERY_JOURNEY_DATA_OUPUT:
				{
					printf("out1.bco=61277\xff\xff\xff");
		//			printf("out2.bco=61277\xff\xff\xff");
				}break;
				case QUERY_JOURNEY_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;		
		case SET_STEP:
		{
			printf("time.txt=\"%.1fs\"\xff\xff\xff",sample_interval/10.0);
			switch(step)
			{
				case _10s:
				{
					printf("move step,489,180,489,180,0,0\xff\xff\xff");
				}break;
				case _1s:
				{
					printf("move step,509,180,509,180,0,0\xff\xff\xff");
				}break;
				case _01s:
				{
					printf("move step,534,180,534,180,0,0\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_ANGLE:
		{
			printf("out1.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			printf("mul.txt=\"X%d\"\xff\xff\xff",x_offset_move);
			switch(cursor_query_angle)
			{
				default:break;
				case QUERY_ANGLE_DATA_OUPUT:
				{
					printf("out1.bco=61277\xff\xff\xff");
		//			printf("out2.bco=61277\xff\xff\xff");
				}break;
				case QUERY_ANGLE_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;
		case QUERY_TIME:
		{
			printf("out1.bco=50779\xff\xff\xff");
			printf("exit.bco=50779\xff\xff\xff");
			printf("mul.txt=\"X%d\"\xff\xff\xff",x_offset_move);
			switch(cursor_query_time)
			{
				default:break;
				case QUERY_TIME_DATA_OUPUT:
				{
					printf("out1.bco=61277\xff\xff\xff");
		//			printf("out2.bco=61277\xff\xff\xff");
				}break;
				case QUERY_TIME_EXIT:
				{
					printf("exit.bco=61277\xff\xff\xff");
				}break;
			}
		}break;
	}
}
