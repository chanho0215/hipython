# Credit Default Model Comparison

- Data: `ml\data\UCI_Credit_Card.csv`
- Train size: 24,000
- Test size: 6,000
- Target positive ratio (default=1): 0.2212
- Best model by ROC-AUC: `gradient_boosting`
- Best model file: `ml\reports\credit_default\best_model_gradient_boosting_20260309_095514.joblib`

## Metrics

| model | test_roc_auc | test_pr_auc | cv_roc_auc_mean | positive_rate_pred@0.5 | accuracy@0.5 | precision@0.5 | recall@0.5 | f1@0.5 | best_f1_threshold | precision@best_f1 | recall@best_f1 | f1@best_f1 | tn@0.5 | fp@0.5 | fn@0.5 | tp@0.5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gradient_boosting | 0.780720 | 0.554228 | 0.781253 | 0.120500 | 0.818667 | 0.665284 | 0.362472 | 0.469268 | 0.239960 | 0.500626 | 0.602864 | 0.547009 | 4431 | 242 | 846 | 481 |
| extra_trees | 0.774410 | 0.547419 | 0.776954 | 0.216000 | 0.795833 | 0.539352 | 0.526752 | 0.532978 | 0.443156 | 0.501976 | 0.574228 | 0.535677 | 4076 | 597 | 628 | 699 |
| random_forest | 0.764936 | 0.545980 | 0.776555 | 0.156833 | 0.808333 | 0.594049 | 0.421251 | 0.492945 | 0.345326 | 0.511565 | 0.566692 | 0.537719 | 4291 | 382 | 768 | 559 |
| logistic_regression | 0.708115 | 0.490444 | 0.726522 | 0.373500 | 0.679667 | 0.367247 | 0.620196 | 0.461323 | 0.567247 | 0.506605 | 0.491334 | 0.498852 | 3255 | 1418 | 504 | 823 |
| dummy_most_frequent | 0.500000 | 0.221167 | 0.500000 | 0.000000 | 0.778833 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.221167 | 1.000000 | 0.362222 | 4673 | 0 | 1327 | 0 |