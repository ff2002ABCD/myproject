#ifndef __KEY_H
#define __KEY_H
#include "main.h"


#define KEYUP 	HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_9)
#define KEYDOWN  HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_8)
#define KEYCONFIRM   HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_7)
#define KEYCANCEL  HAL_GPIO_ReadPin(GPIOC,GPIO_PIN_6)
#define KEYFUN   HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_6)

#define Key  (KEYUP && KEYDOWN && KEYCONFIRM && KEYCANCEL && KEYFUN)

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
    KEY_UP,
    KEY_DOWN,
    KEY_CONFIRM,
		KEY_CANCEL,
		KEY_FUN
}KEY_VALUE;

typedef enum 
{
    NULL_KEY = 0,
    SHORT_KEY =1,
    LONG_KEY
}KEY_TYPE;
extern KEY_STATE KeyState;

//extern u8 g_KeyFlag;
//extern KEY_TYPE g_KeyActionFlag; 

//#define SingleKeyEvent
extern _Bool flag_10s;
#define SingleKey_LongShort_Event	1
void Key_Init(void);
void Key_Scan(void);
void do_key();
extern uint16_t Count,last_Count;
extern uint16_t Diretion;
void get_encoder();

#endif