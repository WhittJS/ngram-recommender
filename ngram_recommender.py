import pandas as pd
import re
from pygments.lexers.jvm import JavaLexer
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from sklearn.model_selection import train_test_split
from collections import Counter
import math
from tqdm import tqdm
import random
import pickle
import os
import time


# Type 1 Clones #
def remove_duplicates(data):
    """Remove duplicate methods based on method content.
      Almost Type-1 with the exception of comments
    """
    return data.drop_duplicates(subset="Method Code", keep="first")


def filter_ascii_methods(data):
    """Filter methods to include only those with ASCII characters."""
    data = data[data["Method Code"].apply(lambda x: all(ord(char) < 128 for char in x))]
    return data

# Three Approaches:
# 	1.	Data Distribution-Based Filtering: We eliminate outliers by analyzing the original data distribution, as demonstrated below.
# 	2.	Literature-Driven Filtering: We follow best practices outlined in research, such as removing methods exceeding 512 tokens in length.
# 	3.	Hybrid Approach: We combine elements from both the distribution-based and literature-driven methods.


def remove_outliers(data, lower_percentile=5, upper_percentile=95):
    """Remove outliers based on method length."""
    method_lengths = data["Method Code"].apply(len)
    lower_bound = method_lengths.quantile(lower_percentile / 100)
    upper_bound = method_lengths.quantile(upper_percentile / 100)
    return data[(method_lengths >= lower_bound) & (method_lengths <= upper_bound)]


def remove_boilerplate_methods(data):
    """Remove boilerplate methods like setters and getters."""
    boilerplate_patterns = [
        r"\bset[A-Z][a-zA-Z0-9_]*\(.*\)\s*{",  # Setter methods
        r"\bget[A-Z][a-zA-Z0-9_]*\(.*\)\s*{",  # Getter methods
    ]
    boilerplate_regex = re.compile("|".join(boilerplate_patterns))
    data = data[~data["Method Code"].apply(lambda x: bool(boilerplate_regex.search(x)))]
    return data


def remove_comments_from_dataframe(df: pd.DataFrame, method_column: str, language: str) -> pd.DataFrame:
    """
    Removes comments from Java methods in a DataFrame and adds a new column with cleaned methods.

    Args:
        df (pd.DataFrame): DataFrame containing the methods.
        method_column (str): Column name containing the raw Java methods.
        language (str): Programming language for the lexer (e.g., 'java').

    Returns:
        pd.DataFrame: Updated DataFrame with a new column 'Java Method No Comments'.
    """
    # Define a function to remove comments from a single method
    def remove_comments(code):
        lexer = get_lexer_by_name(language)
        tokens = lexer.get_tokens(code)
        # Filter out comments using a lambda function
        clean_code = ''.join(token[1] for token in tokens if not (lambda t: t[0] in Token.Comment)(token))

        return clean_code

    # Apply the function to the specified column and add a new column with the results
    df["Method Code No Comments"] = df[method_column].apply(remove_comments)
    return df


def the_xgrams4(n_choice, training_corpus) -> dict:
    the_xgrammys4 = {}
    for sentence in training_corpus:
        words = [word for word in sentence]
        for ix in range(n_choice-1, len(words)):
            try:
                temp_list = []

                for i in range(n_choice-1):
                    temp_list.append(words[ix-n_choice+i+1])
                    # for i in range(n_choice-1):
                    #     temp_list.append(words[ix-i-1])
                    # temp_list.reverse()
                list_key = tuple(temp_list)

                the_xgrammys4[list_key].append(words[ix])
            except KeyError:
                temp_list = []

                for i in range(n_choice-1):
                    temp_list.append(words[ix-n_choice+i+1])
                # for i in range(n_choice-1):
                #     temp_list.append(words[ix-i-1])
                # temp_list.reverse()
                list_key = tuple(temp_list)

                the_xgrammys4[list_key] = []
                the_xgrammys4[list_key].append(words[ix])
    return the_xgrammys4


