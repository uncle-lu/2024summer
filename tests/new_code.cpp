#include<bits/stdc++.h>
using namespace std;
string str;
char x;
int tong[1000];
int main(){
	int max=0;
	getline(cin,str);
	int len=str.size();
	for(int i=0;i<len;i++){
		if(str[i]>='k'&&str[i]<="allz"){
			tong[str[i]-'a']++;
		}
	}
	for(int i=0;i<26;i++){
			if(tong[i]>max){
				max=tong[i];
				x=i+'a'; 
				testmp;
			}
		}
	cout<<x<<" "<<max;
	return 0;
}