#include "stdint.h"	// uint16_t 定义
#include "gui.h"	// gui绘制
#include "lcd.h"	// 颜色定义
#include "main.h"	// 按键定义 LED定义 中断引脚定义
#include "adc.h"	// 
#include "tim.h"
#include "osc.h"


/*
	author：Haozi
	
	Author URI：https://blog.csdn.net/weixin_46253745
	
	Describe：获取ADC的值，并利用GUI进行显示
*/


/* 全局变量 */
uint8_t oscState 		= 	0;		// 0:未就绪	1:运行中 在主函数初始化中改变

/* 波形显示相关		arr:一个格子的时间长度；enlarge调整高度；offset波形左右移动距离 */
uint16_t numF 			=	3;	 	// 第几个等级触发频率
uint32_t ARR			= 	0;		// ADC触发频率，（72M / 36）/ ARR
uint8_t enlarge			=	1;		// 波形放大倍数，默认是1的时候，屏幕刚好显示 0-4095
int8_t offset			=	0;		// 波形偏移量 用于左右移动波形

/* 被测信号的原始数据 */
uint16_t originalAdc[900];			// ADC采集的DMA传输过来的原始数据
uint16_t numOfCollect 	=	640;	// 采样数量

/* 用于计算被测信号的频率 */
uint16_t adcThreshold	=	1024;	// 标记被测信号起始位置的阈值
uint16_t startPosition	=	0;		// 标记被测信号一个周期的起始位置
uint16_t endPosition	=	0;		// 标记被测信号一个周期的结束位置（也是下一个周期的开始）
uint16_t waveFrequency	=	0;		// 被测信号的频率

/* 经过换算用于显示的数据（这里必须用有符号的，否则在限幅的时候会出问题） */
int16_t newWave[600] 	= 	{0};	// 新获取的波形数据
int16_t oldWave[600] 	= 	{0};	// 上一次显示的波形数据

/* 被测信号电压信息 */
float maxVol			=	0;		// 被测信号 最大电压
float minVol			=	0;		// 被测信号 最小电压
float difVoMaxAndMin	=	0;		// 被测信号 最大电压与最小电压的差

/* 按键监测 */
uint8_t keyNum 			=	0;		// 此时选中的按键。0：调整放大倍数； 1：调整时间长度； 2：调整左右偏移
uint8_t keyChanged		=	1;		// 按键状态，是否被按下过。如果按下过，部分内容需要重新刷新显示。

/* 增加 / 减少 */
#define INCREASE 1
#define REDUCE 0

/* 临时存储需要显示内容，无实际意义 */
uint8_t tempBuf[10];


/* ===================================================== */
// 描述：设置示波器每个格子显示的时间长度（其实就是 设置ADC触发频率 / ADC的重装载值）
// 参数：arr：定时器重装载值
//			LCD把屏幕 宽度 320分为了16个格子，每个格子就是20个点。
//			以 ARR = 200举例，定时器频率 72M / 36 = 2M。
//			则 每0.1ms 产生一次中断。20个点就需要 2ms。
//		 	也就是说 一个格子的时常是 2ms。
//		 	其他数值 计算同理。
// 		 实际上，如果算上采样周期的画，每次采样需要7.5个ADC时钟周期，ADC时钟周期为12Mhz，
//		 采集20个点需要的时间为：20 * 7.5 * 1000 / 12M = 0.0125ms 
//		 太小了，所以这里忽略不计。
// 返回值：
/* ===================================================== */
void setAdcFrequency(uint8_t t)
{
    switch(t)
    {
        case 1: // 50us
            ARR = 5;
            break;

        case 2: // 0.1ms
            ARR = 10;
            break;

        case 3: // 0.2ms
            ARR = 20;
            break;

        case 4: // 0.5ms
            ARR = 50;
            break;

        case 5: // 1ms
            ARR = 100;
            break;

        case 6: // 2ms
            ARR = 200;
            break;

        case 7: // 5ms
            ARR = 500;
            break;

        case 8: // 10ms
            ARR = 1000;
            break;

        case 9: // 20ms
            ARR = 2000;
            break;
    }
	
    TIM3->ARR = ARR - 1;
}

