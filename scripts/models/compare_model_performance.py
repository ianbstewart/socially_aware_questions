"""
Compare performance between different models.
"""
import gzip
import os
from argparse import ArgumentParser
from itertools import product, combinations

import numpy as np
np.random.seed(123)
import pandas as pd
import torch
torch.manual_seed(123)
from scipy.stats import wilcoxon
from statsmodels.stats.descriptivestats import sign_test
from test_question_generation import test_question_overlap, STOP_WORDS, load_model, compute_perplexity


def main():
    parser = ArgumentParser()
    parser.add_argument('test_data_file')
    parser.add_argument('--model_output_files', nargs='+', default=[])
    parser.add_argument('--model_names', nargs='+', default=[])
    parser.add_argument('--word_embed_file', default='../../data/embeddings/wiki-news-300d-1M.vec.gz')
    parser.add_argument('--out_dir', default='../../data/reddit_data/')
    args = vars(parser.parse_args())
    test_data_file = args['test_data_file']
    model_output_files = args['model_output_files']
    model_names = args['model_names']
    word_embed_file = args['word_embed_file']
    out_dir = args['out_dir']

    ## load all data
    test_data = torch.load(test_data_file)
    test_text_data = test_data['target_text']
    model_output_data = list(map(lambda x: list(map(lambda y: y.strip(), gzip.open(x, 'rt'))), model_output_files))
    model_output_data = pd.DataFrame(model_output_data, index=model_names).transpose()
    model_output_data = model_output_data.assign(**{'target_text' : test_text_data})
    # tmp debugging
    # model_output_data = model_output_data.loc[np.random.choice(model_output_data.index, 1000, replace=False), :]

    ## get generation scores...again
    ## overlap scores => BLEU, ROUGE, WMD, sentence distance
    generation_score_data = []
    for model_name_i in model_names:
        generation_score_data_i = test_question_overlap(model_output_data.loc[:, model_name_i].values,
                                                        test_data,
                                                        word_embed_file=word_embed_file, stop_words=STOP_WORDS)
        generation_score_data_i = generation_score_data_i.assign(**{'model_name' : model_name_i})
        generation_score_data.append(generation_score_data_i)
    generation_score_data = pd.concat(generation_score_data, axis=0)
    # tmp debugging
    # print(f'generation score data sample:\n{generation_score_data.head()}')
    ## other scores => diversity, redundancy, perplexity (test via bootstrap)
    redundancy_data = []
    perplexity_data = []
    train_data_file = test_data_file.replace('test.pt', 'train.pt')
    train_data = torch.load(train_data_file)
    train_data_text = train_data['target_text']
    model_cache_dir = '../../data/model_cache/'
    model_type_lookup = {
        'text' : 'bart',
        'reader_token' : 'bart',
        'reader_attention' : 'bart_author_attention',
        'reader_subreddit_embed' : 'bart_author_embeds',
        'reader_text_embed': 'bart_author_embeds',
    }
    test_data_dir = os.path.dirname(test_data_file)
    perplexity_sample_size = 5000
    ## pre-sample test data for perplexity => same test data across models
    test_data_sample = test_data.select(np.random.choice(list(range(len(test_data))), perplexity_sample_size, replace=False),
                                        keep_in_memory=True, load_from_cache_file=False)
    for model_name_i, model_output_file_i in zip(model_names, model_output_files):
        # redundancy
        redundancy_i = model_output_data.loc[:, model_name_i].apply(lambda x: int(x in train_data_text))
        redundancy_i = pd.DataFrame(redundancy_i, index=['redundancy']).transpose().assign(**{'model_name' : model_name_i})
        redundancy_data.append(redundancy_i)
        # perplexity
        # reload original model
        model_output_file_dir_i = os.path.join(os.path.dirname(model_output_file_i), 'question_generation_model')
        # print(f'model output file dir {model_output_file_dir_i} has files {os.listdir(model_output_file_dir_i)}')
        model_output_file_dir_files_i = list(map(lambda x: os.path.join(model_output_file_dir_i, x), os.listdir(model_output_file_dir_i)))
        model_checkpoint_dirs_i = list(filter(lambda x: os.path.basename(x).startswith('checkpoint-') and os.path.isdir(x), model_output_file_dir_files_i))
        # print(f'model checkpoint dirs = {model_checkpoint_dirs_i}')
        most_recent_checkpoint_dir_i = max(model_checkpoint_dirs_i, key=lambda x: int(os.path.basename(x).replace('checkpoint-', '')))
        model_weight_file_i = os.path.join(most_recent_checkpoint_dir_i, 'pytorch_model.bin')
        model_type_i = model_type_lookup[model_name_i]
        model_i, tokenizer_i = load_model(model_cache_dir, model_weight_file_i, model_type_i, test_data_dir)
        log_likelihoods_i, _ = compute_perplexity(model_i, model_type_i, perplexity_sample_size, test_data_sample, return_log_likelihoods=True)
        perplexity_i = pd.DataFrame(log_likelihoods_i, columns=['perplexity']).assign(**{'model_name' : model_name_i})
        perplexity_data.append(perplexity_i)
    redundancy_data = pd.concat(redundancy_data, axis=0)
    perplexity_data = pd.concat(perplexity_data, axis=0)
    # tmp debugging
    # print(f'perplexity data sample {perplexity_data.head(10)}')

    ## test significance
    model_combos = list(combinations(model_names, 2))
    print(f'testing model combos {model_combos}')
    bootstrap_iters = 1000
    bootstrap_sample_size = 5000
    generation_score_vars =  ['BLEU-1', 'ROUGE-L', 'sentence_dist', 'WMD']
    model_score_data = []
    for model_1, model_2 in model_combos:
        generation_score_data_1 = generation_score_data[generation_score_data.loc[:, 'model_name']==model_1]
        generation_score_data_2 = generation_score_data[generation_score_data.loc[:, 'model_name']==model_2]
        # tmp debugging
        # print(f'score data 1 sample = {generation_score_data_1.loc[:, "BLEU-1"].head(50)}')
        # print(f'score data 2 sample = {generation_score_data_2.loc[:, "BLEU-1"].head(50)}')
        for generation_score_var_i in generation_score_vars:
            mean_diff_i = np.mean(generation_score_data_1.loc[:, generation_score_var_i] - generation_score_data_2.loc[:, generation_score_var_i])
            test_stat, p_val = wilcoxon(generation_score_data_1.loc[:, generation_score_var_i], generation_score_data_2.loc[:, generation_score_var_i])
            model_score_data.append([model_1, model_2, generation_score_var_i, mean_diff_i, test_stat, p_val])
        ## test perplexity, redundancy, diversity
        # perplexity
        perplexity_data_1 = perplexity_data[perplexity_data.loc[:, 'model_name']==model_1]
        perplexity_data_2 = perplexity_data[perplexity_data.loc[:, 'model_name']==model_2]
        perplexity_diff = np.median(perplexity_data_1.loc[:, 'perplexity'] - perplexity_data_2.loc[:, 'perplexity'])
        test_stat, p_val = wilcoxon(perplexity_data_1.loc[:, 'perplexity'], perplexity_data_2.loc[:, 'perplexity'])
        model_score_data.append([model_1, model_2, 'perplexity', perplexity_diff, test_stat, p_val])
        # redundancy => bootstrap
        redundancy_data_1 = redundancy_data[redundancy_data.loc[:, 'model_name']==model_1]
        redundancy_data_2 = redundancy_data[redundancy_data.loc[:, 'model_name']==model_2]
        redundancy_diffs = []
        for _ in range(bootstrap_iters):
            bootstrap_idx_i = np.random.choice(list(range(redundancy_data_1.shape[0])), bootstrap_sample_size, replace=(bootstrap_sample_size > redundancy_data_1.shape[0]))
            redundancy_data_1_i = redundancy_data_1.iloc[bootstrap_idx_i, :]
            redundancy_data_2_i = redundancy_data_2.iloc[bootstrap_idx_i, :]
            redundancy_diff_i = redundancy_data_1_i.loc[:, 'redundancy'].mean() - redundancy_data_2_i.loc[:, 'redundancy'].mean()
            redundancy_diffs.append(redundancy_diff_i)
        redundancy_diff = np.mean(redundancy_diffs)
        test_stat, p_val = sign_test(redundancy_diff, mu0=0.)
        model_score_data.append([model_1, model_2, 'redundancy', redundancy_diff, test_stat, p_val])
        # diversity => bootstrap
        model_text_1 = model_output_data.loc[:, model_1]
        model_text_2 = model_output_data.loc[:, model_2]
        diversity_diffs = []
        for _ in range(bootstrap_iters):
            bootstrap_idx_i = np.random.choice(list(range(model_output_data.shape[0])), bootstrap_sample_size, replace=(bootstrap_sample_size > model_output_data.shape[0]))
            diversity_1_i = model_text_1.iloc[bootstrap_idx_i].nunique() / model_text_1.shape[0]
            diversity_2_i = model_text_2.iloc[bootstrap_idx_i].nunique() / model_text_2.shape[0]
            diversity_diff_i = diversity_1_i - diversity_2_i
            diversity_diffs.append(diversity_diff_i)
        diversity_diff = np.mean(diversity_diffs)
        test_stat, p_val = sign_test(diversity_diff, mu0=0.)
        model_score_data.append([model_1, model_2, 'diversity', diversity_diff, test_stat, p_val])
    model_score_data = pd.DataFrame(model_score_data, columns=['model_1', 'model_2', 'score', 'mean_diff', 'test_stat', 'p'])

    ## write to file
    model_score_data_file = os.path.join(out_dir, f'model_output_compare_scores.tsv')
    model_score_data.to_csv(model_score_data_file, sep='\t', index=False)

if __name__ == '__main__':
    main()