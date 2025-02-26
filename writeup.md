1) Dataset Creation Process:

Starting with SEART’s github repository search, we found github repositories with java as a primary language to pull methods from. We specified repos with a minimum of 1000 non-blank lines, at least 100 stars, 10 collaborators, and at least one commit since 2023 to ensure some basic repo quality standards. We then limited the max code lines to 10000 to ensure that there weren’t any massive repos that overshadowed and diluted the method pool.

The search returned ~700 repos, which we pared down to 7 repos of medium to small size, processed them with pydriller, and ended with a single method csv file containing ~52000 processed methods for use in the model. 

2) Model Training Methodology
3) Evaluation Results with relevant links
