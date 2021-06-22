#!/bin/bash
#SBATCH --job-name=test_author_group_prediction
#SBATCH --mail-type=BEGIN,END
#SBATCH --output=/home/%u/logs/%x-%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-gpu=50g
#SBATCH --time=47:00:00
#SBATCH --partition=gpu
#SBATCH --gpus=1

# specify CUDA device (only for LIT machines)
export CUDA_VISIBLE_DEVICES=3
#GROUP_CATEGORIES=("location_region" "expert_pct_bin" "relative_time_bin")
GROUP_CATEGORIES=("relative_time_bin")
python test_author_group_prediction.py --group_categories "${GROUP_CATEGORIES[@]}"
#python test_author_group_prediction.py --group_categories "${GROUP_CATEGORIES[@]}" --retrain
# dumb parallel code that doesn't work fml
#export LOCAL_RANK=1
#python -m torch.distributed.launch --nproc_per_node 2 --use_env test_author_group_prediction.py "${GROUP_CATEGORIES[@]}"