#ifndef __KEY_H
#define __KEY_H
#include "main.h"


#define KEY0 	HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_12)
#define KEY1  HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_9)
#define KEY2   HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_10)

#define Key  (KEY0 && KEY1 && KEY2)

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
}KEY_VALUE;

typedef enum 
{
    NULL_KEY = 0,
    SHORT_KEY =1,
    LONG_KEY
}KEY_TYPE;
extern KEY_STATE KeyState;


#define SingleKey_LongShort_Event	1
void Key_Init(void);
void Key_Scan(void);
void do_key();

#endif