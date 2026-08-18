#include "encoder.h"
#include "main.h"
#include "tim.h"
#include "menu.h"
#include "stdio.h"
#include "function.h"
/* 确保 GPIOB / GPIO_PIN_x 等定义可见给静态分析器 */
#include "stm32f1xx_hal.h"

extern int fputc(int ch, FILE* file);
uint16_t Count=10000,last_Count=10000;
uint16_t Diretion=0;
/* 计数差分法所需的上次计数值 */
static uint16_t lastCnt = 0;

void encoder_init()
{
	HAL_TIM_Encoder_Start(&htim_encoder,TIM_CHANNEL_ALL);
	__HAL_TIM_SetCounter(&htim_encoder,30000);
	/* 初始化 lastCnt 为当前计数，避免启动瞬时误判 */
	lastCnt = __HAL_TIM_GET_COUNTER(&htim_encoder);
}

void get_encoder()
{
	/* 计数差分法：读取定时器计数，计算带符号差值处理方向与步数。
	   适用于较高速旋转且能正确处理多步跳变。 */
	{
		uint16_t cnt = __HAL_TIM_GET_COUNTER(&htim_encoder);
		int16_t delta = (int16_t)(cnt - lastCnt); /* 自动处理溢出方向 */
		if (delta != 0) {
			/* 对于一次性大步（快速旋转）可能产生较大 delta，限制单次处理的最大步数以免长时间阻塞 */
			int16_t steps = (delta > 0) ? delta : -delta;
			if (steps > 20) steps = 20;
			if (delta > 0) {
				for (int i = 0; i < steps; i++) {
					clockwise();
				}
			} else {
				for (int i = 0; i < steps; i++) {
					counter_clockwise();
				}
			}
			lastCnt = cnt;
		}
	}
}
void clockwise(void) {
	right_button();
}
void counter_clockwise()
{
	left_button();
}
