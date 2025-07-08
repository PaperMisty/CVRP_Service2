clc,clear
sj0=load('sj.txt');       %加载100个目标的数据
x=sj0(:,1:2:8); x=x(:);
y=sj0(:,2:2:8); y=y(:);
sj=[x y]; d1=[70,40]; 
sj=[d1;sj;d1]; sj=sj*pi/180;  %单位化成弧度
d=zeros(102); %距离矩阵d的初始值
for i=1:101
  for j=i+1:102
  d(i,j)=6370*acos(cos(sj(i,1)-sj(j,1))*cos(sj(i,2))*cos(sj(j,2))+sin(sj(i,2))*sin(sj(j,2)));
  end
end
d=d+d';
rand('state',sum(clock)); %初始化随机数发生器
for k=1:w  %通过改良圈算法选取初始种群
    c=randperm(100); %产生1，...，100的一个全排列  
    c1=[1,c+1,102]; %生成初始解
    for t=1:102 %该层循环是修改圈 
        flag=0; %修改圈退出标志
    for m=1:100
      for n=m+2:101
        if d(c1(m),c1(n))+d(c1(m+1),c1(n+1))<d(c1(m),c1(m+1))+d(c1(n),c1(n+1))
           c1(m+1:n)=c1(n:-1:m+1);  flag=1; %修改圈
        end
      end
    end
   if flag==0
      J(k,c1)=1:102; break %记录下较好的解并退出当前层循环
   end
   end
end


% 计算路径长度
long = zeros(1, length(J));
for j=1:length(J)
    for i=1:101
        long(j)=long(j)+d(J(j,i),J(j,i+1)); %计算每条路径长度
    end
end
% 最优路径
[slong,ind2]=sort(long); %对路径长度按照从小到大排序
J=J(ind2(1),:); %精选前w个较短的路径对应的染色体

plot(x,y,'o'); hold on;
for i=1:length(J)
    plot(sj(J(i,:),1),sj(J(i,:),2),'-')
end
