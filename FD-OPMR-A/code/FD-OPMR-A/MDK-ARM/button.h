/**
  * ????????Key_Scan()??,?????2ms,
  * ???????10ms,?????switch case???????10ms
  * ???10ms?????????
  */
#ifndef __BUTTON_H
#define __BUTTON_H
#include "main.h"


#define KEYUP 	HAL_GPIO_ReadPin(UP_GPIO_Port,UP_Pin)
#define KEYDOWN  HAL_GPIO_ReadPin(DOWN_GPIO_Port,DOWN_Pin)
#define KEYLEFT   HAL_GPIO_ReadPin(LEFT_GPIO_Port,LEFT_Pin)
#define KEYRIGHT   HAL_GPIO_ReadPin(RIGHT_GPIO_Port,RIGHT_Pin)
#define KEYCONFIRM   HAL_GPIO_ReadPin(CONFIRM_GPIO_Port,CONFIRM_Pin)
#define KEYCANCEL   HAL_GPIO_ReadPin(CANCEL_GPIO_Port,CANCEL_Pin)
#define KEYFUN     HAL_GPIO_ReadPin(FUN_GPIO_Port,FUN_Pin)

#define Key  (KEYUP && KEYDOWN && KEYLEFT && KEYRIGHT &&KEYCONFIRM && KEYCANCEL &&KEYFUN)

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
    KEY_LEFT,
		KEY_RIGHT,
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

extern KEY_TYPE g_KeyActionFlag;
extern uint16_t long_counter;
#define SingleKey_LongShort_Event	1
void Key_Init(void);
void Key_Scan(void);
void do_key();

#endif