/* ===================================================== */
// 描述：调整波形幅值放大系数
// 参数：inc：INCREASE 或 REDUCE；是要增加 enlarge 还是减少 enlarge；
//		调整时，同步的，波形的起始阈值 adcThreshold 也要调整，
//		需要放大enlarge时，意味着波形数值比较小，因此也阈值也要调小才能监测到。
// 返回值：
/* ===================================================== */
void setWaveEnlarge(uint8_t inc)
{
    if(enlarge < 4 && inc)
    {
        enlarge *= 2;
    }

    if(enlarge > 1 && !inc)
    {
        enlarge /= 2;
    }

    switch(enlarge)
    {
        case 1:
            adcThreshold = 1500;
            break;

        case 2:
            adcThreshold = 512;
            break;

        case 4:
            adcThreshold = 128;
            break;
    }
}

/* ===================================================== */
// 描述：偏移量设置
// 参数：inc：INCREASE 或 REDUCE；是要 offset 还是减少 offset；
// 返回值：
/* ===================================================== */
void setWaveOffset(uint8_t inc)
{
    uint8_t i = 0;
	
	// 最多左右移动100个数
    if(offset < 100 && offset > -100)
    {
        if(inc)offset++;
        else offset--;
    }
    else
    {
        if(offset == 100)
        {
            offset--;
        }
        else
        {
            offset++;
        }
    }

	// 执行这个函数 还需要再次按下
    while(HAL_GPIO_ReadPin(KEY0_GPIO_Port, KEY0_Pin) == RESET || HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == RESET)
    {
        for(; i < 4; ++i)
        {
			// 超时没动作就退出
            if(HAL_GPIO_ReadPin(KEY0_GPIO_Port, KEY0_Pin) == SET && HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == SET)
            {
                return;
            }
            HAL_Delay(50);
        }

        if(offset < 100 && offset > -100)
        {
            if(inc)offset++;
            else offset--;

            HAL_Delay(20);
            keyChanged = 1;
        }
        else
        {
            return;
        }
    }
}

/* ===================================================== */
// 描述：示波器初始化
// 参数：
// 返回值：
/* ===================================================== */
void OSC_Init(void)
{
	// 初始化 示波器 背景设置
	setBackGroundColor();	// 设置背景颜色
	setBackGroundText();	// 设置背景静态文字
	
	// 1. adc校准
    HAL_ADCEx_Calibration_Start(&hadc1);
	// 2. 开启DMA传输
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)&originalAdc, numOfCollect);
	// 3. 关掉传输一半中断
    __HAL_DMA_DISABLE_IT((&hadc1)->DMA_Handle, DMA_IT_HT);
	// 4. 设置ADC采样频率。并开始计时采样
    setAdcFrequency(numF);
    HAL_TIM_Base_Start(&htim3);
}

/* ===================================================== */
// 描述：DMA传输回调函数，用于绘制获取的ADC波形并输出提示信息。
// 参数：
// 返回值：
// 注意：在绘制期间，会关闭定时器，停止触发ADC。
// 		可以看出，这里的逻辑是，
//		1. 打开定时器计时，定时器开始计数，可以触发中断；
//		2. 定时器触发中断，ADC获取连续的一段电压值；（在这里频率是可以设置的）
//		3. 关闭定时器计数，ADC停止转换；
//		4. 绘制刚刚获取的ADC波形，绘制完成之后，再次打开定时器。
// 		
//		简单来说，其实电压值并不是在连续转换。而是转换一段 停一会 再次转换一段。
/* ===================================================== */
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
	// 失能定时器3
    HAL_TIM_Base_MspDeInit(&htim3);

    if(oscState == 1)
    {
        // HAL_GPIO_TogglePin(LED0_GPIO_Port, LED0_Pin);
        drawStringWithColor(240, 1, 120, "Running ", YELLOW);
		/*
			显示所有需要的内容
			1. 绘制背景网格
			2. 计算被测波形的频率；
			3. 将波形显示在屏幕上；
			4. 更新波形信息
		*/
		
		// 执行过程中 让LED亮
		HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);
		
		drawNetwork();
		updateWaveFrequency();
		OSC_ShowWave();
		OSC_ShowInfo();
		
		// 刷新完成之后 灭掉LED
		HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
    }
    else
    {
        drawStringWithColor(240, 1, 120, "Stopping", RED);
    }
	
	// 使能定时器3
    HAL_TIM_Base_MspInit(&htim3);
}

