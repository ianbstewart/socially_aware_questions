#!/bin/bash
#SBATCH --job-name=clean_data
#SBATCH --mail-user=ianbstew@umich.edu
#SBATCH --mail-type=BEGIN,END
#SBATCH --time=1:00:00
#SBATCH --account=mihalcea1
#SBATCH --output=/home/%u/logs/%x-%j.log
#SBATCH --nodes=1
#SBATCH --partition=standard
#SBATCH --mem-per-cpu=1000m
#echo "starting to clean"

## NYT data
#DATA_DIR=../../data/NYT_scrape/
#DATA_NAME=NYT_full_long_input
#COMMENT_DIR=../../data/nyt_comments/
#COMMENT_MONTH_YEAR_PAIRS=('Jan_2018' 'Feb_2018' 'March_2018' 'April_2018')
#OUT_DIR=../../data/nyt_comments/full_data/
#AUTHOR_DATA=../../data/nyt_comments/author_comment_social_data.tsv
## CNN data
#DATA_FILE=../../data/CNN_articles/cnn/article_question_data.tsv
#DATA_NAME=CNN_long
#OUT_DIR=../../data/CNN_articles/cnn/
## reddit data
DATA_FILE=../../data/reddit_data/subreddit_submissions_2018-01_2019-12.gz
COMMENT_DATA=../../data/reddit_data/advice_subreddit_filter_comment_question_data.gz
# combined data
DATA_NAME=combined_data
OUT_DIR=../../data/reddit_data/
# text-only
#DATA_NAME=advice_subreddit
#OUT_DIR=../../data/reddit_data/
# reddit + author
AUTHOR_DATA=../../data/reddit_data/author_data/combined_author_prior_comment_data.gz # contains static and dynamic author data
# token author representation
#AUTHOR_DATA_TYPE=tokens
#OUT_DIR=../../data/reddit_data/authUr_text_data/
# embed author representation
#AUTHOR_DATA_TYPE=embeds
#OUT_DIR=../../data/reddit_data/author_text_data/author_embed_data/
MODEL_TYPE=bart
#MODEL_TYPE=longformer
# enforce named entity overlap between article and question (>=1 NE overlap per question/article)
#NE_overlap=False
#SAMPLE_PCT=1.0
SAMPLE_PCT=0.25
# NYT
#python clean_data_for_generation.py $OUT_DIR --data_dir $DATA_DIR --data_name $DATA_NAME --comment_dir $COMMENT_DIR --comment_month_year_pairs "${COMMENT_MONTH_YEAR_PAIRS[@]}" --author_data $AUTHOR_DATA --model_type $MODEL_TYPE --sample_pct $SAMPLE_PCT --NE_overlap $NE_overlap
# CNN
#python clean_data_for_generation.py $OUT_DIR --data_file $DATA_FILE --data_name $DATA_NAME --model_type $MODEL_TYPE --sample_pct $SAMPLE_PCT
# reddit
#python clean_data_for_generation.py $OUT_DIR --data_file $DATA_FILE --data_name $DATA_NAME --model_type $MODEL_TYPE --comment_data $COMMENT_DATA --sample_pct $SAMPLE_PCT
# reddit + author
(python clean_data_for_generation.py $OUT_DIR --data_file $DATA_FILE --data_name $DATA_NAME --model_type $MODEL_TYPE --comment_data $COMMENT_DATA --author_data $AUTHOR_DATA --sample_pct $SAMPLE_PCT)&
PID=$!
MAX_MEMORY=80000000000 # 80G
prlimit --pid $PID --as=$MAX_MEMORY
