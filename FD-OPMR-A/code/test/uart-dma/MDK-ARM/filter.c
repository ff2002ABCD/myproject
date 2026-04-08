#include "main.h"
#include "filter.h"

double Last_filter;			//上次滤波值
double DB_filter;			//上次滤波值db

void Filter_Init(void){
	Last_filter = -1;
	DB_filter = -1;
}


// 一阶滤波算法
double First_Filter(double ad){
	double Now_filter;
	if(Last_filter >= 0){
		Now_filter = coefficient * ad + (1.0 - coefficient) * Last_filter;
	}else{
		Now_filter = ad;
	}
	Last_filter = Now_filter;
	return Now_filter;
}

// 对数滤波算法
double log_Filter(double ad){
	double Now_filter;

	if(DB_filter >= 0){
		if(ad < 0.005){
			ad = 0.005;
		}
		if(DB_filter - ad >= 0.008){
			Now_filter = ad;
		}else{
			if(ad < 0.01){
				Now_filter = 0.01 * ad + 0.99 * DB_filter;
			}
			
			if(ad >= 0.01 && ad < 0.02){
				Now_filter = 0.02 * ad + 0.98 * DB_filter;
			}
			
			if(ad >= 0.02 && ad < 0.05){
				Now_filter = 0.05 * ad + 0.95 * DB_filter;
			}
			
			if(ad >= 0.05 && ad < 0.1){
				Now_filter = 0.1 * ad + 0.9 * DB_filter;
			}
			
			if(ad >= 0.1 && ad < 0.15){
				Now_filter = 0.2 * ad + 0.8 * DB_filter;
			}
			
			if(ad >= 0.15){
				Now_filter = 0.5 * ad + 0.5 * DB_filter;
			}
		}
	}else{
		Now_filter = ad;
	}
	DB_filter = Now_filter;
	
	return Now_filter;
}

// 去最大最小取平均数算法
double avg_Filter(double ad[] , int num){
	double avg_ad;
	double max_ad;
	double min_ad;
	int temp_i;
	
	avg_ad = 0;
	max_ad = ad[0];
	min_ad = ad[0];
	
	for(temp_i = 0;temp_i < num;temp_i++){
		avg_ad = avg_ad + ad[temp_i];
		if(max_ad < ad[temp_i]){
			max_ad = ad[temp_i];
		}
		
		if(min_ad > ad[temp_i]){
			min_ad = ad[temp_i];
		}
	}
	
	avg_ad = (avg_ad - min_ad - max_ad) / (num - 2);
	
	return avg_ad;
}

// 去最大最小取平均数算法
double avg_Filter_int(int ad[] , int num){
	double avg_ad;
	double max_ad;
	double min_ad;
	int temp_i;
	
	avg_ad = 0;
	max_ad = ad[0];
	min_ad = ad[0];
	
	for(temp_i = 0;temp_i < num;temp_i++){
		avg_ad = avg_ad + ad[temp_i];
		if(max_ad < ad[temp_i]){
			max_ad = ad[temp_i];
		}
		
		if(min_ad > ad[temp_i]){
			min_ad = ad[temp_i];
		}
	}
	
	avg_ad = (avg_ad - min_ad - max_ad) / (num - 2);
	
	return avg_ad;
}	