/* ===================================================== */
// 描述：从一个上升沿开始计算获取的波形的频率。
//		 对于杂乱的信号，这里其实算的并不准确。
// 参数：
// 返回值：
/* ===================================================== */
void updateWaveFrequency(void)
{
    static uint16_t n = 0;

	// 寻找原始数据中第一个 adcThreshold 附近的点
	// adcThreshold 
    for(n = 100; n < numOfCollect; n++)
    {
        if(originalAdc[n] < adcThreshold && originalAdc[n + 2] > adcThreshold)
        {
            if(n > (numOfCollect - lcddev.width))
            {
                startPosition = 100;
            }
            else
            {
                startPosition = n;
            }
            break;
        }
    }
	// 寻找原始数据中第二个 adcThreshold 附近的点
    for(n = startPosition + 3; n < numOfCollect; n++)
    {
        if(originalAdc[n] < adcThreshold && originalAdc[n + 2] > adcThreshold)
        {
            endPosition = n;
            break;
        }
    }
	/*
		每采集一个点的时间间隔为：ARR / 2M s
		所以这两个点之间的时间间隔为：(endPosition - startPosition) * ARR / 2M s
		频率为：1 / ((endPosition - startPosition) * ARR / 2M)
				= 2M / ((endPosition - startPosition) * ARR)
				= adcFrequency / (endPosition - startPosition)
	*/
    waveFrequency = 2000000 / ((endPosition - startPosition) * ARR);
}

/* ===================================================== */
// 描述：计算上峰值电压、下峰值电压、两者之间的差值
// 参数：
// 返回值：
/* ===================================================== */
void updateDifVoMaxAndMin(void)
{
    uint16_t max = 0;
    uint16_t min = 4095;
    uint16_t n = 0;

    for(n = 1; n < lcddev.width; n++)
    {
        if(newWave[n] > max)
        {
            max = newWave[n];
        }
        if(newWave[n] < min)
        {
            min = newWave[n];
        }
    }
	maxVol = (float) max * (3.3 / 4096.0);
	minVol = (float) min * (3.3 / 4096.0);
    difVoMaxAndMin = maxVol - minVol;
}

/* ===================================================== */
// 描述：显示波形图
// 参数：
// 返回值：
/* ===================================================== */
void OSC_ShowWave(void)
{
	// 电压曲线中的点 在LCD上对应的 Y 坐标
    int16_t prePos = 0;		// 前一个点坐标
	int16_t afterPos = 0;	// 后一个点坐标
	
    static uint16_t n = 0;

	// 把原始ADC数据 放到 newWave 数组中（从我们算频率的地方截取）
    for(n = 0; n < lcddev.width; n++)
    {
        newWave[n] = originalAdc[offset + startPosition + n];
    }

	// 计算上峰值电压、下峰值电压、差值
    updateDifVoMaxAndMin();
	
	/*
		坐标转换公式：enlarge = 1 时，可以限制在 40 - 200 之间。
		enlarge = 1 时
			newWave[i] = 0 时；对应Y坐标为 200；
			newWave[i] = 4095 时；对应Y坐标为 200 - 4095 * 0.03907 = 40.00835 约等于40；
		enlarge = 2 时
			newWave[i] = 0 时；对应Y坐标为 200；
			newWave[i] = 4095 时；对应Y坐标为 200 - 4095 * 0.03907 * 2 = -119,9833 约等于 -120；
		enlarge = 4 时
			newWave[i] = 0 时；对应Y坐标为 200；
			newWave[i] = 4095 时；对应Y坐标为 200 - 4095 * 0.03907 * 4 = -439.9666 约等于 -440；
	*/
    newWave[0] = prePos = ((lcddev.height - 40) - (newWave[0] * 0.0397 * enlarge));

    for(n = 1; n < (lcddev.width - 2); n++)
    {
        newWave[n] = afterPos = (lcddev.height - 40) - ((double)(newWave[n] * 0.0397 * enlarge));
		// 如果调整了放大倍数，需要限幅(20 - 220之间)
//        if(afterPos >= 220)	// 这里貌似也不用其实
//        {
//            newWave[n] = afterPos = 219;
//        }
        if(afterPos <= 20)	// 限制顶端
        {
            newWave[n] = afterPos = 21;
        }
	
        drawLineWithColor(n, oldWave[n], n + 1, oldWave[n + 1], BLACK);	// 清除上一时刻的线
        drawLineWithColor(n, prePos, n + 1, afterPos, YELLOW);			// 画上新的线
        
		prePos = afterPos; // 更新
    }

	// 全部画完之后，把现在的存到旧的里面去，用于下次画线的时候擦除。
    for(n = 1; n < lcddev.width; n++)
    {
        oldWave[n] = newWave[n - 1];
    }
}

