1) Dataset Creation Process:

Starting with SEART’s github repository search, we found github repositories with java as a primary language to pull methods from. We specified repos with a minimum of 1000 non-blank lines, at least 100 stars, 10 collaborators, and at least one commit since 2023 to ensure some basic repo quality standards. We then limited the max code lines to 10000 to ensure that there weren’t any massive repos that overshadowed and diluted the method pool.

The search returned ~1300 repos, which we pared down to 18 repos of medium to small size, processed them with pydriller, and ended with a single method csv file containing ~300000 processed methods for use in the model. 

2) Ngram Model Creation

The ngram model is creating by looping over the tokens in the corpus. The grams are stored in a dictionary, with the n-1 tokens acting as the key. The preceding possible token is then appended. For example a trigram with the first two tokens as 'OperationStatus' and '(';  

('OperationStatus', '('): ['true',
  'true',
  'false',
  'false',
  'true',
  'true',
  'true',
  'true',
  'true'],

The most probable word given n-1 tokens is found by using the n-1 tokens as a key to the dictionary, picking the word that appears the most. If the key isn't found it returns NA with a zero probablity. Chaining the most probable words is how code prediction is done. Here is an example using a trigram model as the same tokens as before; limiting the length to 5 more tokens, displaying its associated probability.

('true', 0.7777777777777778)
(')', 0.6111111111111112)
(';', 0.8095238095238095)
('\n', 0.998810232004759)
('}', 0.5163164953062137)
['OperationStatus', '(', 'true', ')', ';', '\n', '}']

3) Model Training Methodology
4) Evaluation Results with relevant links
