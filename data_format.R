#Author   : Lingjun Lyu, Xuanli He, Hao Duan
#Version  : 1.2
#Filename : data_format.R
PATH <- "data/train_instance.csv"
TEST <- "data/test_instances.csv"
# read raw data file
raw_data <- read.table(PATH,sep=",")
test_data <- read.table(TEST,sep=",")
#print(colnames(raw_data))
colnames(raw_data) <- c("from", "to",
                        "from_outedges", "from_inedges", 
                        "to_outedges", "to_inedges", 
                        "common",
                        "cosine", "jaccard",
                        "jaccard_mute", "adar",
                        "pref_attach","kn1",
                        "class")

colnames(test_data) <- c("from", "to",
                        "from_outedges", "from_inedges", 
                        "to_outedges", "to_inedges", 
                        "common",
                        "cosine", "jaccard",
                        "jaccard_mute", "adar",
                        "pref_attach","kn1")


n <- nrow(raw_data)
# shuffle the order of instances
raw_data <- raw_data[sample(n,n),]

# select four features from data
train_reduced <- data.frame(common=raw_data$common, adar=raw_data$adar,
                            kn1=raw_data$kn1, jaccard_mute=raw_data$jaccard_mute,
                            class=raw_data$class)
test_reduced <- data.frame(common=test_data$common, adar=test_data$adar,
                            kn1=test_data$kn1,jaccard_mute=test_data$jaccard_mute)

# train common normalization
common <- train_reduced$common
mu <- mean(common)
sigma <- sd(common-mu)
print(paste("common mu", mu))
print(paste("common sd", sigma))
common_norm <- (common-mu) / sigma
train_reduced$common <- common_norm

# test common normalization
common <- test_reduced$common
test_reduced$common <- (common-mu) / sigma

# train adar normalization
adar <- train_reduced$adar
mu <- mean(adar)
sigma <- sd(adar-mu)
print(paste("adar mu", mu))
print(paste("adar sd", sigma))
adar_norm <- (adar-mu) / sigma
train_reduced$adar <- adar_norm

# test adar normalization
adar <- test_reduced$adar
test_reduced$adar <- (adar-mu) / sigma

write.csv(train_reduced,
          file="data/complexity/train_instance.csv",row.names=F)
write.csv(test_reduced,
          file="data/complexity/test_instance.csv",row.names=F)

# dump instances with 11 features
write.table(raw_data[,3:ncol(raw_data)], "data/train_formmatted_data.csv", sep=",", row.names=F)
write.table(test_data[,3:ncol(test_data)], "data/test_formmatted_data.csv", sep=",", row.names=F)

# run randomforest
library("randomForest")
set.seed(415)
# feed random forest
fit <- randomForest(as.factor(class) ~ common+adar+kn1+jaccard_mute,
                    data=train_reduced, importance=T, ntree=500)
# predict test data
prediction <- predict(fit,test_reduced,type="prob")

# dump result to disk
submit <- data.frame(Id=c(nrow(Prediction)), Prediction=prediction)
write.csv(submit, file="randomForest.csv", row.names=F)