/* ===================================================== */
// 描述：显示波形的信息
// 参数：
// 返回值：
/* ===================================================== */
void OSC_ShowInfo(void)
{
    static float temp = 0;

	/* LCD下面的信息 */
    // 显示最大电压
	sprintf((char*)tempBuf, "%.2f", maxVol);
	drawStringWithColor(32, 222, 32, tempBuf, GREEN);
	// 显示最小电压
	sprintf((char*)tempBuf, "%.2f", minVol);
	drawStringWithColor(112, 222, 32, tempBuf, GREEN);
	// 显示电压差
    sprintf((char*)tempBuf, "%.2f", difVoMaxAndMin);
    drawStringWithColor(200, 222, 32, tempBuf, GREEN);
	// 显示频率
    LCD_ShowNum(248, 222, waveFrequency, 5, 16);

	/* LCD上面的信息 */
    if(keyChanged == 1)
    {
		// 0:显示幅值
        sprintf((char*)tempBuf, "%dV ", 4 / enlarge);
		drawStringWithColor(5, 1, 50, tempBuf, YELLOW);
		
        // 1:显示每个格子对应的时常
        temp = ARR / 100.0;
        if(temp < 0.1)
        {
            sprintf((char*)tempBuf, " %dus ", ARR * 10);
        }
        else if(temp < 1.0)
        {
            sprintf((char*)tempBuf, " %.1fms ", temp);
        }
        else
        {
            sprintf((char*)tempBuf, " %dms  ", (uint8_t)temp);
        }
		drawStringWithColor(45, 1, 60, tempBuf, YELLOW);

        // 2:显示偏移
		drawStringWithColor(108, 2, 200, "[-----------]", YELLOW);

        if(keyNum == 2)
        {
            POINT_COLOR = WHITE;
        }
        LCD_ShowChar(155 + offset * 0.42, 2, '|', 16, 1);
        LCD_ShowChar(157 + offset * 0.42, 2, '|', 16, 1);


        // 显示选择
        if(keyNum == 0)
        {
            POINT_COLOR = WHITE;
			LCD_DrawRectangle(1, 1, 40, 17);
        }
        else
        {
            POINT_COLOR = BLACK;
            LCD_DrawRectangle(1, 1, 40, 17);
        }

        if(keyNum == 1)
        {
            POINT_COLOR = WHITE;
            LCD_DrawRectangle(45, 1, 95, 17);
        }
        else
        {
            POINT_COLOR = BLACK;
			LCD_DrawRectangle(45, 1, 95, 17);
        }
        keyChanged = 0;
    }
}

/* ======================= 下面的是按键相关，用于调整示波器参数 =================== */

/* ===================================================== */
// 描述：按键中断函数
// 参数：
// 返回值：
/* ===================================================== */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    uint8_t i = 0;
    HAL_Delay(20);

	// KEY_UP 按键按下
    if(GPIO_Pin == WK_UP_Pin)
    {
        if(HAL_GPIO_ReadPin(WK_UP_GPIO_Port, WK_UP_Pin) == SET)
        {
            for(; i < 11 && HAL_GPIO_ReadPin(WK_UP_GPIO_Port, WK_UP_Pin) == SET; ++i)
            {
                HAL_Delay(50);
            }
			// 如果持续500ms 一直是按下的，停止运行示波器。再次长按启动
            if(i == 11)
            {
                oscState = !oscState;
            }
            else
            {
				if(keyNum >= 3)
				{
					keyNum = 0;
				}
				else
				{
					keyNum++;
				}
            }
            keyChanged = 1;
        }
    }
    else if(GPIO_Pin == KEY0_Pin)
    {
        if(HAL_GPIO_ReadPin(KEY0_GPIO_Port, KEY0_Pin) == RESET)
        {
            if(keyNum == 0)
            {
                setWaveEnlarge(INCREASE);
            }
            else if(keyNum == 1 && 2 <= numF)
            {
				setAdcFrequency(--numF);
            }
            else if(keyNum == 2)
            {
				setWaveOffset(INCREASE);
            }
            keyChanged = 1;
        }
    }
    else if(GPIO_Pin == KEY1_Pin)
    {
        if(HAL_GPIO_ReadPin(KEY1_GPIO_Port, KEY1_Pin) == RESET)
        {
            if(keyNum == 0)
            {
                setWaveEnlarge(REDUCE);
            }
            else if(keyNum == 1 && numF <= 8)
            {
				setAdcFrequency(++numF);
            }
            else if(keyNum == 2)
            {
                setWaveOffset(REDUCE);
            }
            keyChanged = 1;
        }
    }
}




