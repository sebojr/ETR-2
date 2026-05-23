# =========================================================
# SOCIAL MEDIA SENTIMENT ANALYSIS PIPELINE
# TRANSLATED CONTENT ONLY VERSION
# =========================================================

library(tidyverse)
library(tidytext)
library(caret)
library(textdata)
library(tm)
library(text2vec)
library(randomForest)
library(syuzhet)

# =========================================================
# 1. LOAD DATA
# =========================================================
setwd("D:/OneDrive/Documents/ETR 2")
getwd()
df <- read.csv("Translated_RobinPadilla_Dataset.csv")

glimpse(df)

# =========================================================
# 2. USE ONLY TRANSLATED CONTENT
# =========================================================

df_clean <- df |>
  
  # Keep only needed metadata + TRANSLATED TEXT
  select(
    Query_Topic,
    Translated_Content,
    Subreddit,
    Score,
    Num_Comments
  ) |>
  
  na.omit() |>
  
  # MAIN TEXT SOURCE = TRANSLATED ONLY
  mutate(Text = tolower(Translated_Content)) |>
  
  mutate(Text = gsub("http\\S+", "", Text)) |>
  mutate(Text = gsub("[^[:alnum:] ]", "", Text)) |>
  mutate(Text = gsub("\\s+", " ", Text)) |>
  mutate(Text = trimws(Text)) |>
  
  filter(Text != "")

# =========================================================
# 3. SENTIMENT ANALYSIS (ON TRANSLATED TEXT)
# =========================================================

scores <- get_sentiment(df_clean$Text)

df_clean$sentiment <- case_when(
  scores > 0 ~ "positive",
  scores < 0 ~ "negative",
  TRUE ~ "neutral"
)

df_clean$sentiment <- as.factor(df_clean$sentiment)

table(df_clean$sentiment)

# =========================================================
# 4. TEXT ANALYSIS (TRANSLATED ONLY)
# =========================================================

tokens <- df_clean |>
  unnest_tokens(word, Text)

tokens <- tokens |>
  anti_join(stop_words, by = "word")

word_freq <- tokens |>
  count(word, sort = TRUE)

print(head(word_freq, 20))

# =========================================================
# 5. FEATURE ENGINEERING (OPTIONAL TEXT INSIGHT)
# =========================================================

tfidf <- tokens |>
  count(sentiment, word, sort = TRUE) |>
  bind_tf_idf(word, sentiment, n)

print(head(tfidf, 20))

# =========================================================
# 6. TRAIN / TEST SPLIT
# =========================================================

set.seed(123)

train_index <- createDataPartition(
  df_clean$sentiment,
  p = 0.8,
  list = FALSE
)

train <- df_clean[train_index, ]
test <- df_clean[-train_index, ]

# =========================================================
# 7. MODEL (ENGAGEMENT + SENTIMENT LABEL)
# =========================================================

model <- randomForest(
  sentiment ~ Score + Num_Comments,
  data = train,
  ntree = 200
)

print(model)

# =========================================================
# 8. PREDICTION
# =========================================================

pred <- predict(model, test)

confusionMatrix(pred, test$sentiment)

# =========================================================
# 9. VISUALIZATION
# =========================================================

ggplot(df_clean, aes(x = sentiment)) +
  geom_bar(fill = "steelblue") +
  ggtitle("Sentiment Distribution (Translated Content Only)") +
  xlab("Sentiment") +
  ylab("Count")

top_words <- word_freq |>
  slice_max(n, n = 10)

ggplot(top_words, aes(x = reorder(word, n), y = n)) +
  geom_col() +
  coord_flip() +
  ggtitle("Top Words (Translated Content Only)") +
  xlab("Words") +
  ylab("Frequency")

# =========================================================
# 10. EXPORT
# =========================================================

write.csv(
  df_clean,
  "translated_only_sentiment_dataset.csv",
  row.names = FALSE
)

cat("\n============================\n")
cat("TRANSLATED CONTENT ANALYSIS COMPLETED\n")
cat("============================\n")
cat("Rows:", nrow(df_clean), "\n")
cat("Sentiment Summary:\n")
print(table(df_clean$sentiment))