def find_most_prob_word(token_list, model: dict):
    list_key = tuple(token_list)
    try:
        possible_words = model[list_key]
        # print(possible_words)
        c = Counter(possible_words)
        sum = c.total()
        most_common_word = c.most_common(1)
        word = most_common_word[0][0]
        common_count = most_common_word[0][1]
        # returns most probable word and probability
        return (word, f"{common_count/sum:.1f}")
    except KeyError:
        # print("not found")
        return ("NA", 0)


def find_word_prob(token_list, word, model: dict):
    list_key = tuple(token_list)
    try:
        possible_words = model[list_key]
        # print(possible_words)
        c = Counter(possible_words)
        sum = c.total()
        word_count = c[word]
        return word_count/sum
    except KeyError:
        return 0

def too_many_closing_brackets(the_tokens):
  stack = []
  for t in the_tokens:
    if(t=="(" or t=="{" or t=="["):
      stack.append(t)
    elif(t==")" or t=="}" or t=="]"):
      if ((not stack) or ((t == ')' and stack[-1] != '(')) or ((t == '}' and stack[-1] != '{')) or ((t == ']' and stack[-1] != '['))):
        #a miss match or too many closing
        return True

      stack.pop()
  #could be more opening brackets left on stack
  #but this method just checks if there
  #are too many closing so the continue method can continue on
  return False

def repeated_x_times(the_tokens,x):
  repeating = False
  if(len(the_tokens)>=x):
    for i in range(x-1):
      if(the_tokens[-i-2]==the_tokens[-i-1]):
          repeating = True
          if(i==x-2):
            return True
      else:
          repeating = False
  else:
    return False

def check_alternating_pairs(the_tokens):
  if(len(the_tokens)>=4):
    if(the_tokens[-1]==the_tokens[-3] and the_tokens[-2]==the_tokens[-4]):
      return True
    else:
      return False
  else:
    return False

def continue_method(the_tokens, n, max_length, model):
    predicted_tokens = []
    max_repetitions = 5
    n = n-1
    for _ in range(max_length):
        next_token = find_most_prob_word(the_tokens[-n:], model)
        # print(next_token)
        if next_token[0] == "NA":
            break
        if(check_alternating_pairs(the_tokens)):
          break
        the_tokens.append(next_token[0])
        if(repeated_x_times(the_tokens,max_repetitions)):
          predicted_tokens.append((next_token[0], next_token[1]))
          break
        if(too_many_closing_brackets(the_tokens)):
          break
        predicted_tokens.append((next_token[0], next_token[1]))
    return(predicted_tokens)


def perplexity(methods, n_choice, model: dict):
    total_log_prob = 0
    total_tokens = 0

    for method in tqdm(methods):
        for ix in range(n_choice-1, len(method)):
            context = method[ix-(n_choice-1):ix]
            token = method[ix]

            probability = find_word_prob(context, token, model)
            # print(f"given {context} and {word}, the probability is {probability}")
            if probability > 0:
                total_log_prob += math.log2(probability)
            else:
                total_log_prob += math.log2(1e-10)  # prevent log(0) blowing up
            total_tokens += 1
    avg_log_prob = total_log_prob / total_tokens
    return 2 ** (-avg_log_prob)


def preprocess(df):
    print("Initial dataset size:", len(df))
    df = remove_duplicates(df)
    print("After removing duplicates:", len(df))

    df = filter_ascii_methods(df)
    print("After filtering ASCII methods:", len(df))

    df = remove_outliers(df)
    print("After removing outliers:", len(df))

    df = remove_boilerplate_methods(df)
    print("After removing boilerplate methods:", len(df))

    df = remove_comments_from_dataframe(df, "Method Code", "Java")
    print("After cleaning comments:", len(df))

    # print(df["Method Code"])
    methods = df["Method Code No Comments"]
    return methods


def output_json(test_sentences, n_choice_model, best_performer_n, filename):
    print("Generating json output...")
    random.seed(42)
    json_test_samples = random.sample(test_sentences, 100)
    predicted_methods = []
    for method in tqdm(json_test_samples):
        predicted_methods.append(continue_method(method[0:best_performer_n], best_performer_n, len(method), n_choice_model)[best_performer_n:])
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('{\n')
        for i, value in enumerate(predicted_methods):
            comma = ',' if i < len(predicted_methods) - 1 else ''
            file.write(f'    "{i}": {value}{comma}\n')
        file.write('}\n')


