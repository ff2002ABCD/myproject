#ifndef __KEY_H
#define __KEY_H
#include "main.h"
#include "stm32f1xx_hal.h"
#include <stdint.h>


#define KEYUP 	HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_1)
#define KEYDOWN  HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_4)
#define KEYCONFIRM   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_0)
#define KEYCANCEL  HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_7)
#define KEYRIGHT  HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_5)
#define KEYLEFT  HAL_GPIO_ReadPin(GPIOA,GPIO_PIN_6)
#define KEYFUN   HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_5)  // 添加编码器按键PB5
#define Key  (KEYUP && KEYDOWN && KEYCONFIRM && KEYCANCEL && KEYLEFT && KEYRIGHT && KEYFUN)

typedef enum
{
    KEY_CHECK = 0,
    KEY_COMFIRM = 1,
    KEY_RELEASE = 2,
}KEY_STATE;

//按键值定义
typedef enum
{
    KEY_NULL = 0,
    KEY_UP,
    KEY_DOWN,
    KEY_CONFIRM,
	KEY_CANCEL,
   	KEY_RIGHT,
	KEY_LEFT,
    KEY_FUN      // 添加编码器按键
}KEY_VALUE;

typedef enum 
{
    NULL_KEY = 0,
    SHORT_KEY =1,
    LONG_KEY
}KEY_TYPE;
extern KEY_STATE KeyState;

//extern u8 g_KeyFlag;
extern KEY_TYPE g_KeyActionFlag; 

//#define SingleKeyEvent
extern _Bool flag_10s;
#define SingleKey_LongShort_Event	1
void Key_Init(void);
void Key_Scan(void);
void do_key(void);
void Current_control(void);
extern uint16_t Count,last_Count;
extern uint16_t Diretion;

// 添加编码器按键处理函数声明
void fun_button(void);

#endif
