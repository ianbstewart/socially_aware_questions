SUBMISSION_DATA=../../data/reddit_data/subreddit_submissions_2018-01_2019-12.gz
OUT_DIR=../../data/reddit_data/
DATA_DIR=/local2/lbiester/pushshift/comments/
## serial
#COMMENT_DATES="2019,1,2019,12"
#python collect_all_child_comments_from_submissions.py $SUBMISSION_DATA --out_dir $OUT_DIR --data_dir $DATA_DIR --comment_dates $COMMENT_DATES
## parallel
COMMENT_YEAR=2019
COMMENT_START_MONTH=12
COMMENT_END_MONTH=12
## generate all combos lol
COMMENT_YEAR_MONTH_PAIRS=()
for COMMENT_MONTH in `seq $COMMENT_START_MONTH $COMMENT_END_MONTH`;
do
  COMMENT_YEAR_MONTH_PAIRS+=($COMMENT_YEAR,"$COMMENT_MONTH",$COMMENT_YEAR,"$COMMENT_MONTH")
done
NUM_JOBS=4
parallel --jobs $NUM_JOBS python collect_all_child_comments_from_submissions.py $SUBMISSION_DATA --out_dir $OUT_DIR --data_dir $DATA_DIR --comment_dates {} ::: "${COMMENT_YEAR_MONTH_PAIRS[@]}"