def train_test_model(train_sentences, test_sentences, val_sentences):
    n_choice_model_dict = {}
    n_choice_perplexity_dict = {}

    # edit these values
    min_ngram = 2
    max_ngram = 10

    for n_choice in range(min_ngram, max_ngram+1):
        print(f"Training {n_choice}-gram model...")
        n_choice_model_dict[n_choice] = the_xgrams4(n_choice, train_sentences)
        print(f"Evaluating {n_choice}-gram model...")
        n_choice_perplexity_dict[n_choice] = perplexity(test_sentences, n_choice, n_choice_model_dict[n_choice])
        print(f"For {n_choice}-gram model, the perplexity is {n_choice_perplexity_dict[n_choice]}")
    best_performer = min(n_choice_perplexity_dict, key=n_choice_perplexity_dict.get)
    print(f"The best performing model is the {best_performer}-gram model with a {min(n_choice_perplexity_dict.values())} perplexity")
    print("Validating best-perfoming model...")
    print(f"For best-performing model ({best_performer}-gram), the perplexity was validated at {perplexity(val_sentences, best_performer, n_choice_model_dict[best_performer])}")
    return n_choice_model_dict[best_performer], best_performer

if __name__ == "__main__":

    print("Reading datasets...")

    with open('training.txt', 'r') as file:
        list = []
        for i in file.readlines():
            list.append(i)
        prof_df = pd.DataFrame(list)
        prof_df.columns = ['Method Code']
    
    our_df = pd.concat([pd.read_csv("output_1.csv"),pd.read_csv("output_2.csv")],ignore_index=True)

    print("Datasets read. Preprocessing...")

    methods = preprocess(our_df)

    print("Tokenizing...")

    sentences = []
    for method in tqdm(methods):
        lexer = JavaLexer()

        tokens = ['<s>'] + [t[1] for t in lexer.get_tokens(method) if ' ' not in t[1]] + ['</s>']
        # print(tokens)
        # print(len(tokens))
        sentences.append(tokens)
    # print(sentences)

    train_sentences, test_sentences = train_test_split(sentences, test_size=0.1, random_state=42)
    train_sentences, val_sentences = train_test_split(train_sentences, test_size=0.1111, random_state=42)
    print(f"number of training methods: {len(train_sentences)}")
    print(f"number of validation methods: {len(val_sentences)}")
    print(f"number of test methods: {len(test_sentences)}")

    if os.path.isfile("student_model.pkl"):
        print("Student model found! If you want to train a new model, delete student_model.pkl and re-run.")
        time.sleep(3)
        with open("student_model.pkl", "rb") as file:
            best_performer_model = pickle.load(file)
        best_performer_n = len(next(iter(best_performer_model.keys())))+1
    else:
        print("Model not found. Training new model on our dataset...")
        best_performer_model, best_performer_n = train_test_model(train_sentences, test_sentences, val_sentences)
        with open("student_model.pkl", "wb") as file:
            pickle.dump(best_performer_model, file)

    output_json(test_sentences, best_performer_model, best_performer_n, 'results_student_model.json')

    if os.path.isfile("teacher_model.pkl"):
        print("Teacher model found! If you want to train a new model, delete teacher_model.pkl and re-run.")
        time.sleep(3)
        with open("teacher_model.pkl", "rb") as file:
            best_performer_model = pickle.load(file)
        best_performer_n = len(next(iter(best_performer_model.keys())))+1
    else:
        prof_train_sentences = []
        for method in prof_df["Method Code"]:
            prof_train_sentences.append(['<s>'] + method.split() + ['</s>'])
        print("Model not found. Training model on teacher dataset...")
        best_performer_model, best_performer_n = train_test_model(prof_train_sentences, test_sentences, val_sentences)
        with open("teacher_model.pkl", "wb") as file:
            pickle.dump(best_performer_model, file)

    output_json(test_sentences, best_performer_model, best_performer_n, 'results_teacher_model.json')
