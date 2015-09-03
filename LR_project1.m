%Author:  Xuanli He, Lingjuan Lyu, Hao Duan
%Version: 1.2

%read training set
train=load('train_instance.txt');
%read test set
test=load('test_instance.txt');
% feed logistic regression
b = glmfit(train(:,1:4),train(:,5),'binomial');  % logistic regression
% predict test
p = glmval(b,test(:,1:4),'logit');     % get fitted probabilities for scores
  
      
