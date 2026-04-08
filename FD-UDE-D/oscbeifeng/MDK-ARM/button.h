/**
  * ????????Key_Scan()??,?????2ms,
  * ???????10ms,?????switch case???????10ms
  * ???10ms?????????
  */
#ifndef __BUTTON_H
#define __BUTTON_H
#include "main.h"


#define KEY0 	HAL_GPIO_ReadPin(GPIOE,GPIO_PIN_1)
#define KEY1  HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_2)//????1
#define KEY2   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_3)//????2 
#define KEY3   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_4)
#define KEY4   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)
#define KEY5   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_6)

#define Key  (KEY0 && KEY1 && KEY2 && KEY3 &&KEY4 &&KEY5)

typedef enum
{
    KEY_CHECK = 0,
    KEY_COMFIRM = 1,
    KEY_RELEASE = 2,
}KEY_STATE;

//??????,
typedef enum
{
    KEY_NULL = 0,
    KEY_0,
    KEY_1,
    KEY_2,
		KEY_3,
		KEY_4,
		KEY_5
}KEY_VALUE;

typedef enum 
{
    NULL_KEY = 0,
    SHORT_KEY =1,
    LONG_KEY
}KEY_TYPE;


//extern u8 g_KeyFlag;
//extern KEY_TYPE g_KeyActionFlag; 

//??????
//#define SingleKeyEvent

//???????????
#define SingleKey_LongShort_Event	1
void Key_Init(void);
void Key_Scan(void);
void do_key();

#endif

