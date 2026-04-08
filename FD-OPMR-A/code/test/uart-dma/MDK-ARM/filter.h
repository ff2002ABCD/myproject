#ifndef _filter_H
#define _filter_H

#define coefficient   0.01               // 滤波系数coefficient（0-1） 

extern double Last_filter;			//上次滤波值
extern double DB_filter;			//上次滤波值db

void Filter_Init(void);
double First_Filter(double ad);		// 一阶滤波算法

double log_Filter(double ad);		// 对数滤波算法

double avg_Filter(double ad[] , int num);		// 去最大最小取平均数算法

double avg_Filter_int(int ad[] , int num);		// 去最大最小取平均数算法


#endif
