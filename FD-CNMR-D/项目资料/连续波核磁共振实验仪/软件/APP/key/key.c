#include "main.h"

/*******************************************************************************
* 函 数 名         : KEY_Init
* 函数功能		   : 按键初始化
* 输    入         : 无
* 输    出         : 无
*******************************************************************************/
void KEY_Init(void)
{
	GPIO_InitTypeDef GPIO_InitStructure; //定义结构体变量	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB,ENABLE);
	
	GPIO_InitStructure.GPIO_Pin=KEY_UP_Pin|KEY_DOWN_Pin|KEY_QD_Pin|KEY_FH_Pin;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;	//上拉输入
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
}

/*******************************************************************************
* 函 数 名         : KEY_Scan
* 函数功能		   : 按键扫描检测
* 输    入         : mode=0:单次按下按键
					 mode=1：连续按下按键
* 输    出         : 0：未有按键按下
					 KEY_UP：K_UP键按下
					 KEY_DOWN：K_DOWN键按下
					 KEY_LEFT：K_LEFT键按下
					 KEY_RIGHT：K_RIGHT键按下
*******************************************************************************/


u8 KEY_Scan(void){
	u8 key;
	key = key_data.key_number;
	if(key != 0){
		key_data.key_cishu++;
		key_data.key_number = 0;
	}
	return key;
}
//按键扫描

void ReadKeyPort(void){
	if(K_UP==0){
		key_data.key_number_t2 = KEY_UP;
		key_data.key = 11;
	}
	if(K_DOWN==0){
		key_data.key_number_t2 = KEY_DOWN;
		key_data.key = 12;
	}
//	if(K_LEFT==0){
//		key_data.key_number_t2 = KEY_LEFT;
//		key_data.key = 13;
//	}
//	if(K_RIGHT==0){
//		key_data.key_number_t2 = KEY_RIGHT;
//		key_data.key = 14;
//	}
	if(K_QD==0){
		key_data.key_number_t2 = KEY_QD;
		key_data.key = 15;
	}
	if(K_FH==0){
		key_data.key_number_t2 = KEY_FH;
		key_data.key = 16;
	}
	
	if(K_UP==1 && K_DOWN==1 && K_QD==1 && K_FH==1){//无按键按下
		key_data.key_number_t1 = 0;
		key_data.key_number_t2 = 0;
		key_data.key_time = 0;
		key_data.key_cishu = 0;
		key_data.key_long = 0;
		key_data.key = 0;
	}
	
	if(key_data.key_number_t2 == key_data.key_number_t1){
		key_data.key_time++;
		if(key_data.key_time == 3 && key_data.key_cishu == 0){//30ms确定按下
			key_data.key_number = key_data.key_number_t1;
		}
		
		if(key_data.key_time == 53 && key_data.key_long == 0 && speed_up >= 1){//500ms确定长按
			key_data.key_long = 1;
			key_data.key_time = 0;
		}
		
		if(key_data.key_time == 20 && key_data.key_long == 1){
			key_data.key_number = key_data.key_number_t1;
			key_data.key_time = 0;
			if(key_data.key_cishu >= 10 && speed_up >= 2){//二阶加速
				key_data.key_long = 2;
			}
		}
		
		if(key_data.key_time == 4 && key_data.key_long == 2){
			key_data.key_number = key_data.key_number_t1;
			key_data.key_time = 0;
			if(key_data.key_cishu >= 100){//三阶加速
				key_data.key_long = 3;
			}
		}
		
		if(key_data.key_time == 1 && key_data.key_long == 3){
			key_data.key_number = key_data.key_number_t1;
			key_data.key_time = 0;
		}
	}else{
		key_data.key_number_t1 = key_data.key_number_t2;
		key_data.key_time = 0;
	}
}
