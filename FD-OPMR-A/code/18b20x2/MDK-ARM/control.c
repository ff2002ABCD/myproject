#include "main.h"
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
#include "measure.h"
#include "menu.h"

//void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
//{		

//	//按钮——左
//	if(GPIO_Pin==GPIO_PIN_3)
//	{
//		//delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_RESET)
//		{
//			delay_ms(500);
//			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					left_button();
//					if(button_counter<15) {delay_ms(130);button_counter++;}
//					if(button_counter>=10) {delay_ms(30);}
//					
//				}
//				button_counter=0;
//			}
//			else
//			{
//				//printf("duanan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				printf("duan\xFF\xFF\xFF");
//			//delay_ms(50);
//			//for(int i=0;i<200;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				left_button();
//			}
//		}
//	}
//	//按钮——右
//	if(GPIO_Pin==GPIO_PIN_4)
//	{
//		//delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
//		{
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					right_button();
//					if(button_counter==0){delay_ms(500);button_counter++;}
//					if(button_counter<15&&button_counter>0) {delay_ms(130);button_counter++;}
//					if(button_counter>=15) {delay_ms(30);}
//					
//					
//				}
//				button_counter=0;
//		}
//	}
//	//按钮——确认
//	if(GPIO_Pin==GPIO_PIN_5)
//	{
//		//delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)==GPIO_PIN_RESET)
//		{
//			delay_ms(1000);
//			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				cancel_button();
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					//left_button();
//					//cursor_button();
//					
//					if(button_counter<10) {delay_ms(200);;button_counter++;}
//					if(button_counter>=10) {delay_ms(50);}
//				}
//				button_counter=0;
//			}
//			else
//			{	
//				//printf("duanan\r\n");
//			//	left_button();
//			//	cursor_button();
//			//	menu2_button();
//				confirm_button();
//			}
//		}
//	}
//	//按钮——下
//	if(GPIO_Pin==GPIO_PIN_2)
//	{
//	//	delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_2)==GPIO_PIN_RESET)
//		{
//			delay_ms(500);
//			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_2)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_2)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					down_button();
//					if(button_counter<10) {delay_ms(200);button_counter++;}
//					if(button_counter>=4) {delay_ms(50);}
//				}
//				button_counter=0;
//			}
//			else
//			{
//				//printf("duanan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				printf("duan\xFF\xFF\xFF");
//			//delay_ms(50);
//			//for(int i=0;i<200;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				down_button();
//			}
//		}
//	}
//	//上
//	if(GPIO_Pin==GPIO_PIN_1)
//	{
//	//	delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//		{
//			delay_ms(500);
//			if(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				
//				while(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					up_button();
//					if(button_counter<10) {delay_ms(200);button_counter++;}
//					if(button_counter>=4) {delay_ms(50);}
//				}
//				button_counter=0;
//			}
//			else
//			{
//				//printf("duanan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				printf("duan\xFF\xFF\xFF");
//			//delay_ms(50);
//			//for(int i=0;i<200;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				up_button();
//			}
//		}
//	}
//	//菜单——切换
//	if(GPIO_Pin==GPIO_PIN_6)
//	{
//		//delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_RESET)
//		{
//			delay_ms(1000);
//			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_RESET)
//				{
//					//printf("changan\xFF\xFF\xFF");
//					//left_button();
//					//cursor_button();
//					
//					if(button_counter<10) {delay_ms(200);;button_counter++;}
//					if(button_counter>=10) {delay_ms(50);}
//				}
//				button_counter=0;
//			}
//			else
//			{	
//				//printf("duanan\r\n");
//			//	left_button();
//			//	cursor_button();
//			//	menu2_button();
//				menu2_button();
//			}
//		}
//	}
//	//菜单——按钮
//	if(GPIO_Pin==GPIO_PIN_12)
//	{
//		delay_ms(5);
//		if(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//		{
//			delay_ms(500);
//			if(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//			{
//				//printf("changan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				printf("changan\xFF\xFF\xFF");
//				menu_status=0;
//				printf("t0.txt=\"通道\"\xFF\xFF\xFF");
//				printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
//				if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
//				printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
//				printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
//				printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
//				printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
//				printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
//				printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
//				while(HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)==GPIO_PIN_RESET)
//				{
//				
//				}
//				
//			}
//			else
//			{
//				//printf("duanan\r\n");
//				//for(int i=0;i<300;i++) printf("\x01\xff\xff\xff");//确保透传结束
//				printf("duan\xFF\xFF\xFF");
//				switch(menu_status)
//				{
//					//待机
//					case 0:
//					{
//						menu_status=1;
//						printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
//					}break;
//					//通道
//					case 1:
//					{
//						menu_status+=8;
//						printf("t0.txt=\"->通道\"\xFF\xFF\xFF");
//					}break;
//					//时间档位
//					case 2:
//					{
//						menu_status+=8;
//						printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");
//						if(fft_enable==1) printf("t2.txt=\"->频率档位\"\xFF\xFF\xFF");
//					}break;
//					//垂直档位
//					case 3:
//					{
//						menu_status+=8;
//						printf("t4.txt=\"->垂直档位\"\xFF\xFF\xFF");
//					}break;
//					//水平偏移
//					case 4:
//					{
//						menu_status+=8;
//						printf("t6.txt=\"->水平偏移\"\xFF\xFF\xFF");
//					}break;
//					//垂直偏移
//					case 5:
//					{
//						menu_status+=8;
//						printf("t8.txt=\"->垂直偏移\"\xFF\xFF\xFF");
//					}break;
//					//触发阈值
//					case 6:
//					{
//						menu_status+=8;
//						printf("t10.txt=\"->触发阈值\"\xFF\xFF\xFF");
//					}break;
//					//耦合方式
//					case 7:
//					{
//						menu_status+=8;
//						printf("t12.txt=\"->耦合方式\"\xFF\xFF\xFF");
//					}break;
//					//触发类型
//					case 8:
//					{
//						menu_status+=8;
//						printf("t14.txt=\"->触发类型\"\xFF\xFF\xFF");
//					}break;
//					//通道
//					case 9:
//					{
//						menu_status-=8;
//						printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
//					}break;
//					//时间档位
//					case 10:
//					{
//						menu_status-=8;
//						printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
//					}break;
//					//垂直档位
//					case 11:
//					{
//						menu_status-=8;
//						printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
//					}break;
//					//水平偏移
//					case 12:
//					{
//						menu_status-=8;
//						printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
//					}break;
//					//垂直偏移
//					case 13:
//					{
//						menu_status-=8;
//						printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
//					}break;
//					//触发阈值
//					case 14:
//					{
//						menu_status-=8;
//						printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
//					}break;
//					//耦合方式
//					case 15:
//					{
//						menu_status-=8;
//						printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
//					}break;
//					//触发类型
//					case 16:
//					{
//						menu_status-=8;
//						printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
//					}break;
//				}
//			}
//		}
//	}
//	//曲线————逆时针
//	else if(GPIO_Pin==GPIO_PIN_8)
//	{
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_9)==GPIO_PIN_SET&&HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_8)==GPIO_PIN_RESET)
//		{
//			//for(int i=0;i<700;i++) printf("\x01\xff\xff\xff");//确保透传结束
//			printf("nishizheng\xFF\xFF\xFF");
//			switch(cursor_status)
//			{
//				case 3:
//				{
//					if(hengzong==0)
//						{
//							if(cursor_num==0&&y1>0)
//							{
//								//printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
//								printf("move t18,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
//								printf("move t20,0,%d,0,%d,0,30\xFF\xFF\xFF",y1,y1-step);
//								y1-=step;
//							}
//							else if(cursor_num==1&&y2>0)
//							{
//								//printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
//								printf("move t19,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
//								printf("move t21,0,%d,0,%d,0,30\xFF\xFF\xFF",y2,y2-step);
//								y2-=step;
//							}
//						}
//						else
//						{
//							if(cursor_num==0&&x1>0)
//							{
//								//printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
//								printf("move t16,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
//								printf("move t22,%d,0,%d,0,0,30\xFF\xFF\xFF",x1,x1-step);
//								x1-=step;
//							}
//							else if(cursor_num==1&&x2>0)
//							{
//								//printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
//								printf("move t17,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
//								printf("move t23,%d,0,%d,0,0,30\xFF\xFF\xFF",x2,x2-step);
//								x2-=step;
//							}
//						}
//				}break;
//			}
//		}
//	}
//	//菜单2-按钮
//	else if(GPIO_Pin==GPIO_PIN_13)
//	{
//		delay_ms(20);
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
//		{
//			delay_ms(500);
//			if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
//			{
//				//changan
//				
//				while(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)==GPIO_PIN_RESET)
//				{
//				
//				}
//				
//			}
//			else 
//			{
//			 //duanan
//				
//			}
//		}
//	}
//	
//	//菜单2-逆时针
//	else if(GPIO_Pin==GPIO_PIN_5)
//	{	
//		if(HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)==GPIO_PIN_SET&&HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)==GPIO_PIN_RESET) 
//		{
//			printf("nishizheng\xFF\xFF\xFF");
//			switch(menu2_status)
//			{
////				case 1:
////				{
////					menu2_status=5;
////				}break;
//				case 2:
//				{
//					menu2_status--;
//					printf("t44.txt=\"->校准模式\"\xff\xff\xff");
//					if(xy_enable==0)
//					printf("t45.txt=\"Y-T\"\xff\xff\xff");
//					else printf("t45.txt=\"X-Y\"\xff\xff\xff");
//				}break;
//				case 3:
//				{
//					menu2_status--;
//					if(xy_enable==0)
//					printf("t45.txt=\"->Y-T\"\xff\xff\xff");
//					else printf("t45.txt=\"->X-Y\"\xff\xff\xff");
//					switch(Trigger_ANS)
//					{
//						case 0:
//						{
//							printf("t46.txt=\"AUTO\"\xff\xff\xff");
//						}break;
//						case 1:
//						{
//							printf("t46.txt=\"NORMAL\"\xff\xff\xff");
//						}break;
//						case 2:
//						{
//							printf("t46.txt=\"SINGLE\"\xff\xff\xff");
//						}break;
//					}
//				}break;
//				case 4:
//				{
//					menu2_status--;
//					switch(Trigger_ANS)
//					{
//						case 0:
//						{
//							printf("t46.txt=\"->AUTO\"\xff\xff\xff");
//						}break;
//						case 1:
//						{
//							printf("t46.txt=\"->NORMAL\"\xff\xff\xff");
//						}break;
//						case 2:
//						{
//							printf("t46.txt=\"->SINGLE\"\xff\xff\xff");
//						}break;
//					}
//					if(fft_enable==1)
//					{
//						printf("t49.txt=\"FFT开\"\xff\xff\xff");
//					}
//					else printf("t49.txt=\"FFT关\"\xff\xff\xff");
//				}break;
//			case 5:
//				{
//					menu2_status--;
//					if(fft_enable==1)
//					{
//						printf("t49.txt=\"->FFT开\"\xff\xff\xff");
//					}
//					else printf("t49.txt=\"->FFT关\"\xff\xff\xff");
////					if(get_freq_enable==1) printf("t50.txt=\"测频开\"\xff\xff\xff");
////					else printf("t50.txt=\"测频关\"\xff\xff\xff");
//				}break;
//				case 6:
//				{
//					menu2_status--;
////					if(get_freq_enable==1) printf("t50.txt=\"->测频开\"\xff\xff\xff");
////					else printf("t50.txt=\"->测频关\"\xff\xff\xff");
//					printf("t57.txt=\"切换参数\"\xff\xff\xff");
//				}break;
//			}
//		
//		}
//	}
////	switch(cursor_status)
////	{
////		case 0:
////		{
////			printf("vis t16,0\xFF\xFF\xFF");
////			printf("vis t17,0\xFF\xFF\xFF");
////			printf("vis t18,0\xFF\xFF\xFF");
////			printf("vis t19,0\xFF\xFF\xFF");
////			printf("vis t20,0\xFF\xFF\xFF");
////			printf("vis t21,0\xFF\xFF\xFF");
////			printf("vis t22,0\xFF\xFF\xFF");
////			printf("vis t23,0\xFF\xFF\xFF");
////			printf("vis t24,0\xFF\xFF\xFF");
////		}break;
////		case 1:
////		{
////			printf("vis t16,1\xFF\xFF\xFF");
////			printf("vis t17,1\xFF\xFF\xFF");
////			printf("vis t18,1\xFF\xFF\xFF");
////			printf("vis t19,1\xFF\xFF\xFF");
////			printf("vis t20,1\xFF\xFF\xFF");
////			printf("vis t21,1\xFF\xFF\xFF");
////			printf("vis t22,1\xFF\xFF\xFF");
////			printf("vis t23,1\xFF\xFF\xFF");
////			printf("vis t24,1\xFF\xFF\xFF");
////			if(hengzong==0) printf("t24.txt=\"选横纵：横\"\xFF\xFF\xFF");
////			else printf("t24.txt=\"选横纵：纵\"\xFF\xFF\xFF");
////		}break;
////		case 2:
////		{
////			printf("vis t16,1\xFF\xFF\xFF");
////			printf("vis t17,1\xFF\xFF\xFF");
////			printf("vis t18,1\xFF\xFF\xFF");
////			printf("vis t19,1\xFF\xFF\xFF");
////			printf("vis t20,1\xFF\xFF\xFF");
////			printf("vis t21,1\xFF\xFF\xFF");
////			printf("vis t22,1\xFF\xFF\xFF");
////			printf("vis t23,1\xFF\xFF\xFF");
////			printf("vis t24,1\xFF\xFF\xFF");
////			if(cursor_num==0)
////			{
////				printf("t24.txt=\"选通道：1\"\xFF\xFF\xFF");
////			}
////			else
////			{
////				printf("t24.txt=\"选通道：2\"\xFF\xFF\xFF");
////			}
////		}break;
////		case 3:
////		{
////			printf("vis t16,1\xFF\xFF\xFF");
////			printf("vis t17,1\xFF\xFF\xFF");
////			printf("vis t18,1\xFF\xFF\xFF");
////			printf("vis t19,1\xFF\xFF\xFF");
////			printf("vis t20,1\xFF\xFF\xFF");
////			printf("vis t21,1\xFF\xFF\xFF");
////			printf("vis t22,1\xFF\xFF\xFF");
////			printf("vis t23,1\xFF\xFF\xFF");
////			printf("vis t24,1\xFF\xFF\xFF");
////			if(hengzong==0)
////			{
////				if(cursor_num==0)
////				{
////					printf("t24.txt=\"选中：横1\"\xFF\xFF\xFF");
////				}
////				else if(cursor_num==1)
////				{
////					printf("t24.txt=\"选中：横2\"\xFF\xFF\xFF");
////				}
////			}
////			else
////			{
////				if(cursor_num==0)
////				{
////					printf("t24.txt=\"选中：纵1\"\xFF\xFF\xFF");
////				}
////				else if(cursor_num==1)
////				{
////					printf("t24.txt=\"选中：纵2\"\xFF\xFF\xFF");
////				}
////			}
////		}break;
////		
////	}
////	//刷新菜单2
////	printf("vis t44,1\xFF\xFF\xFF");
////	printf("vis t45,1\xFF\xFF\xFF");
////	printf("vis t46,1\xFF\xFF\xFF");
////	printf("vis t49,1\xFF\xFF\xFF");
////	printf("vis t50,1\xFF\xFF\xFF");
////	printf("vis t57,1\xFF\xFF\xFF");
////	
////	}
////	//刷新菜单1
////	printf("t0.txt=\"通道\"\xFF\xFF\xFF");
////	printf("t2.txt=\"时间档位\"\xFF\xFF\xFF");
////	if(fft_enable==1) printf("t2.txt=\"频率档位\"\xFF\xFF\xFF");
////	printf("t4.txt=\"垂直档位\"\xFF\xFF\xFF");
////	printf("t6.txt=\"水平偏移\"\xFF\xFF\xFF");
////	printf("t8.txt=\"垂直偏移\"\xFF\xFF\xFF");
////	printf("t10.txt=\"触发阈值\"\xFF\xFF\xFF");
////	printf("t12.txt=\"耦合方式\"\xFF\xFF\xFF");
////	printf("t14.txt=\"触发类型\"\xFF\xFF\xFF");
////	switch(menu_status)
////	{
////		case 1:
////		{
////			printf("t0.txt=\"*通道\"\xFF\xFF\xFF");
////		}break;
////		case 2:
////		{
////			printf("t2.txt=\"*时间档位\"\xFF\xFF\xFF");
////			if(fft_enable==1) printf("t2.txt=\"*频率档位\"\xFF\xFF\xFF");
////		}break;
////		case 3:
////		{
////			printf("t4.txt=\"*垂直档位\"\xFF\xFF\xFF");
////		}break;
////		case 4:
////		{
////			printf("t6.txt=\"*水平偏移\"\xFF\xFF\xFF");
////		}break;
////		case 5:
////		{
////			printf("t8.txt=\"*垂直偏移\"\xFF\xFF\xFF");
////		}break;
////		case 6:
////		{
////			printf("t10.txt=\"*触发阈值\"\xFF\xFF\xFF");
////		}break;
////		case 7:
////		{
////			printf("t12.txt=\"*耦合方式\"\xFF\xFF\xFF");
////		}break;
////		case 8:
////		{
////			printf("t14.txt=\"*触发类型\"\xFF\xFF\xFF");
////		}break;
////		case 9:
////		{
////			printf("t0.txt=\"->通道\"\xFF\xFF\xFF");
////		}break;
////		case 10:
////		{
////			printf("t2.txt=\"->时间档位\"\xFF\xFF\xFF");
////			if(fft_enable==1) printf("t2.txt=\"->频率档位\"\xFF\xFF\xFF");
////		}break;
////		case 11:
////		{
////			printf("t4.txt=\"->垂直档位\"\xFF\xFF\xFF");
////		}break;
////		case 12:
////		{
////			printf("t6.txt=\"->水平偏移\"\xFF\xFF\xFF");
////		}break;
////		case 13:
////		{
////			printf("t8.txt=\"->垂直偏移\"\xFF\xFF\xFF");
////		}break;
////		case 14:
////		{
////			printf("t10.txt=\"->触发阈值\"\xFF\xFF\xFF");
////		}break;
////		case 15:
////		{
////			printf("t12.txt=\"->耦合方式\"\xFF\xFF\xFF");
////		}break;
////		case 16:
////		{
////			printf("t14.txt=\"->触发类型\"\xFF\xFF\xFF");
////		}break;
////	}

	
//	 __HAL_GPIO_EXTI_CLEAR_IT(GPIO_Pin);
//	
//}

