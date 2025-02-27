import pandas as pd
import re
from pygments.lexers.jvm import JavaLexer
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from sklearn.model_selection import train_test_split
from collections import Counter
import math
from tqdm import tqdm


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


def the_xgrams4(n_choice) -> dict:
    the_xgrammys4 = {}
    for sentence in train_sentences:
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
        return word, common_count/sum
    except KeyError:
        print("not found")
        return "NA", 0


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


def continue_method(the_tokens, n, max_length):
    n = n-1
    for i in range(max_length):
        next_token = find_most_prob_word(the_tokens[-n:])
        print(next_token)
        the_tokens.append(next_token[0])
    print(the_tokens)


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


if __name__ == "__main__":
    df = pd.concat([pd.read_csv("output_1.csv"),pd.read_csv("output_2.csv")],ignore_index=True)

    methods = preprocess(df)

    sentences = []
    for method in methods:
        lexer = JavaLexer()

        tokens = ['<s>'] + [t[1] for t in lexer.get_tokens(method) if ' ' not in t[1]] + ['</s>']
        # print(tokens)
        # print(len(tokens))
        sentences.append(tokens)
    # print(sentences)

    train_sentences, test_sentences = train_test_split(sentences, test_size=0.2, random_state=42)
    train_sentences, val_sentences = train_test_split(train_sentences, test_size=0.2, random_state=42)
    print(f"number of training methods: {len(train_sentences)}")
    print(f"number of validation methods: {len(val_sentences)}")
    print(f"number of test methods: {len(test_sentences)}")

    n_choice_model = {}
    n_choice_perplexity = {}

    # edit these values
    min_ngram = 4
    max_ngram = 15

    for n_choice in range(min_ngram, max_ngram+1):
        print(f"Training {n_choice}-gram model...")
        model = the_xgrams4(n_choice)
        n_choice_model[n_choice] = model
        print(f"Evaluating {n_choice}-gram model...")
        n_choice_perplexity[n_choice] = perplexity(test_sentences, n_choice, model)
        print(f"For {n_choice}-gram model, the perplexity is {n_choice_perplexity[n_choice]}")
    best_performer = min(n_choice_perplexity, key=n_choice_perplexity.get)
    print(f"The best performing model is the {best_performer}-gram model with a {min(n_choice_perplexity.values())} perplexity")
    print("Validating best-perfoming model...")
    print(f"For best-performing model ({best_performer}-gram), the perplexity was validated at {perplexity(val_sentences, best_performer, n_choice_model[best_performer])}")
